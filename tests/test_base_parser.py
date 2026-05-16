"""
Comprehensive tests for parsers/base_parser.py

Tests BaseParser abstract class and its helper methods.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, mock_open
import tempfile
import json

from parsers.base_parser import BaseParser
from schemas import APISchema, Endpoint, ModelSchema, FieldSchema, FieldType
from core.exceptions import ParserError


# ============================================================================
# Test Parser Implementation
# ============================================================================

class TestParser(BaseParser):
    """Concrete test implementation of BaseParser."""
    
    def __init__(self, source: str | Path):
        super().__init__(source)
        self.parse_called = False
        self.extract_endpoints_called = False
        self.extract_models_called = False
    
    async def parse(self) -> APISchema:
        """Test implementation of parse."""
        self.parse_called = True
        return APISchema(
            title="Test API",
            version="1.0.0",
            base_url="https://api.example.com",
            endpoints=[],
            models={}
        )
    
    def extract_endpoints(self, spec: dict) -> list[Endpoint]:
        """Test implementation of extract_endpoints."""
        self.extract_endpoints_called = True
        return []
    
    def extract_models(self, spec: dict) -> dict[str, ModelSchema]:
        """Test implementation of extract_models."""
        self.extract_models_called = True
        return {}


# ============================================================================
# Initialization Tests
# ============================================================================

class TestBaseParserInitialization:
    """Test BaseParser initialization."""
    
    def test_initialization_with_string_path(self):
        """Test initialization with string path."""
        parser = TestParser("/path/to/spec.yaml")
        
        assert parser.source == "/path/to/spec.yaml"
    
    def test_initialization_with_path_object(self):
        """Test initialization with Path object."""
        path = Path("/path/to/spec.yaml")
        parser = TestParser(path)
        
        assert parser.source == "/path/to/spec.yaml"
    
    def test_initialization_with_url(self):
        """Test initialization with URL."""
        parser = TestParser("https://api.example.com/spec.yaml")
        
        assert parser.source == "https://api.example.com/spec.yaml"


# ============================================================================
# Abstract Method Tests
# ============================================================================

class TestBaseParserAbstractMethods:
    """Test that abstract methods must be implemented."""
    
    @pytest.mark.asyncio
    async def test_parse_is_implemented(self):
        """Test parse method is implemented in subclass."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = await parser.parse()
        
        assert parser.parse_called
        assert isinstance(result, APISchema)
    
    def test_extract_endpoints_is_implemented(self):
        """Test extract_endpoints is implemented in subclass."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser.extract_endpoints({})
        
        assert parser.extract_endpoints_called
        assert isinstance(result, list)
    
    def test_extract_models_is_implemented(self):
        """Test extract_models is implemented in subclass."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser.extract_models({})
        
        assert parser.extract_models_called
        assert isinstance(result, dict)


# ============================================================================
# Validate Source Tests
# ============================================================================

class TestBaseParserValidateSource:
    """Test BaseParser validate_source method."""
    
    def test_validate_source_url_returns_true(self):
        """Test validate_source returns True for URLs."""
        parser = TestParser("https://api.example.com/spec.yaml")
        
        result = parser.validate_source()
        
        assert result is True
    
    def test_validate_source_existing_file(self):
        """Test validate_source returns True for existing file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test: data")
            temp_path = f.name
        
        try:
            parser = TestParser(temp_path)
            result = parser.validate_source()
            assert result is True
        finally:
            Path(temp_path).unlink()
    
    def test_validate_source_nonexistent_file(self):
        """Test validate_source returns False for nonexistent file."""
        parser = TestParser("/nonexistent/path/spec.yaml")
        
        result = parser.validate_source()
        
        assert result is False
    
    def test_validate_source_directory_not_file(self):
        """Test validate_source returns False for directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = TestParser(temp_dir)
            
            result = parser.validate_source()
            
            assert result is False


# ============================================================================
# Load File Tests
# ============================================================================

class TestBaseParserLoadFile:
    """Test BaseParser _load_file method."""
    
    def test_load_json_file(self):
        """Test loading JSON file."""
        test_data = {"test": "data", "number": 123}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)
        
        try:
            parser = TestParser(str(temp_path))
            result = parser._load_file(temp_path)
            
            assert result == test_data
        finally:
            temp_path.unlink()
    
    def test_load_yaml_file(self):
        """Test loading YAML file."""
        yaml_content = "test: data\nnumber: 123\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            parser = TestParser(str(temp_path))
            result = parser._load_file(temp_path)
            
            assert result["test"] == "data"
            assert result["number"] == 123
        finally:
            temp_path.unlink()
    
    def test_load_yml_file(self):
        """Test loading .yml file."""
        yaml_content = "test: data\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            parser = TestParser(str(temp_path))
            result = parser._load_file(temp_path)
            
            assert result["test"] == "data"
        finally:
            temp_path.unlink()
    
    def test_load_unsupported_format(self):
        """Test loading unsupported file format raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test data")
            temp_path = Path(f.name)
        
        try:
            parser = TestParser(str(temp_path))
            
            with pytest.raises(ParserError) as exc_info:
                parser._load_file(temp_path)
            
            assert "Unsupported file format" in str(exc_info.value)
            assert ".txt" in str(exc_info.value)
        finally:
            temp_path.unlink()
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json")
            temp_path = Path(f.name)
        
        try:
            parser = TestParser(str(temp_path))
            
            with pytest.raises(ParserError) as exc_info:
                parser._load_file(temp_path)
            
            assert "Failed to load specification file" in str(exc_info.value)
        finally:
            temp_path.unlink()


# ============================================================================
# Fetch URL Tests
# ============================================================================

class TestBaseParserFetchURL:
    """Test BaseParser _fetch_url method."""
    
    @pytest.mark.asyncio
    async def test_fetch_url_success(self):
        """Test successful URL fetch."""
        parser = TestParser("https://api.example.com/spec.yaml")
        
        mock_data = {"openapi": "3.0.0", "info": {"title": "Test API"}}
        
        with patch('core.base_provider.SimpleProvider') as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.fetch = AsyncMock(return_value=mock_data)
            mock_provider.__aenter__ = AsyncMock(return_value=mock_provider)
            mock_provider.__aexit__ = AsyncMock()
            mock_provider_class.return_value = mock_provider
            
            result = await parser._fetch_url("https://api.example.com/spec.yaml")
        
        assert result == mock_data
    
    @pytest.mark.asyncio
    async def test_fetch_url_failure(self):
        """Test URL fetch failure raises error."""
        parser = TestParser("https://api.example.com/spec.yaml")
        
        with patch('core.base_provider.SimpleProvider') as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.fetch = AsyncMock(side_effect=Exception("Connection failed"))
            mock_provider.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
            mock_provider.__aexit__ = AsyncMock()
            mock_provider_class.return_value = mock_provider
            
            with pytest.raises(ParserError) as exc_info:
                await parser._fetch_url("https://api.example.com/spec.yaml")
        
        assert "Failed to fetch specification from URL" in str(exc_info.value)


# ============================================================================
# Normalize Model Name Tests
# ============================================================================

class TestBaseParserNormalizeModelName:
    """Test BaseParser _normalize_model_name method."""
    
    def test_normalize_snake_case(self):
        """Test normalizing snake_case to PascalCase."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._normalize_model_name("user_profile")
        
        assert result == "UserProfile"
    
    def test_normalize_camel_case(self):
        """Test normalizing camelCase to PascalCase."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._normalize_model_name("userProfile")
        
        assert result == "UserProfile"
    
    def test_normalize_kebab_case(self):
        """Test normalizing kebab-case to PascalCase."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._normalize_model_name("user-profile")
        
        assert result == "UserProfile"
    
    def test_normalize_with_spaces(self):
        """Test normalizing name with spaces."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._normalize_model_name("user profile data")
        
        assert result == "UserProfileData"
    
    def test_normalize_with_special_chars(self):
        """Test normalizing name with special characters."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._normalize_model_name("user@profile#data")
        
        # Special chars are removed, leaving "userprofiledata" which becomes "Userprofiledata"
        assert result == "Userprofiledata"
    
    def test_normalize_already_pascal_case(self):
        """Test normalizing already PascalCase name."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._normalize_model_name("UserProfile")
        
        assert result == "UserProfile"
    
    def test_normalize_with_numbers(self):
        """Test normalizing name with numbers."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._normalize_model_name("user_profile_v2")
        
        assert result == "UserProfileV2"


# ============================================================================
# Normalize Field Name Tests
# ============================================================================

class TestBaseParserNormalizeFieldName:
    """Test BaseParser _normalize_field_name method."""
    
    def test_normalize_field_name_camel_case(self):
        """Test normalizing camelCase field name."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._normalize_field_name("userName")
        
        assert result == "user_name"
    
    def test_normalize_field_name_pascal_case(self):
        """Test normalizing PascalCase field name."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._normalize_field_name("UserName")
        
        assert result == "user_name"
    
    def test_normalize_field_name_already_snake_case(self):
        """Test normalizing already snake_case field name."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._normalize_field_name("user_name")
        
        assert result == "user_name"


# ============================================================================
# Generate Model Name Tests
# ============================================================================

class TestBaseParserGenerateModelName:
    """Test BaseParser _generate_model_name method."""
    
    def test_generate_model_name_simple_path(self):
        """Test generating model name from simple path."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._generate_model_name("/users")
        
        assert result == "UsersResponse"
    
    def test_generate_model_name_nested_path(self):
        """Test generating model name from nested path."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._generate_model_name("/users/posts")
        
        assert result == "UsersPostsResponse"
    
    def test_generate_model_name_with_parameters(self):
        """Test generating model name ignores path parameters."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._generate_model_name("/users/{id}/posts/{post_id}")
        
        assert result == "UsersPostsResponse"
    
    def test_generate_model_name_custom_suffix(self):
        """Test generating model name with custom suffix."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._generate_model_name("/users", suffix="Request")
        
        assert result == "UsersRequest"
    
    def test_generate_model_name_root_path(self):
        """Test generating model name from root path."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._generate_model_name("/")
        
        assert result == "DefaultResponse"
    
    def test_generate_model_name_empty_path(self):
        """Test generating model name from empty path."""
        parser = TestParser("/path/to/spec.yaml")
        
        result = parser._generate_model_name("")
        
        assert result == "DefaultResponse"


# ============================================================================
# Deduplicate Models Tests
# ============================================================================

class TestBaseParserDeduplicateModels:
    """Test BaseParser _deduplicate_models method."""
    
    def test_deduplicate_identical_models(self):
        """Test deduplicating identical models."""
        parser = TestParser("/path/to/spec.yaml")
        
        field1 = FieldSchema(name="id", type=FieldType.INTEGER, required=True)
        field2 = FieldSchema(name="name", type=FieldType.STRING, required=True)
        
        model1 = ModelSchema(name="User", fields=[field1, field2])
        model2 = ModelSchema(name="UserCopy", fields=[field1, field2])
        
        models = {"User": model1, "UserCopy": model2}
        
        result = parser._deduplicate_models(models)
        
        assert len(result) == 1
        assert "User" in result or "UserCopy" in result
    
    def test_deduplicate_different_models(self):
        """Test deduplicating keeps different models."""
        parser = TestParser("/path/to/spec.yaml")
        
        field1 = FieldSchema(name="id", type=FieldType.INTEGER, required=True)
        field2 = FieldSchema(name="name", type=FieldType.STRING, required=True)
        field3 = FieldSchema(name="email", type=FieldType.STRING, required=True)
        
        model1 = ModelSchema(name="User", fields=[field1, field2])
        model2 = ModelSchema(name="Profile", fields=[field1, field3])
        
        models = {"User": model1, "Profile": model2}
        
        result = parser._deduplicate_models(models)
        
        assert len(result) == 2
        assert "User" in result
        assert "Profile" in result
    
    def test_deduplicate_different_field_order(self):
        """Test deduplicating recognizes same fields in different order."""
        parser = TestParser("/path/to/spec.yaml")
        
        field1 = FieldSchema(name="id", type=FieldType.INTEGER, required=True)
        field2 = FieldSchema(name="name", type=FieldType.STRING, required=True)
        
        model1 = ModelSchema(name="User", fields=[field1, field2])
        model2 = ModelSchema(name="UserCopy", fields=[field2, field1])
        
        models = {"User": model1, "UserCopy": model2}
        
        result = parser._deduplicate_models(models)
        
        assert len(result) == 1
    
    def test_deduplicate_different_required_status(self):
        """Test deduplicating keeps models with different required status."""
        parser = TestParser("/path/to/spec.yaml")
        
        field1 = FieldSchema(name="id", type=FieldType.INTEGER, required=True)
        field2 = FieldSchema(name="name", type=FieldType.STRING, required=True)
        field3 = FieldSchema(name="name", type=FieldType.STRING, required=False)
        
        model1 = ModelSchema(name="User", fields=[field1, field2])
        model2 = ModelSchema(name="UserOptional", fields=[field1, field3])
        
        models = {"User": model1, "UserOptional": model2}
        
        result = parser._deduplicate_models(models)
        
        assert len(result) == 2


# ============================================================================
# Validate Parsed Schema Tests
# ============================================================================

class TestBaseParserValidateParsedSchema:
    """Test BaseParser _validate_parsed_schema method."""
    
    def test_validate_valid_schema(self):
        """Test validating a valid schema passes."""
        parser = TestParser("/path/to/spec.yaml")
        
        schema = APISchema(
            title="Test API",
            version="1.0.0",
            base_url="https://api.example.com",
            endpoints=[],
            models={}
        )
        
        # Should not raise
        parser._validate_parsed_schema(schema)
    
    def test_validate_invalid_schema_raises_error(self):
        """Test validating invalid schema raises error."""
        parser = TestParser("/path/to/spec.yaml")
        
        # Create schema with validation errors
        with patch.object(APISchema, 'validate_schema') as mock_validate:
            mock_validate.return_value = ["Error 1", "Error 2"]
            
            schema = APISchema(
                title="Test API",
                version="1.0.0",
                base_url="https://api.example.com",
                endpoints=[],
                models={}
            )
            
            with pytest.raises(ParserError) as exc_info:
                parser._validate_parsed_schema(schema)
            
            assert "Parsed schema has validation errors" in str(exc_info.value)
            assert "errors" in exc_info.value.details


# ============================================================================
# Integration Tests
# ============================================================================

class TestBaseParserIntegration:
    """Integration tests for BaseParser."""
    
    @pytest.mark.asyncio
    async def test_full_parse_flow_with_file(self):
        """Test complete parsing flow with file."""
        test_data = {"test": "data"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            parser = TestParser(temp_path)
            
            # Validate source
            assert parser.validate_source() is True
            
            # Load file
            loaded_data = parser._load_file(Path(temp_path))
            assert loaded_data == test_data
            
            # Parse
            result = await parser.parse()
            assert isinstance(result, APISchema)
        finally:
            Path(temp_path).unlink()
    
    def test_model_name_normalization_pipeline(self):
        """Test complete model name normalization pipeline."""
        parser = TestParser("/path/to/spec.yaml")
        
        # Test various input formats
        test_cases = [
            ("user_profile", "UserProfile"),
            ("userProfile", "UserProfile"),
            ("user-profile", "UserProfile"),
            ("user profile", "UserProfile"),
            ("UserProfile", "UserProfile"),
        ]
        
        for input_name, expected in test_cases:
            result = parser._normalize_model_name(input_name)
            assert result == expected, f"Failed for {input_name}"


# Made with Bob