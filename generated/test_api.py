"""
Auto-generated API tests for Query API.

Generated: 2026-05-16T20:57:58.377674Z
API Version: 1.0.0

This test suite uses pytest and polyfactory to test all API endpoints.
"""

import pytest
from typing import Any, Dict
from polyfactory.factories.pydantic_factory import ModelFactory

from models import Query, Character, Location, Episode, FilterCharacter, Characters, Info, FilterLocation, FilterEpisode
from validators import APIValidator


# Pydantic model factories for generating test data
class QueryFactory(ModelFactory[Query]):
    """Factory for generating Query test instances."""
    __model__ = Query

class CharacterFactory(ModelFactory[Character]):
    """Factory for generating Character test instances."""
    __model__ = Character

class LocationFactory(ModelFactory[Location]):
    """Factory for generating Location test instances."""
    __model__ = Location

class EpisodeFactory(ModelFactory[Episode]):
    """Factory for generating Episode test instances."""
    __model__ = Episode

class FilterCharacterFactory(ModelFactory[FilterCharacter]):
    """Factory for generating FilterCharacter test instances."""
    __model__ = FilterCharacter

class CharactersFactory(ModelFactory[Characters]):
    """Factory for generating Characters test instances."""
    __model__ = Characters

class InfoFactory(ModelFactory[Info]):
    """Factory for generating Info test instances."""
    __model__ = Info

class FilterLocationFactory(ModelFactory[FilterLocation]):
    """Factory for generating FilterLocation test instances."""
    __model__ = FilterLocation

class FilterEpisodeFactory(ModelFactory[FilterEpisode]):
    """Factory for generating FilterEpisode test instances."""
    __model__ = FilterEpisode


@pytest.fixture
def api_base_url():
    """Base URL for API tests."""
    return "https://rickandmortyapi.com/graphql"


@pytest.fixture
async def api_validator(api_base_url):
    """Create API validator instance."""
    async with APIValidator(
        base_url=api_base_url,
        timeout=30.0,
        max_retries=3,
    ) as validator:
        yield validator


@pytest.fixture
def mock_response_data():
    """Generate mock response data for testing."""
    return {
        "Query": QueryFactory.build().model_dump(),
        "Character": CharacterFactory.build().model_dump(),
        "Location": LocationFactory.build().model_dump(),
        "Episode": EpisodeFactory.build().model_dump(),
        "FilterCharacter": FilterCharacterFactory.build().model_dump(),
        "Characters": CharactersFactory.build().model_dump(),
        "Info": InfoFactory.build().model_dump(),
        "FilterLocation": FilterLocationFactory.build().model_dump(),
        "FilterEpisode": FilterEpisodeFactory.build().model_dump(),
    }

# Tests for GET /query/character

@pytest.mark.asyncio
async def test_character_success(api_validator, httpx_mock):
    """
    Test successful GET /query/character.
    
    Get a specific character by ID
    """
    # Arrange: Create mock response data
    mock_data = CharacterFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/character",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Call the validator
    result = await api_validator.validate_character(
        id="test_value",
    )
    
    # Assert: Verify the result
    assert isinstance(result, Character)


@pytest.mark.asyncio
async def test_character_validation_error(api_validator, httpx_mock):
    """
    Test GET /query/character with invalid response data.
    
    Should raise ValidationException when response doesn't match schema.
    """
    from exceptions import ValidationException
    
    # Arrange: Create invalid response data
    invalid_data = {"invalid": "data", "missing": "required_fields"}
    
    # Mock the HTTP response with invalid data
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/character",
        json=invalid_data,
        status_code=200,
    )
    
    # Act & Assert: Should raise ValidationException
    with pytest.raises(ValidationException):
        await api_validator.validate_character(
            id="test_value",
        )


@pytest.mark.asyncio
async def test_character_http_error(api_validator, httpx_mock):
    """
    Test GET /query/character with HTTP error.
    
    Should raise APIException when HTTP request fails.
    """
    from exceptions import APIException
    
    # Mock HTTP error response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/character",
        status_code=404,
        json={"error": "Not found"},
    )
    
    # Act & Assert: Should raise APIException
    with pytest.raises(APIException):
        await api_validator.validate_character(
            id="test_value",
        )


@pytest.mark.asyncio
async def test_character_schema_drift(api_validator, httpx_mock):
    """
    Test GET /query/character with schema drift.
    
    Should detect when response has extra or missing fields.
    """
    # Arrange: Create response with extra fields
    mock_data = CharacterFactory.build()
    response_data = mock_data.model_dump()
    response_data["extra_field"] = "unexpected"
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/character",
        json=response_data,
        status_code=200,
    )
    
    # Act: Call the validator (should log warning but not fail)
    result = await api_validator.validate_character(
        id="test_value",
    )
    
    # Assert: Should still return valid result despite drift
    assert isinstance(result, Character)


@pytest.mark.asyncio
async def test_character_with_parameters(api_validator, httpx_mock):
    """
    Test GET /query/character with various parameter combinations.
    """
    # Arrange: Create mock response
    mock_data = CharacterFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/character",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Test with different parameter values
    result = await api_validator.validate_character(
        id="test_value",
    )
    
    # Assert
    assert isinstance(result, Character)

# Tests for GET /query/characters

@pytest.mark.asyncio
async def test_characters_success(api_validator, httpx_mock):
    """
    Test successful GET /query/characters.
    
    Get the list of all characters
    """
    # Arrange: Create mock response data
    mock_data = CharactersFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/characters",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Call the validator
    result = await api_validator.validate_characters(
    )
    
    # Assert: Verify the result
    assert isinstance(result, Characters)


@pytest.mark.asyncio
async def test_characters_validation_error(api_validator, httpx_mock):
    """
    Test GET /query/characters with invalid response data.
    
    Should raise ValidationException when response doesn't match schema.
    """
    from exceptions import ValidationException
    
    # Arrange: Create invalid response data
    invalid_data = {"invalid": "data", "missing": "required_fields"}
    
    # Mock the HTTP response with invalid data
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/characters",
        json=invalid_data,
        status_code=200,
    )
    
    # Act & Assert: Should raise ValidationException
    with pytest.raises(ValidationException):
        await api_validator.validate_characters(
        )


@pytest.mark.asyncio
async def test_characters_http_error(api_validator, httpx_mock):
    """
    Test GET /query/characters with HTTP error.
    
    Should raise APIException when HTTP request fails.
    """
    from exceptions import APIException
    
    # Mock HTTP error response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/characters",
        status_code=404,
        json={"error": "Not found"},
    )
    
    # Act & Assert: Should raise APIException
    with pytest.raises(APIException):
        await api_validator.validate_characters(
        )


@pytest.mark.asyncio
async def test_characters_schema_drift(api_validator, httpx_mock):
    """
    Test GET /query/characters with schema drift.
    
    Should detect when response has extra or missing fields.
    """
    # Arrange: Create response with extra fields
    mock_data = CharactersFactory.build()
    response_data = mock_data.model_dump()
    response_data["extra_field"] = "unexpected"
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/characters",
        json=response_data,
        status_code=200,
    )
    
    # Act: Call the validator (should log warning but not fail)
    result = await api_validator.validate_characters(
    )
    
    # Assert: Should still return valid result despite drift
    assert isinstance(result, Characters)


@pytest.mark.asyncio
async def test_characters_with_parameters(api_validator, httpx_mock):
    """
    Test GET /query/characters with various parameter combinations.
    """
    # Arrange: Create mock response
    mock_data = CharactersFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/characters",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Test with different parameter values
    result = await api_validator.validate_characters(
        page=123,
        filter="test_value",
    )
    
    # Assert
    assert isinstance(result, Characters)

# Tests for GET /query/charactersByIds

@pytest.mark.asyncio
async def test_characters_by_ids_success(api_validator, httpx_mock):
    """
    Test successful GET /query/charactersByIds.
    
    Get a list of characters selected by ids
    """
    # Arrange: Create mock response data
    mock_data = CharacterFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/charactersByIds",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Call the validator
    result = await api_validator.validate_characters_by_ids(
        ids=[],
    )
    
    # Assert: Verify the result
    assert isinstance(result, Character)


@pytest.mark.asyncio
async def test_characters_by_ids_validation_error(api_validator, httpx_mock):
    """
    Test GET /query/charactersByIds with invalid response data.
    
    Should raise ValidationException when response doesn't match schema.
    """
    from exceptions import ValidationException
    
    # Arrange: Create invalid response data
    invalid_data = {"invalid": "data", "missing": "required_fields"}
    
    # Mock the HTTP response with invalid data
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/charactersByIds",
        json=invalid_data,
        status_code=200,
    )
    
    # Act & Assert: Should raise ValidationException
    with pytest.raises(ValidationException):
        await api_validator.validate_characters_by_ids(
            ids=[],
        )


@pytest.mark.asyncio
async def test_characters_by_ids_http_error(api_validator, httpx_mock):
    """
    Test GET /query/charactersByIds with HTTP error.
    
    Should raise APIException when HTTP request fails.
    """
    from exceptions import APIException
    
    # Mock HTTP error response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/charactersByIds",
        status_code=404,
        json={"error": "Not found"},
    )
    
    # Act & Assert: Should raise APIException
    with pytest.raises(APIException):
        await api_validator.validate_characters_by_ids(
            ids=[],
        )


@pytest.mark.asyncio
async def test_characters_by_ids_schema_drift(api_validator, httpx_mock):
    """
    Test GET /query/charactersByIds with schema drift.
    
    Should detect when response has extra or missing fields.
    """
    # Arrange: Create response with extra fields
    mock_data = CharacterFactory.build()
    response_data = mock_data.model_dump()
    response_data["extra_field"] = "unexpected"
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/charactersByIds",
        json=response_data,
        status_code=200,
    )
    
    # Act: Call the validator (should log warning but not fail)
    result = await api_validator.validate_characters_by_ids(
        ids=[],
    )
    
    # Assert: Should still return valid result despite drift
    assert isinstance(result, Character)


@pytest.mark.asyncio
async def test_characters_by_ids_with_parameters(api_validator, httpx_mock):
    """
    Test GET /query/charactersByIds with various parameter combinations.
    """
    # Arrange: Create mock response
    mock_data = CharacterFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/charactersByIds",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Test with different parameter values
    result = await api_validator.validate_characters_by_ids(
        ids=[],
    )
    
    # Assert
    assert isinstance(result, Character)

# Tests for GET /query/location

@pytest.mark.asyncio
async def test_location_success(api_validator, httpx_mock):
    """
    Test successful GET /query/location.
    
    Get a specific locations by ID
    """
    # Arrange: Create mock response data
    mock_data = LocationFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/location",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Call the validator
    result = await api_validator.validate_location(
        id="test_value",
    )
    
    # Assert: Verify the result
    assert isinstance(result, Location)


@pytest.mark.asyncio
async def test_location_validation_error(api_validator, httpx_mock):
    """
    Test GET /query/location with invalid response data.
    
    Should raise ValidationException when response doesn't match schema.
    """
    from exceptions import ValidationException
    
    # Arrange: Create invalid response data
    invalid_data = {"invalid": "data", "missing": "required_fields"}
    
    # Mock the HTTP response with invalid data
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/location",
        json=invalid_data,
        status_code=200,
    )
    
    # Act & Assert: Should raise ValidationException
    with pytest.raises(ValidationException):
        await api_validator.validate_location(
            id="test_value",
        )


@pytest.mark.asyncio
async def test_location_http_error(api_validator, httpx_mock):
    """
    Test GET /query/location with HTTP error.
    
    Should raise APIException when HTTP request fails.
    """
    from exceptions import APIException
    
    # Mock HTTP error response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/location",
        status_code=404,
        json={"error": "Not found"},
    )
    
    # Act & Assert: Should raise APIException
    with pytest.raises(APIException):
        await api_validator.validate_location(
            id="test_value",
        )


@pytest.mark.asyncio
async def test_location_schema_drift(api_validator, httpx_mock):
    """
    Test GET /query/location with schema drift.
    
    Should detect when response has extra or missing fields.
    """
    # Arrange: Create response with extra fields
    mock_data = LocationFactory.build()
    response_data = mock_data.model_dump()
    response_data["extra_field"] = "unexpected"
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/location",
        json=response_data,
        status_code=200,
    )
    
    # Act: Call the validator (should log warning but not fail)
    result = await api_validator.validate_location(
        id="test_value",
    )
    
    # Assert: Should still return valid result despite drift
    assert isinstance(result, Location)


@pytest.mark.asyncio
async def test_location_with_parameters(api_validator, httpx_mock):
    """
    Test GET /query/location with various parameter combinations.
    """
    # Arrange: Create mock response
    mock_data = LocationFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/location",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Test with different parameter values
    result = await api_validator.validate_location(
        id="test_value",
    )
    
    # Assert
    assert isinstance(result, Location)

# Tests for GET /query/locations

@pytest.mark.asyncio
async def test_locations_success(api_validator, httpx_mock):
    """
    Test successful GET /query/locations.
    
    Get the list of all locations
    """
    # Arrange: Create mock response data
    mock_data = LocationsFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/locations",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Call the validator
    result = await api_validator.validate_locations(
    )
    
    # Assert: Verify the result
    assert isinstance(result, Locations)


@pytest.mark.asyncio
async def test_locations_validation_error(api_validator, httpx_mock):
    """
    Test GET /query/locations with invalid response data.
    
    Should raise ValidationException when response doesn't match schema.
    """
    from exceptions import ValidationException
    
    # Arrange: Create invalid response data
    invalid_data = {"invalid": "data", "missing": "required_fields"}
    
    # Mock the HTTP response with invalid data
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/locations",
        json=invalid_data,
        status_code=200,
    )
    
    # Act & Assert: Should raise ValidationException
    with pytest.raises(ValidationException):
        await api_validator.validate_locations(
        )


@pytest.mark.asyncio
async def test_locations_http_error(api_validator, httpx_mock):
    """
    Test GET /query/locations with HTTP error.
    
    Should raise APIException when HTTP request fails.
    """
    from exceptions import APIException
    
    # Mock HTTP error response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/locations",
        status_code=404,
        json={"error": "Not found"},
    )
    
    # Act & Assert: Should raise APIException
    with pytest.raises(APIException):
        await api_validator.validate_locations(
        )


@pytest.mark.asyncio
async def test_locations_schema_drift(api_validator, httpx_mock):
    """
    Test GET /query/locations with schema drift.
    
    Should detect when response has extra or missing fields.
    """
    # Arrange: Create response with extra fields
    mock_data = LocationsFactory.build()
    response_data = mock_data.model_dump()
    response_data["extra_field"] = "unexpected"
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/locations",
        json=response_data,
        status_code=200,
    )
    
    # Act: Call the validator (should log warning but not fail)
    result = await api_validator.validate_locations(
    )
    
    # Assert: Should still return valid result despite drift
    assert isinstance(result, Locations)


@pytest.mark.asyncio
async def test_locations_with_parameters(api_validator, httpx_mock):
    """
    Test GET /query/locations with various parameter combinations.
    """
    # Arrange: Create mock response
    mock_data = LocationsFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/locations",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Test with different parameter values
    result = await api_validator.validate_locations(
        page=123,
        filter="test_value",
    )
    
    # Assert
    assert isinstance(result, Locations)

# Tests for GET /query/locationsByIds

@pytest.mark.asyncio
async def test_locations_by_ids_success(api_validator, httpx_mock):
    """
    Test successful GET /query/locationsByIds.
    
    Get a list of locations selected by ids
    """
    # Arrange: Create mock response data
    mock_data = LocationFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/locationsByIds",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Call the validator
    result = await api_validator.validate_locations_by_ids(
        ids=[],
    )
    
    # Assert: Verify the result
    assert isinstance(result, Location)


@pytest.mark.asyncio
async def test_locations_by_ids_validation_error(api_validator, httpx_mock):
    """
    Test GET /query/locationsByIds with invalid response data.
    
    Should raise ValidationException when response doesn't match schema.
    """
    from exceptions import ValidationException
    
    # Arrange: Create invalid response data
    invalid_data = {"invalid": "data", "missing": "required_fields"}
    
    # Mock the HTTP response with invalid data
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/locationsByIds",
        json=invalid_data,
        status_code=200,
    )
    
    # Act & Assert: Should raise ValidationException
    with pytest.raises(ValidationException):
        await api_validator.validate_locations_by_ids(
            ids=[],
        )


@pytest.mark.asyncio
async def test_locations_by_ids_http_error(api_validator, httpx_mock):
    """
    Test GET /query/locationsByIds with HTTP error.
    
    Should raise APIException when HTTP request fails.
    """
    from exceptions import APIException
    
    # Mock HTTP error response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/locationsByIds",
        status_code=404,
        json={"error": "Not found"},
    )
    
    # Act & Assert: Should raise APIException
    with pytest.raises(APIException):
        await api_validator.validate_locations_by_ids(
            ids=[],
        )


@pytest.mark.asyncio
async def test_locations_by_ids_schema_drift(api_validator, httpx_mock):
    """
    Test GET /query/locationsByIds with schema drift.
    
    Should detect when response has extra or missing fields.
    """
    # Arrange: Create response with extra fields
    mock_data = LocationFactory.build()
    response_data = mock_data.model_dump()
    response_data["extra_field"] = "unexpected"
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/locationsByIds",
        json=response_data,
        status_code=200,
    )
    
    # Act: Call the validator (should log warning but not fail)
    result = await api_validator.validate_locations_by_ids(
        ids=[],
    )
    
    # Assert: Should still return valid result despite drift
    assert isinstance(result, Location)


@pytest.mark.asyncio
async def test_locations_by_ids_with_parameters(api_validator, httpx_mock):
    """
    Test GET /query/locationsByIds with various parameter combinations.
    """
    # Arrange: Create mock response
    mock_data = LocationFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/locationsByIds",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Test with different parameter values
    result = await api_validator.validate_locations_by_ids(
        ids=[],
    )
    
    # Assert
    assert isinstance(result, Location)

# Tests for GET /query/episode

@pytest.mark.asyncio
async def test_episode_success(api_validator, httpx_mock):
    """
    Test successful GET /query/episode.
    
    Get a specific episode by ID
    """
    # Arrange: Create mock response data
    mock_data = EpisodeFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episode",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Call the validator
    result = await api_validator.validate_episode(
        id="test_value",
    )
    
    # Assert: Verify the result
    assert isinstance(result, Episode)


@pytest.mark.asyncio
async def test_episode_validation_error(api_validator, httpx_mock):
    """
    Test GET /query/episode with invalid response data.
    
    Should raise ValidationException when response doesn't match schema.
    """
    from exceptions import ValidationException
    
    # Arrange: Create invalid response data
    invalid_data = {"invalid": "data", "missing": "required_fields"}
    
    # Mock the HTTP response with invalid data
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episode",
        json=invalid_data,
        status_code=200,
    )
    
    # Act & Assert: Should raise ValidationException
    with pytest.raises(ValidationException):
        await api_validator.validate_episode(
            id="test_value",
        )


@pytest.mark.asyncio
async def test_episode_http_error(api_validator, httpx_mock):
    """
    Test GET /query/episode with HTTP error.
    
    Should raise APIException when HTTP request fails.
    """
    from exceptions import APIException
    
    # Mock HTTP error response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episode",
        status_code=404,
        json={"error": "Not found"},
    )
    
    # Act & Assert: Should raise APIException
    with pytest.raises(APIException):
        await api_validator.validate_episode(
            id="test_value",
        )


@pytest.mark.asyncio
async def test_episode_schema_drift(api_validator, httpx_mock):
    """
    Test GET /query/episode with schema drift.
    
    Should detect when response has extra or missing fields.
    """
    # Arrange: Create response with extra fields
    mock_data = EpisodeFactory.build()
    response_data = mock_data.model_dump()
    response_data["extra_field"] = "unexpected"
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episode",
        json=response_data,
        status_code=200,
    )
    
    # Act: Call the validator (should log warning but not fail)
    result = await api_validator.validate_episode(
        id="test_value",
    )
    
    # Assert: Should still return valid result despite drift
    assert isinstance(result, Episode)


@pytest.mark.asyncio
async def test_episode_with_parameters(api_validator, httpx_mock):
    """
    Test GET /query/episode with various parameter combinations.
    """
    # Arrange: Create mock response
    mock_data = EpisodeFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episode",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Test with different parameter values
    result = await api_validator.validate_episode(
        id="test_value",
    )
    
    # Assert
    assert isinstance(result, Episode)

# Tests for GET /query/episodes

@pytest.mark.asyncio
async def test_episodes_success(api_validator, httpx_mock):
    """
    Test successful GET /query/episodes.
    
    Get the list of all episodes
    """
    # Arrange: Create mock response data
    mock_data = EpisodesFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episodes",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Call the validator
    result = await api_validator.validate_episodes(
    )
    
    # Assert: Verify the result
    assert isinstance(result, Episodes)


@pytest.mark.asyncio
async def test_episodes_validation_error(api_validator, httpx_mock):
    """
    Test GET /query/episodes with invalid response data.
    
    Should raise ValidationException when response doesn't match schema.
    """
    from exceptions import ValidationException
    
    # Arrange: Create invalid response data
    invalid_data = {"invalid": "data", "missing": "required_fields"}
    
    # Mock the HTTP response with invalid data
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episodes",
        json=invalid_data,
        status_code=200,
    )
    
    # Act & Assert: Should raise ValidationException
    with pytest.raises(ValidationException):
        await api_validator.validate_episodes(
        )


@pytest.mark.asyncio
async def test_episodes_http_error(api_validator, httpx_mock):
    """
    Test GET /query/episodes with HTTP error.
    
    Should raise APIException when HTTP request fails.
    """
    from exceptions import APIException
    
    # Mock HTTP error response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episodes",
        status_code=404,
        json={"error": "Not found"},
    )
    
    # Act & Assert: Should raise APIException
    with pytest.raises(APIException):
        await api_validator.validate_episodes(
        )


@pytest.mark.asyncio
async def test_episodes_schema_drift(api_validator, httpx_mock):
    """
    Test GET /query/episodes with schema drift.
    
    Should detect when response has extra or missing fields.
    """
    # Arrange: Create response with extra fields
    mock_data = EpisodesFactory.build()
    response_data = mock_data.model_dump()
    response_data["extra_field"] = "unexpected"
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episodes",
        json=response_data,
        status_code=200,
    )
    
    # Act: Call the validator (should log warning but not fail)
    result = await api_validator.validate_episodes(
    )
    
    # Assert: Should still return valid result despite drift
    assert isinstance(result, Episodes)


@pytest.mark.asyncio
async def test_episodes_with_parameters(api_validator, httpx_mock):
    """
    Test GET /query/episodes with various parameter combinations.
    """
    # Arrange: Create mock response
    mock_data = EpisodesFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episodes",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Test with different parameter values
    result = await api_validator.validate_episodes(
        page=123,
        filter="test_value",
    )
    
    # Assert
    assert isinstance(result, Episodes)

# Tests for GET /query/episodesByIds

@pytest.mark.asyncio
async def test_episodes_by_ids_success(api_validator, httpx_mock):
    """
    Test successful GET /query/episodesByIds.
    
    Get a list of episodes selected by ids
    """
    # Arrange: Create mock response data
    mock_data = EpisodeFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episodesByIds",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Call the validator
    result = await api_validator.validate_episodes_by_ids(
        ids=[],
    )
    
    # Assert: Verify the result
    assert isinstance(result, Episode)


@pytest.mark.asyncio
async def test_episodes_by_ids_validation_error(api_validator, httpx_mock):
    """
    Test GET /query/episodesByIds with invalid response data.
    
    Should raise ValidationException when response doesn't match schema.
    """
    from exceptions import ValidationException
    
    # Arrange: Create invalid response data
    invalid_data = {"invalid": "data", "missing": "required_fields"}
    
    # Mock the HTTP response with invalid data
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episodesByIds",
        json=invalid_data,
        status_code=200,
    )
    
    # Act & Assert: Should raise ValidationException
    with pytest.raises(ValidationException):
        await api_validator.validate_episodes_by_ids(
            ids=[],
        )


@pytest.mark.asyncio
async def test_episodes_by_ids_http_error(api_validator, httpx_mock):
    """
    Test GET /query/episodesByIds with HTTP error.
    
    Should raise APIException when HTTP request fails.
    """
    from exceptions import APIException
    
    # Mock HTTP error response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episodesByIds",
        status_code=404,
        json={"error": "Not found"},
    )
    
    # Act & Assert: Should raise APIException
    with pytest.raises(APIException):
        await api_validator.validate_episodes_by_ids(
            ids=[],
        )


@pytest.mark.asyncio
async def test_episodes_by_ids_schema_drift(api_validator, httpx_mock):
    """
    Test GET /query/episodesByIds with schema drift.
    
    Should detect when response has extra or missing fields.
    """
    # Arrange: Create response with extra fields
    mock_data = EpisodeFactory.build()
    response_data = mock_data.model_dump()
    response_data["extra_field"] = "unexpected"
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episodesByIds",
        json=response_data,
        status_code=200,
    )
    
    # Act: Call the validator (should log warning but not fail)
    result = await api_validator.validate_episodes_by_ids(
        ids=[],
    )
    
    # Assert: Should still return valid result despite drift
    assert isinstance(result, Episode)


@pytest.mark.asyncio
async def test_episodes_by_ids_with_parameters(api_validator, httpx_mock):
    """
    Test GET /query/episodesByIds with various parameter combinations.
    """
    # Arrange: Create mock response
    mock_data = EpisodeFactory.build()
    
    # Mock the HTTP response
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/episodesByIds",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Test with different parameter values
    result = await api_validator.validate_episodes_by_ids(
        ids=[],
    )
    
    # Assert
    assert isinstance(result, Episode)


# Integration tests

@pytest.mark.asyncio
async def test_api_validator_context_manager(api_base_url):
    """Test APIValidator as async context manager."""
    async with APIValidator(base_url=api_base_url) as validator:
        assert validator._client is not None
    
    # Client should be closed after context exit
    # Note: We can't directly test this without accessing private attributes


@pytest.mark.asyncio
async def test_api_validator_caching(api_base_url, httpx_mock):
    """Test response caching functionality."""
    # Arrange: Create mock response
    mock_data = QueryFactory.build()
    
    httpx_mock.add_response(
        method="GET",
        url=f"{api_base_url}/query/character",
        json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
        status_code=200,
    )
    
    # Act: Make two requests with caching enabled
    async with APIValidator(base_url=api_base_url, enable_cache=True) as validator:
        result1 = await validator.validate_character(
        )
        result2 = await validator.validate_character(
        )
        
        # Assert: Both results should be identical (from cache)
        assert result1 == result2


@pytest.mark.asyncio
async def test_validation_report():
    """Test ValidationReport functionality."""
    from validators import ValidationReport
    
    report = ValidationReport()
    
    # Add some results
    report.add_result("/users", True)
    report.add_result("/posts", False, error="Validation failed")
    report.add_result("/comments", True, drift={"extra": ["field1"]})
    
    # Get summary
    summary = report.get_summary()
    assert summary["total"] == 3
    assert summary["successful"] == 2
    assert summary["failed"] == 1
    assert summary["drift_detected"] == 1
    assert summary["success_rate"] == pytest.approx(66.67, rel=0.01)
    
    # Get failed endpoints
    failed = report.get_failed_endpoints()
    assert len(failed) == 1
    assert failed[0]["endpoint"] == "/posts"
    
    # Get drift endpoints
    drift = report.get_drift_endpoints()
    assert len(drift) == 1
    assert drift[0]["endpoint"] == "/comments"


# Performance tests

@pytest.mark.asyncio
@pytest.mark.slow
async def test_concurrent_requests(api_base_url, httpx_mock):
    """Test handling multiple concurrent requests."""
    import asyncio
    
    # Arrange: Mock multiple responses
    mock_data = QueryFactory.build()
    
    for _ in range(10):
        httpx_mock.add_response(
            method="GET",
            url=f"{api_base_url}/query/character",
            json=mock_data.model_dump() if hasattr(mock_data, 'model_dump') else mock_data,
            status_code=200,
        )
    
    # Act: Make concurrent requests
    async with APIValidator(base_url=api_base_url) as validator:
        tasks = [
            validator.validate_character(
            )
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)
        
        # Assert: All requests should succeed
        assert len(results) == 10


# Edge case tests

@pytest.mark.asyncio
async def test_empty_response(api_validator, httpx_mock):
    """Test handling of empty response."""
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/character",
        json={},
        status_code=200,
    )
    
    # Should handle empty response gracefully
    with pytest.raises(Exception):  # Could be ValidationException or other
        await api_validator.validate_character(
        )


@pytest.mark.asyncio
async def test_malformed_json(api_validator, httpx_mock):
    """Test handling of malformed JSON response."""
    httpx_mock.add_response(
        method="GET",
        url="https://rickandmortyapi.com/graphql/query/character",
        content=b"not valid json",
        status_code=200,
    )
    
    from exceptions import ValidationException
    
    with pytest.raises(ValidationException):
        await api_validator.validate_character(
        )
