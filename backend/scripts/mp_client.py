"""Materials Project API client for data ingestion"""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

import httpx

from app.core.config import settings


class MaterialsProjectClient:
    """
    client for fetching data from Materials Project API

    uses the new MP API (api.materialsproject.org) with async support
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
    ):
        self.api_key = api_key or settings.MP_API_KEY
        self.base_url = settings.MP_API_BASE_URL
        self.cache_dir = cache_dir or Path("./data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if not self.api_key:
            raise ValueError(
                "Materials Project API key required. "
                "Set MP_API_KEY environment variable or pass api_key parameter."
            )

    def _get_headers(self) -> dict:
        """get API request headers"""
        return {
            "X-API-KEY": self.api_key,
            "Accept": "application/json",
        }

    def _cache_path(self, endpoint: str, params: dict) -> Path:
        """generate cache file path for a request"""
        import hashlib
        param_str = json.dumps(params, sort_keys=True)
        cache_key = hashlib.md5(f"{endpoint}:{param_str}".encode()).hexdigest()
        return self.cache_dir / f"{cache_key}.json"

    async def _fetch_with_cache(
        self,
        endpoint: str,
        params: dict,
        use_cache: bool = True,
        cache_ttl_hours: int = 24,
    ) -> Any:
        """getch data with optional caching"""
        cache_path = self._cache_path(endpoint, params)

        # Check cache
        if use_cache and cache_path.exists():
            cache_age = datetime.now().timestamp() - cache_path.stat().st_mtime
            if cache_age < cache_ttl_hours * 3600:
                with open(cache_path) as f:
                    return json.load(f)

        # Fetch from API
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

        # Cache result
        with open(cache_path, "w") as f:
            json.dump(data, f)

        return data

    async def get_material(self, material_id: str) -> dict:
        """
        getch a single material by ID

        args:
            material_id: Material ID (e.g., "mp-1234")

        returns:
            Material data dictionary
        """
        endpoint = f"/materials/summary/{material_id}"
        data = await self._fetch_with_cache(endpoint, {})
        return data.get("data", [{}])[0] if data.get("data") else {}

    async def search_materials(
        self,
        chemsys: Optional[str] = None,
        elements: Optional[list[str]] = None,
        formula: Optional[str] = None,
        crystal_system: Optional[str] = None,
        spacegroup_number: Optional[int] = None,
        band_gap_min: Optional[float] = None,
        band_gap_max: Optional[float] = None,
        is_stable: Optional[bool] = None,
        fields: Optional[list[str]] = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        search for materials with filters

        returns:
            List of material data dictionaries
        """
        params = {"_limit": limit}

        if chemsys:
            params["chemsys"] = chemsys
        if elements:
            params["elements"] = ",".join(elements)
        if formula:
            params["formula"] = formula
        if crystal_system:
            params["crystal_system"] = crystal_system
        if spacegroup_number:
            params["spacegroup_number"] = spacegroup_number
        if band_gap_min is not None:
            params["band_gap_min"] = band_gap_min
        if band_gap_max is not None:
            params["band_gap_max"] = band_gap_max
        if is_stable is not None:
            params["is_stable"] = str(is_stable).lower()
        if fields:
            params["_fields"] = ",".join(fields)

        endpoint = "/materials/summary/"
        data = await self._fetch_with_cache(endpoint, params, cache_ttl_hours=1)
        return data.get("data", [])

    async def get_structure(self, material_id: str) -> dict:
        """
        fetch crystal structure for a material

        returns structure in pymatgen-compatible format
        """
        endpoint = f"/materials/core/{material_id}"
        params = {"_fields": "structure"}
        data = await self._fetch_with_cache(endpoint, params)
        if data.get("data"):
            return data["data"][0].get("structure", {})
        return {}

    async def get_electronic_structure(self, material_id: str) -> dict:
        """Fetch electronic structure data (band structure, DOS)."""
        endpoint = f"/materials/electronic_structure/{material_id}"
        data = await self._fetch_with_cache(endpoint, {})
        return data.get("data", [{}])[0] if data.get("data") else {}

    async def get_thermo(self, material_id: str) -> dict:
        """Fetch thermodynamic data."""
        endpoint = f"/materials/thermo/{material_id}"
        data = await self._fetch_with_cache(endpoint, {})
        return data.get("data", [{}])[0] if data.get("data") else {}

    async def bulk_fetch_materials(
        self,
        material_ids: list[str],
        include_structure: bool = True,
        batch_size: int = 50,
    ) -> list[dict]:
        """
        fetch multiple materials in batches

        args:
            material_ids: List of material IDs
            include_structure: Whether to include structure data
            batch_size: Number of materials per API request

        returns:
            List of material data dictionaries
        """
        all_materials = []

        for i in range(0, len(material_ids), batch_size):
            batch_ids = material_ids[i:i + batch_size]

            # Fetch batch
            tasks = [self.get_material(mid) for mid in batch_ids]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for mid, result in zip(batch_ids, batch_results):
                if isinstance(result, Exception):
                    print(f"Error fetching {mid}: {result}")
                    continue

                if include_structure:
                    try:
                        structure = await self.get_structure(mid)
                        result["structure"] = structure
                    except Exception as e:
                        print(f"Error fetching structure for {mid}: {e}")

                all_materials.append(result)

            # Rate limiting
            await asyncio.sleep(0.5)

        return all_materials


async def main():
    """example usage of the Materials Project client"""
    client = MaterialsProjectClient()

    # Search for iron oxides
    print("Searching for Fe-O materials...")
    materials = await client.search_materials(
        chemsys="Fe-O",
        is_stable=True,
        limit=10,
    )

    print(f"Found {len(materials)} materials")
    for mat in materials[:5]:
        print(f"  {mat.get('material_id')}: {mat.get('formula_pretty')}")


if __name__ == "__main__":
    asyncio.run(main())
