"""
Auto-generated FastAPI application for Query API.

Generated: 2026-05-17T11:16:29.405012Z
API Version: 1.0.0

This FastAPI app exposes the API validators as REST endpoints.
"""

from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from loguru import logger

from models import Query, Character, Location, Episode, FilterCharacter, Characters, Info, FilterLocation, FilterEpisode
from validators import APIValidator, ValidationReport
from exceptions import ValidationException, APIException, SchemaException


# Request/Response models for the validation service

class ValidationRequest(BaseModel):
    """Request model for validation endpoint."""
    target_url: str = Field(..., description="Target API base URL to validate against")
    character_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters for GET /query/character"
    )
    characters_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters for GET /query/characters"
    )
    characters_by_ids_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters for GET /query/charactersByIds"
    )
    location_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters for GET /query/location"
    )
    locations_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters for GET /query/locations"
    )
    locations_by_ids_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters for GET /query/locationsByIds"
    )
    episode_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters for GET /query/episode"
    )
    episodes_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters for GET /query/episodes"
    )
    episodes_by_ids_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters for GET /query/episodesByIds"
    )


class ValidationResult(BaseModel):
    """Result of a single endpoint validation."""
    endpoint: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    success: bool = Field(..., description="Whether validation succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")
    drift: Optional[Dict[str, List[str]]] = Field(None, description="Schema drift details")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")


class ValidationResponse(BaseModel):
    """Response model for validation endpoint."""
    api_title: str = Field(..., description="API title")
    api_version: str = Field(..., description="API version")
    target_url: str = Field(..., description="Target URL validated")
    results: List[ValidationResult] = Field(..., description="Validation results")
    summary: Dict[str, Any] = Field(..., description="Validation summary")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    api_title: str = Field(..., description="API title")
    api_version: str = Field(..., description="API version")
    endpoints_count: int = Field(..., description="Number of endpoints")


# Application lifespan management

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    logger.info("Starting Query API validation service")
    yield
    logger.info("Shutting down Query API validation service")


# Create FastAPI application

app = FastAPI(
    title="Query API Validation Service",
    description="GraphQL API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers

@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions."""
    logger.error(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation failed",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle API exceptions."""
    logger.error(f"API error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "API request failed",
            "message": exc.message,
        },
    )


@app.exception_handler(SchemaException)
async def schema_exception_handler(request: Request, exc: SchemaException):
    """Handle schema exceptions."""
    logger.error(f"Schema error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Schema error",
            "message": exc.message,
        },
    )


# Health check endpoint

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and basic information.
    """
    return HealthResponse(
        status="healthy",
        api_title="Query API",
        api_version="1.0.0",
        endpoints_count=9,
    )


# Validation endpoints

@app.post("/validate", response_model=ValidationResponse, tags=["Validation"])
async def validate_api(request: ValidationRequest):
    """
    Validate all API endpoints.
    
    Validates all endpoints of the target API and returns detailed results.
    """
    import time
    
    report = ValidationReport()
    results: List[ValidationResult] = []
    
    async with APIValidator(
        base_url=request.target_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        # Validate GET /query/character
        try:
            start_time = time.time()
            
            # Get parameters from request
            params = request.character_params or {}
            result = await validator.validate_character(
                id=params.get("id", "default"),
            )
            
            response_time = (time.time() - start_time) * 1000
            
            results.append(ValidationResult(
                endpoint="/query/character",
                method="GET",
                success=True,
                response_time_ms=response_time,
            ))
            report.add_result("/query/character", True)
            
        except ValidationException as e:
            results.append(ValidationResult(
                endpoint="/query/character",
                method="GET",
                success=False,
                error=str(e),
            ))
            report.add_result("/query/character", False, error=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error validating /query/character: {e}")
            results.append(ValidationResult(
                endpoint="/query/character",
                method="GET",
                success=False,
                error=f"Unexpected error: {str(e)}",
            ))
            report.add_result("/query/character", False, error=str(e))
        
        # Validate GET /query/characters
        try:
            start_time = time.time()
            
            # Get parameters from request
            params = request.characters_params or {}
            result = await validator.validate_characters(
                page=params.get("page"),
                filter=params.get("filter"),
            )
            
            response_time = (time.time() - start_time) * 1000
            
            results.append(ValidationResult(
                endpoint="/query/characters",
                method="GET",
                success=True,
                response_time_ms=response_time,
            ))
            report.add_result("/query/characters", True)
            
        except ValidationException as e:
            results.append(ValidationResult(
                endpoint="/query/characters",
                method="GET",
                success=False,
                error=str(e),
            ))
            report.add_result("/query/characters", False, error=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error validating /query/characters: {e}")
            results.append(ValidationResult(
                endpoint="/query/characters",
                method="GET",
                success=False,
                error=f"Unexpected error: {str(e)}",
            ))
            report.add_result("/query/characters", False, error=str(e))
        
        # Validate GET /query/charactersByIds
        try:
            start_time = time.time()
            
            # Get parameters from request
            params = request.characters_by_ids_params or {}
            result = await validator.validate_characters_by_ids(
                ids=params.get("ids", []),
            )
            
            response_time = (time.time() - start_time) * 1000
            
            results.append(ValidationResult(
                endpoint="/query/charactersByIds",
                method="GET",
                success=True,
                response_time_ms=response_time,
            ))
            report.add_result("/query/charactersByIds", True)
            
        except ValidationException as e:
            results.append(ValidationResult(
                endpoint="/query/charactersByIds",
                method="GET",
                success=False,
                error=str(e),
            ))
            report.add_result("/query/charactersByIds", False, error=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error validating /query/charactersByIds: {e}")
            results.append(ValidationResult(
                endpoint="/query/charactersByIds",
                method="GET",
                success=False,
                error=f"Unexpected error: {str(e)}",
            ))
            report.add_result("/query/charactersByIds", False, error=str(e))
        
        # Validate GET /query/location
        try:
            start_time = time.time()
            
            # Get parameters from request
            params = request.location_params or {}
            result = await validator.validate_location(
                id=params.get("id", "default"),
            )
            
            response_time = (time.time() - start_time) * 1000
            
            results.append(ValidationResult(
                endpoint="/query/location",
                method="GET",
                success=True,
                response_time_ms=response_time,
            ))
            report.add_result("/query/location", True)
            
        except ValidationException as e:
            results.append(ValidationResult(
                endpoint="/query/location",
                method="GET",
                success=False,
                error=str(e),
            ))
            report.add_result("/query/location", False, error=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error validating /query/location: {e}")
            results.append(ValidationResult(
                endpoint="/query/location",
                method="GET",
                success=False,
                error=f"Unexpected error: {str(e)}",
            ))
            report.add_result("/query/location", False, error=str(e))
        
        # Validate GET /query/locations
        try:
            start_time = time.time()
            
            # Get parameters from request
            params = request.locations_params or {}
            result = await validator.validate_locations(
                page=params.get("page"),
                filter=params.get("filter"),
            )
            
            response_time = (time.time() - start_time) * 1000
            
            results.append(ValidationResult(
                endpoint="/query/locations",
                method="GET",
                success=True,
                response_time_ms=response_time,
            ))
            report.add_result("/query/locations", True)
            
        except ValidationException as e:
            results.append(ValidationResult(
                endpoint="/query/locations",
                method="GET",
                success=False,
                error=str(e),
            ))
            report.add_result("/query/locations", False, error=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error validating /query/locations: {e}")
            results.append(ValidationResult(
                endpoint="/query/locations",
                method="GET",
                success=False,
                error=f"Unexpected error: {str(e)}",
            ))
            report.add_result("/query/locations", False, error=str(e))
        
        # Validate GET /query/locationsByIds
        try:
            start_time = time.time()
            
            # Get parameters from request
            params = request.locations_by_ids_params or {}
            result = await validator.validate_locations_by_ids(
                ids=params.get("ids", []),
            )
            
            response_time = (time.time() - start_time) * 1000
            
            results.append(ValidationResult(
                endpoint="/query/locationsByIds",
                method="GET",
                success=True,
                response_time_ms=response_time,
            ))
            report.add_result("/query/locationsByIds", True)
            
        except ValidationException as e:
            results.append(ValidationResult(
                endpoint="/query/locationsByIds",
                method="GET",
                success=False,
                error=str(e),
            ))
            report.add_result("/query/locationsByIds", False, error=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error validating /query/locationsByIds: {e}")
            results.append(ValidationResult(
                endpoint="/query/locationsByIds",
                method="GET",
                success=False,
                error=f"Unexpected error: {str(e)}",
            ))
            report.add_result("/query/locationsByIds", False, error=str(e))
        
        # Validate GET /query/episode
        try:
            start_time = time.time()
            
            # Get parameters from request
            params = request.episode_params or {}
            result = await validator.validate_episode(
                id=params.get("id", "default"),
            )
            
            response_time = (time.time() - start_time) * 1000
            
            results.append(ValidationResult(
                endpoint="/query/episode",
                method="GET",
                success=True,
                response_time_ms=response_time,
            ))
            report.add_result("/query/episode", True)
            
        except ValidationException as e:
            results.append(ValidationResult(
                endpoint="/query/episode",
                method="GET",
                success=False,
                error=str(e),
            ))
            report.add_result("/query/episode", False, error=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error validating /query/episode: {e}")
            results.append(ValidationResult(
                endpoint="/query/episode",
                method="GET",
                success=False,
                error=f"Unexpected error: {str(e)}",
            ))
            report.add_result("/query/episode", False, error=str(e))
        
        # Validate GET /query/episodes
        try:
            start_time = time.time()
            
            # Get parameters from request
            params = request.episodes_params or {}
            result = await validator.validate_episodes(
                page=params.get("page"),
                filter=params.get("filter"),
            )
            
            response_time = (time.time() - start_time) * 1000
            
            results.append(ValidationResult(
                endpoint="/query/episodes",
                method="GET",
                success=True,
                response_time_ms=response_time,
            ))
            report.add_result("/query/episodes", True)
            
        except ValidationException as e:
            results.append(ValidationResult(
                endpoint="/query/episodes",
                method="GET",
                success=False,
                error=str(e),
            ))
            report.add_result("/query/episodes", False, error=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error validating /query/episodes: {e}")
            results.append(ValidationResult(
                endpoint="/query/episodes",
                method="GET",
                success=False,
                error=f"Unexpected error: {str(e)}",
            ))
            report.add_result("/query/episodes", False, error=str(e))
        
        # Validate GET /query/episodesByIds
        try:
            start_time = time.time()
            
            # Get parameters from request
            params = request.episodes_by_ids_params or {}
            result = await validator.validate_episodes_by_ids(
                ids=params.get("ids", []),
            )
            
            response_time = (time.time() - start_time) * 1000
            
            results.append(ValidationResult(
                endpoint="/query/episodesByIds",
                method="GET",
                success=True,
                response_time_ms=response_time,
            ))
            report.add_result("/query/episodesByIds", True)
            
        except ValidationException as e:
            results.append(ValidationResult(
                endpoint="/query/episodesByIds",
                method="GET",
                success=False,
                error=str(e),
            ))
            report.add_result("/query/episodesByIds", False, error=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error validating /query/episodesByIds: {e}")
            results.append(ValidationResult(
                endpoint="/query/episodesByIds",
                method="GET",
                success=False,
                error=f"Unexpected error: {str(e)}",
            ))
            report.add_result("/query/episodesByIds", False, error=str(e))
        
    
    return ValidationResponse(
        api_title="Query API",
        api_version="1.0.0",
        target_url=request.target_url,
        results=results,
        summary=report.get_summary(),
    )


@app.post(
    "/validate/query/character",
    response_model=Character,
    tags=["Endpoints"],
)
async def validate_character(
    target_url: str,
    id: str,
):
    """
    Validate GET /query/character.
    
    Get a specific character by ID
    
    Args:
        target_url: Target API base URL
        id: No description
    
    Returns:
        Validated response model
    """
    async with APIValidator(
        base_url=target_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        try:
            result = await validator.validate_character(
                id=id,
            )
            return result
        except ValidationException as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e.message}",
            )
        except APIException as e:
            raise HTTPException(
                status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API request failed: {e.message}",
            )

@app.post(
    "/validate/query/characters",
    response_model=Characters,
    tags=["Endpoints"],
)
async def validate_characters(
    target_url: str,
    page: Optional[int] = None,
    filter: Optional[str] = None,
):
    """
    Validate GET /query/characters.
    
    Get the list of all characters
    
    Args:
        target_url: Target API base URL
        page: No description
        filter: No description
    
    Returns:
        Validated response model
    """
    async with APIValidator(
        base_url=target_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        try:
            result = await validator.validate_characters(
                page=page,
                filter=filter,
            )
            return result
        except ValidationException as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e.message}",
            )
        except APIException as e:
            raise HTTPException(
                status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API request failed: {e.message}",
            )

@app.post(
    "/validate/query/charactersByIds",
    response_model=Character,
    tags=["Endpoints"],
)
async def validate_characters_by_ids(
    target_url: str,
    ids: List[Any],
):
    """
    Validate GET /query/charactersByIds.
    
    Get a list of characters selected by ids
    
    Args:
        target_url: Target API base URL
        ids: No description
    
    Returns:
        Validated response model
    """
    async with APIValidator(
        base_url=target_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        try:
            result = await validator.validate_characters_by_ids(
                ids=ids,
            )
            return result
        except ValidationException as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e.message}",
            )
        except APIException as e:
            raise HTTPException(
                status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API request failed: {e.message}",
            )

@app.post(
    "/validate/query/location",
    response_model=Location,
    tags=["Endpoints"],
)
async def validate_location(
    target_url: str,
    id: str,
):
    """
    Validate GET /query/location.
    
    Get a specific locations by ID
    
    Args:
        target_url: Target API base URL
        id: No description
    
    Returns:
        Validated response model
    """
    async with APIValidator(
        base_url=target_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        try:
            result = await validator.validate_location(
                id=id,
            )
            return result
        except ValidationException as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e.message}",
            )
        except APIException as e:
            raise HTTPException(
                status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API request failed: {e.message}",
            )

@app.post(
    "/validate/query/locations",
    response_model=Any,
    tags=["Endpoints"],
)
async def validate_locations(
    target_url: str,
    page: Optional[int] = None,
    filter: Optional[str] = None,
):
    """
    Validate GET /query/locations.
    
    Get the list of all locations
    
    Args:
        target_url: Target API base URL
        page: No description
        filter: No description
    
    Returns:
        Validated response model
    """
    async with APIValidator(
        base_url=target_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        try:
            result = await validator.validate_locations(
                page=page,
                filter=filter,
            )
            return result
        except ValidationException as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e.message}",
            )
        except APIException as e:
            raise HTTPException(
                status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API request failed: {e.message}",
            )

@app.post(
    "/validate/query/locationsByIds",
    response_model=Location,
    tags=["Endpoints"],
)
async def validate_locations_by_ids(
    target_url: str,
    ids: List[Any],
):
    """
    Validate GET /query/locationsByIds.
    
    Get a list of locations selected by ids
    
    Args:
        target_url: Target API base URL
        ids: No description
    
    Returns:
        Validated response model
    """
    async with APIValidator(
        base_url=target_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        try:
            result = await validator.validate_locations_by_ids(
                ids=ids,
            )
            return result
        except ValidationException as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e.message}",
            )
        except APIException as e:
            raise HTTPException(
                status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API request failed: {e.message}",
            )

@app.post(
    "/validate/query/episode",
    response_model=Episode,
    tags=["Endpoints"],
)
async def validate_episode(
    target_url: str,
    id: str,
):
    """
    Validate GET /query/episode.
    
    Get a specific episode by ID
    
    Args:
        target_url: Target API base URL
        id: No description
    
    Returns:
        Validated response model
    """
    async with APIValidator(
        base_url=target_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        try:
            result = await validator.validate_episode(
                id=id,
            )
            return result
        except ValidationException as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e.message}",
            )
        except APIException as e:
            raise HTTPException(
                status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API request failed: {e.message}",
            )

@app.post(
    "/validate/query/episodes",
    response_model=Any,
    tags=["Endpoints"],
)
async def validate_episodes(
    target_url: str,
    page: Optional[int] = None,
    filter: Optional[str] = None,
):
    """
    Validate GET /query/episodes.
    
    Get the list of all episodes
    
    Args:
        target_url: Target API base URL
        page: No description
        filter: No description
    
    Returns:
        Validated response model
    """
    async with APIValidator(
        base_url=target_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        try:
            result = await validator.validate_episodes(
                page=page,
                filter=filter,
            )
            return result
        except ValidationException as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e.message}",
            )
        except APIException as e:
            raise HTTPException(
                status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API request failed: {e.message}",
            )

@app.post(
    "/validate/query/episodesByIds",
    response_model=Episode,
    tags=["Endpoints"],
)
async def validate_episodes_by_ids(
    target_url: str,
    ids: List[Any],
):
    """
    Validate GET /query/episodesByIds.
    
    Get a list of episodes selected by ids
    
    Args:
        target_url: Target API base URL
        ids: No description
    
    Returns:
        Validated response model
    """
    async with APIValidator(
        base_url=target_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        try:
            result = await validator.validate_episodes_by_ids(
                ids=ids,
            )
            return result
        except ValidationException as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e.message}",
            )
        except APIException as e:
            raise HTTPException(
                status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API request failed: {e.message}",
            )


# OpenAPI schema endpoint

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    """Get OpenAPI schema."""
    return app.openapi()


# Root endpoint

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns basic API information and available endpoints.
    """
    return {
        "title": "Query API Validation Service",
        "version": "1.0.0",
        "description": "GraphQL API",
        "endpoints": {
            "health": "/health",
            "validate_all": "/validate",
            "openapi": "/openapi.json",
            "docs": "/docs",
            "redoc": "/redoc",
        },
        "target_api": {
            "title": "Query API",
            "version": "1.0.0",
            "base_url": "https://rickandmortyapi.com",
            "endpoints_count": 9,
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )