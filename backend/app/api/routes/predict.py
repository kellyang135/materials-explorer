"""ML prediction API routes"""

from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.schemas.search import PredictRequest, PredictResponse, PropertyPrediction
from app.services.ml_service import MLService

router = APIRouter()

# Initialize ML service (lazy loading)
ml_service = MLService()


@router.post("", response_model=PredictResponse)
async def predict_properties(
    request: PredictRequest,
    background_tasks: BackgroundTasks,
):
    """
    predict material properties using ML models

    accepts
    - structure_json: Structure in pymatgen JSON format
    - cif_string: Structure in CIF format

    available properties to predict
    - formation_energy: Formation energy per atom (eV/atom)
    - band_gap: Electronic band gap (eV)
    - bulk_modulus: Bulk modulus (GPa)
    - shear_modulus: Shear modulus (GPa)
    """
    # Validate input
    if not request.structure_json and not request.cif_string:
        raise HTTPException(
            status_code=400,
            detail="Must provide either structure_json or cif_string"
        )

    try:
        # Parse structure
        structure = ml_service.parse_structure(
            structure_json=request.structure_json,
            cif_string=request.cif_string,
        )

        # Run predictions
        predictions = []
        warnings = []

        for prop in request.properties:
            try:
                result = await ml_service.predict_property(structure, prop)
                predictions.append(
                    PropertyPrediction(
                        name=result["name"],
                        value=result["value"],
                        unit=result.get("unit"),
                        uncertainty=result.get("uncertainty"),
                        model=result["model"],
                    )
                )
            except ValueError as e:
                warnings.append(f"Could not predict {prop}: {str(e)}")

        if not predictions:
            raise HTTPException(
                status_code=400,
                detail="No predictions could be made. " + "; ".join(warnings)
            )

        return PredictResponse(
            predictions=predictions,
            structure_formula=structure.composition.reduced_formula if structure else None,
            warnings=warnings if warnings else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/models")
async def list_available_models():
    """list available ML models and their supported properties"""
    return {
        "models": ml_service.get_available_models(),
        "supported_properties": [
            {
                "name": "formation_energy",
                "description": "Formation energy per atom",
                "unit": "eV/atom",
            },
            {
                "name": "band_gap",
                "description": "Electronic band gap",
                "unit": "eV",
            },
            {
                "name": "bulk_modulus",
                "description": "Bulk modulus",
                "unit": "GPa",
            },
            {
                "name": "shear_modulus",
                "description": "Shear modulus",
                "unit": "GPa",
            },
        ],
    }


@router.post("/batch")
async def predict_batch(
    structures: list[PredictRequest],
    background_tasks: BackgroundTasks,
):
    """
    batch prediction for multiple structures

    returns predictions for each structure
    failed predictions are included with error messages
    """
    if len(structures) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 structures per batch request"
        )

    results = []
    for i, req in enumerate(structures):
        try:
            result = await predict_properties(req, background_tasks)
            results.append({"index": i, "success": True, "result": result})
        except HTTPException as e:
            results.append({
                "index": i,
                "success": False,
                "error": e.detail,
            })

    return {
        "total": len(structures),
        "successful": sum(1 for r in results if r["success"]),
        "results": results,
    }
