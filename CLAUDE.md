# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a materials science database and visualization platform built with FastAPI. The backend provides REST APIs for managing materials data from the Materials Project, including crystal structures, properties, and ML-based property predictions.

## Key Architecture

### Database Models
- **Material**: Core material entity with formula, composition, crystal structure metadata
- **Element**: Periodic table elements with atomic properties  
- **Composition**: Junction table for material-element relationships with stoichiometric amounts
- **Property**: Material properties (formation energy, band gap, etc.)
- **Calculation**: DFT calculation metadata and results
- **Structure**: Crystal structure data with lattice parameters and atomic sites

### API Structure
- `/api/v1/materials/*` - CRUD operations for materials
- `/api/v1/search/*` - Search and filtering endpoints
- `/api/v1/predict/*` - ML property prediction endpoints
- `/api/v1/compare/*` - Material comparison utilities
- `/api/v1/phase-diagram/*` - Phase diagram generation

### Core Services
- **MLService** (`app/services/ml_service.py`): Placeholder ML inference service for property predictions
- **RedisCache** (`app/core/cache.py`): Async Redis caching for API responses
- **Database Session** (`app/db/session.py`): Async SQLAlchemy session management

## Development Commands

### Running the Application
```bash
# Start the FastAPI server (from backend/ directory)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
# http://localhost:8000/docs (Swagger)
# http://localhost:8000/redoc (ReDoc)
```

### Data Ingestion
```bash
# Ingest materials from Materials Project API
python -m scripts.ingest_data --chemsys Fe-O --limit 100
python -m scripts.ingest_data --elements Fe,Co,Ni --stable-only --limit 50

# Note: Requires MP_API_KEY environment variable
```

### Database Setup
The application uses PostgreSQL with async SQLAlchemy. Database tables are auto-created on startup via the lifespan handler in `app/main.py`.

## Environment Configuration

### Required Environment Variables
- `MP_API_KEY`: Materials Project API key for data ingestion
- `POSTGRES_*`: Database connection parameters (defaults provided for local dev)
- `REDIS_*`: Redis connection parameters (defaults to localhost)

### Database URLs
- Async: `postgresql+asyncpg://user:pass@host:port/db`
- Sync (migrations): `postgresql://user:pass@host:port/db`

## Code Patterns

### API Route Structure
Routes follow RESTful conventions with async handlers, Pydantic schemas for validation, and dependency injection for database sessions. All routes include proper error handling and caching where applicable.

### Database Operations
All database operations use async SQLAlchemy with proper session management via dependency injection. Complex queries use selectinload for eager loading of relationships.

### Caching Strategy
Redis caching is implemented at the service level with TTL-based expiration. Cache keys follow the pattern `{resource}:{identifier}` (e.g., `material:mp-1234`).