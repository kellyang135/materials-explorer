#!/usr/bin/env python3
"""
Comprehensive test script to verify the materials-explorer system
Tests: Database contents, Backend API responses, Frontend endpoints
"""

import asyncio
import json
import sqlite3
import requests
import sys
from pathlib import Path
from typing import Dict, List, Any

# Test configuration
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1"
DATABASE_PATH = Path(__file__).parent / "backend" / "materials_explorer.db"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_section(title: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}")
    print(f" {title}")
    print(f"{'='*60}{Colors.END}")

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"  {msg}")

def test_database():
    """Test database file existence and contents"""
    print_section("Testing Database")
    
    # Check if database file exists
    if not DATABASE_PATH.exists():
        print_error(f"Database file not found at {DATABASE_PATH}")
        return False
    
    print_success(f"Database file found at {DATABASE_PATH}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        expected_tables = ['materials', 'elements', 'compositions', 'structures', 'properties', 'calculations']
        
        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            print_warning(f"Missing tables: {missing_tables}")
        else:
            print_success("All expected tables found")
        
        print_info(f"Available tables: {tables}")
        
        # Check materials count
        cursor.execute("SELECT COUNT(*) FROM materials")
        material_count = cursor.fetchone()[0]
        print_info(f"Materials in database: {material_count}")
        
        if material_count == 0:
            print_error("No materials found in database")
            return False
        
        # Show sample materials
        cursor.execute("SELECT material_id, formula, spacegroup_number FROM materials LIMIT 5")
        materials = cursor.fetchall()
        print_info("Sample materials:")
        for mat in materials:
            print_info(f"  - {mat[0]}: {mat[1]} (spacegroup: {mat[2]})")
        
        # Check compositions
        cursor.execute("SELECT COUNT(*) FROM compositions")
        comp_count = cursor.fetchone()[0]
        print_info(f"Composition entries: {comp_count}")
        
        # Check structures 
        cursor.execute("SELECT COUNT(*) FROM structures")
        struct_count = cursor.fetchone()[0]
        print_info(f"Structure entries: {struct_count}")
        
        conn.close()
        print_success("Database validation completed")
        return True
        
    except Exception as e:
        print_error(f"Database error: {e}")
        return False

def test_backend_health():
    """Test backend health endpoint"""
    print_section("Testing Backend Health")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend health check passed: {data}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend. Is it running on localhost:8000?")
        return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_materials_list():
    """Test materials list endpoint"""
    print_section("Testing Materials List API")
    
    try:
        response = requests.get(f"{API_BASE}/materials", timeout=10)
        print_info(f"GET /api/v1/materials -> {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Materials list retrieved successfully")
            print_info(f"Total materials: {data.get('total', 'unknown')}")
            print_info(f"Current page: {data.get('page', 'unknown')}")
            print_info(f"Items in response: {len(data.get('items', []))}")
            
            # Show sample materials
            items = data.get('items', [])
            if items:
                print_info("Sample materials from API:")
                for item in items[:3]:
                    print_info(f"  - {item.get('material_id')}: {item.get('formula')} (density: {item.get('density', 'N/A')})")
                return True
            else:
                print_error("API returned empty items list")
                return False
        else:
            print_error(f"Materials list failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Materials list error: {e}")
        return False

def test_specific_material():
    """Test getting a specific material"""
    print_section("Testing Specific Material API")
    
    # First get a material ID from the list
    try:
        response = requests.get(f"{API_BASE}/materials?page=1&page_size=1", timeout=10)
        if response.status_code != 200:
            print_error("Could not get material list for testing specific material")
            return False
            
        data = response.json()
        items = data.get('items', [])
        if not items:
            print_error("No materials available for testing")
            return False
        
        material_id = items[0]['material_id']
        print_info(f"Testing with material ID: {material_id}")
        
        # Test specific material endpoint
        response = requests.get(f"{API_BASE}/materials/{material_id}", timeout=10)
        print_info(f"GET /api/v1/materials/{material_id} -> {response.status_code}")
        
        if response.status_code == 200:
            material = response.json()
            print_success(f"Material {material_id} retrieved successfully")
            print_info(f"Formula: {material.get('formula')}")
            print_info(f"Crystal system: {material.get('crystal_system')}")
            print_info(f"Spacegroup: {material.get('spacegroup_number')} ({material.get('spacegroup_symbol')})")
            print_info(f"Density: {material.get('density')} g/cm³")
            
            # Test structure endpoint
            struct_response = requests.get(f"{API_BASE}/materials/{material_id}/structure", timeout=10)
            print_info(f"GET /api/v1/materials/{material_id}/structure -> {struct_response.status_code}")
            
            if struct_response.status_code == 200:
                structure = struct_response.json()
                print_success("Structure data retrieved successfully")
                print_info(f"Sites: {structure.get('num_sites')}")
                print_info(f"Ordered: {structure.get('is_ordered')}")
                return True
            else:
                print_warning(f"Structure endpoint failed: {struct_response.status_code}")
                return True  # Material endpoint worked
                
        elif response.status_code == 404:
            print_error(f"Material {material_id} not found (404)")
            return False
        else:
            print_error(f"Material request failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Specific material test error: {e}")
        return False

def test_search_api():
    """Test search endpoint"""
    print_section("Testing Search API")
    
    try:
        # Test basic search
        response = requests.get(f"{API_BASE}/search?query=Si", timeout=10)
        print_info(f"GET /api/v1/search?query=Si -> {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Search API working")
            print_info(f"Search results: {len(data.get('items', []))} materials")
            return True
        else:
            print_warning(f"Search API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Search API error: {e}")
        return False

def test_ml_predictions():
    """Test ML prediction endpoint"""
    print_section("Testing ML Prediction API")
    
    try:
        # Test prediction models endpoint
        response = requests.get(f"{API_BASE}/predict/models", timeout=10)
        print_info(f"GET /api/v1/predict/models -> {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print_success("Prediction models endpoint working")
            print_info(f"Available models: {list(models.keys()) if isinstance(models, dict) else models}")
            return True
        else:
            print_warning(f"Prediction models failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"ML prediction test error: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print(f"{Colors.BOLD}Materials Explorer System Test{Colors.END}")
    print(f"Testing backend at: {BACKEND_URL}")
    print(f"Testing database at: {DATABASE_PATH}")
    
    test_results = {
        "Database": test_database(),
        "Backend Health": test_backend_health(),
        "Materials List API": test_materials_list(),
        "Specific Material API": test_specific_material(),
        "Search API": test_search_api(),
        "ML Prediction API": test_ml_predictions(),
    }
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status:4} {test_name}{Colors.END}")
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print_success("All tests passed! System is working correctly.")
        return True
    else:
        print_error("Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)