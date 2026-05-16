"""
Unit tests for core/utils.py

Tests utility functions for file I/O, hashing, and string manipulation.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from core.utils import (
    calculate_schema_hash,
    deep_merge,
    extract_base_url,
    format_bytes,
    is_url,
    load_json_file,
    load_yaml_file,
    normalize_field_name,
    sanitize_filename,
    truncate_string,
    write_json_file,
    write_yaml_file,
)


class TestFileOperations:
    """Test file I/O operations."""
    
    def test_load_json_file(self, tmp_path):
        """Test loading JSON file."""
        json_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        loaded_data = load_json_file(json_file)
        assert loaded_data == test_data
    
    def test_load_json_file_not_found(self, tmp_path):
        """Test loading non-existent JSON file."""
        with pytest.raises(FileNotFoundError):
            load_json_file(tmp_path / "nonexistent.json")
    
    def test_load_json_file_invalid(self, tmp_path):
        """Test loading invalid JSON file."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json {")
        
        with pytest.raises(json.JSONDecodeError):
            load_json_file(json_file)
    
    def test_load_yaml_file(self, tmp_path):
        """Test loading YAML file."""
        yaml_file = tmp_path / "test.yaml"
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        
        with open(yaml_file, 'w') as f:
            yaml.dump(test_data, f)
        
        loaded_data = load_yaml_file(yaml_file)
        assert loaded_data == test_data
    
    def test_load_yaml_file_not_found(self, tmp_path):
        """Test loading non-existent YAML file."""
        with pytest.raises(FileNotFoundError):
            load_yaml_file(tmp_path / "nonexistent.yaml")
    
    def test_write_json_file(self, tmp_path):
        """Test writing JSON file."""
        json_file = tmp_path / "output.json"
        test_data = {"key": "value", "number": 42}
        
        write_json_file(json_file, test_data)
        
        assert json_file.exists()
        with open(json_file, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data
    
    def test_write_json_file_creates_directory(self, tmp_path):
        """Test that write_json_file creates parent directories."""
        json_file = tmp_path / "subdir" / "nested" / "output.json"
        test_data = {"key": "value"}
        
        write_json_file(json_file, test_data)
        
        assert json_file.exists()
        assert json_file.parent.exists()
    
    def test_write_json_file_with_indent(self, tmp_path):
        """Test writing JSON file with custom indentation."""
        json_file = tmp_path / "output.json"
        test_data = {"key": "value"}
        
        write_json_file(json_file, test_data, indent=4)
        
        content = json_file.read_text()
        assert "    " in content  # 4-space indentation
    
    def test_write_yaml_file(self, tmp_path):
        """Test writing YAML file."""
        yaml_file = tmp_path / "output.yaml"
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        
        write_yaml_file(yaml_file, test_data)
        
        assert yaml_file.exists()
        with open(yaml_file, 'r') as f:
            loaded_data = yaml.safe_load(f)
        assert loaded_data == test_data
    
    def test_write_yaml_file_creates_directory(self, tmp_path):
        """Test that write_yaml_file creates parent directories."""
        yaml_file = tmp_path / "subdir" / "output.yaml"
        test_data = {"key": "value"}
        
        write_yaml_file(yaml_file, test_data)
        
        assert yaml_file.exists()
        assert yaml_file.parent.exists()


class TestSchemaHashing:
    """Test schema hashing for drift detection."""
    
    def test_calculate_schema_hash(self):
        """Test schema hash calculation."""
        schema = {"key": "value", "number": 42}
        hash_value = calculate_schema_hash(schema)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64 hex characters
    
    def test_calculate_schema_hash_consistency(self):
        """Test that same schema produces same hash."""
        schema = {"key": "value", "number": 42}
        hash1 = calculate_schema_hash(schema)
        hash2 = calculate_schema_hash(schema)
        
        assert hash1 == hash2
    
    def test_calculate_schema_hash_key_order_independent(self):
        """Test that key order doesn't affect hash."""
        schema1 = {"a": 1, "b": 2, "c": 3}
        schema2 = {"c": 3, "a": 1, "b": 2}
        
        hash1 = calculate_schema_hash(schema1)
        hash2 = calculate_schema_hash(schema2)
        
        assert hash1 == hash2
    
    def test_calculate_schema_hash_different_values(self):
        """Test that different schemas produce different hashes."""
        schema1 = {"key": "value1"}
        schema2 = {"key": "value2"}
        
        hash1 = calculate_schema_hash(schema1)
        hash2 = calculate_schema_hash(schema2)
        
        assert hash1 != hash2
    
    def test_calculate_schema_hash_nested(self):
        """Test hashing nested schemas."""
        schema = {
            "user": {
                "name": "John",
                "age": 30,
                "address": {
                    "city": "NYC",
                    "zip": "10001"
                }
            }
        }
        hash_value = calculate_schema_hash(schema)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64


class TestFieldNameNormalization:
    """Test field name normalization."""
    
    def test_normalize_camel_case(self):
        """Test normalizing camelCase."""
        assert normalize_field_name("userId") == "user_id"
        assert normalize_field_name("userName") == "user_name"
        assert normalize_field_name("isActive") == "is_active"
    
    def test_normalize_pascal_case(self):
        """Test normalizing PascalCase."""
        assert normalize_field_name("UserID") == "user_id"
        assert normalize_field_name("UserName") == "user_name"
        assert normalize_field_name("IsActive") == "is_active"
    
    def test_normalize_hyphenated(self):
        """Test normalizing hyphenated names."""
        assert normalize_field_name("user-id") == "user_id"
        assert normalize_field_name("user-name") == "user_name"
    
    def test_normalize_dotted(self):
        """Test normalizing dotted names."""
        assert normalize_field_name("user.id") == "user_id"
        assert normalize_field_name("user.name") == "user_name"
    
    def test_normalize_spaces(self):
        """Test normalizing names with spaces."""
        assert normalize_field_name("user id") == "user_id"
        assert normalize_field_name("user name") == "user_name"
    
    def test_normalize_multiple_underscores(self):
        """Test removing multiple consecutive underscores."""
        assert normalize_field_name("user__id") == "user_id"
        assert normalize_field_name("user___name") == "user_name"
    
    def test_normalize_leading_trailing_underscores(self):
        """Test removing leading/trailing underscores."""
        assert normalize_field_name("_user_id_") == "user_id"
        assert normalize_field_name("__user_name__") == "user_name"
    
    def test_normalize_already_normalized(self):
        """Test that already normalized names remain unchanged."""
        assert normalize_field_name("user_id") == "user_id"
        assert normalize_field_name("user_name") == "user_name"
    
    def test_normalize_mixed_formats(self):
        """Test normalizing mixed format names."""
        assert normalize_field_name("user-ID.Name") == "user_id_name"
        assert normalize_field_name("User Name-ID") == "user_name_id"


class TestURLValidation:
    """Test URL validation."""
    
    def test_is_url_http(self):
        """Test HTTP URLs."""
        assert is_url("http://example.com")
        assert is_url("http://api.example.com/v1")
        assert is_url("http://example.com:8080")
    
    def test_is_url_https(self):
        """Test HTTPS URLs."""
        assert is_url("https://example.com")
        assert is_url("https://api.example.com/v1/users")
        assert is_url("https://example.com:443/path")
    
    def test_is_url_localhost(self):
        """Test localhost URLs."""
        assert is_url("http://localhost")
        assert is_url("http://localhost:8000")
        assert is_url("https://localhost:3000/api")
    
    def test_is_url_ip_address(self):
        """Test IP address URLs."""
        assert is_url("http://127.0.0.1")
        assert is_url("http://192.168.1.1:8080")
        assert is_url("https://10.0.0.1/api")
    
    def test_is_url_not_url(self):
        """Test non-URL strings."""
        assert not is_url("example.com")
        assert not is_url("file.json")
        assert not is_url("/path/to/file")
        assert not is_url("not a url")
        assert not is_url("")


class TestFilenameSanitization:
    """Test filename sanitization."""
    
    def test_sanitize_filename_invalid_chars(self):
        """Test removing invalid characters."""
        assert sanitize_filename("file<name>.txt") == "file_name_.txt"
        assert sanitize_filename("file:name.txt") == "file_name.txt"
        assert sanitize_filename('file"name.txt') == "file_name.txt"
        assert sanitize_filename("file/name.txt") == "file_name.txt"
        assert sanitize_filename("file\\name.txt") == "file_name.txt"
        assert sanitize_filename("file|name.txt") == "file_name.txt"
        assert sanitize_filename("file?name.txt") == "file_name.txt"
        assert sanitize_filename("file*name.txt") == "file_name.txt"
    
    def test_sanitize_filename_leading_trailing(self):
        """Test removing leading/trailing spaces and dots."""
        assert sanitize_filename("  filename.txt  ") == "filename.txt"
        assert sanitize_filename("..filename.txt..") == "filename.txt"
        assert sanitize_filename(" . filename.txt . ") == "filename.txt"
    
    def test_sanitize_filename_length_limit(self):
        """Test filename length limiting."""
        long_name = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) == 255
    
    def test_sanitize_filename_valid(self):
        """Test that valid filenames remain unchanged."""
        assert sanitize_filename("valid_filename.txt") == "valid_filename.txt"
        assert sanitize_filename("file-name_123.json") == "file-name_123.json"


class TestDeepMerge:
    """Test deep dictionary merging."""
    
    def test_deep_merge_simple(self):
        """Test merging simple dictionaries."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}
        result = deep_merge(dict1, dict2)
        
        assert result == {"a": 1, "b": 2, "c": 3, "d": 4}
    
    def test_deep_merge_override(self):
        """Test that dict2 values override dict1."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        result = deep_merge(dict1, dict2)
        
        assert result == {"a": 1, "b": 3, "c": 4}
    
    def test_deep_merge_nested(self):
        """Test merging nested dictionaries."""
        dict1 = {"a": {"x": 1, "y": 2}, "b": 3}
        dict2 = {"a": {"y": 3, "z": 4}, "c": 5}
        result = deep_merge(dict1, dict2)
        
        assert result == {"a": {"x": 1, "y": 3, "z": 4}, "b": 3, "c": 5}
    
    def test_deep_merge_deeply_nested(self):
        """Test merging deeply nested dictionaries."""
        dict1 = {"a": {"b": {"c": 1, "d": 2}}}
        dict2 = {"a": {"b": {"d": 3, "e": 4}}}
        result = deep_merge(dict1, dict2)
        
        assert result == {"a": {"b": {"c": 1, "d": 3, "e": 4}}}
    
    def test_deep_merge_non_dict_override(self):
        """Test that non-dict values override nested dicts."""
        dict1 = {"a": {"x": 1, "y": 2}}
        dict2 = {"a": "string"}
        result = deep_merge(dict1, dict2)
        
        assert result == {"a": "string"}
    
    def test_deep_merge_preserves_original(self):
        """Test that original dictionaries are not modified."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3}
        result = deep_merge(dict1, dict2)
        
        assert dict1 == {"a": 1, "b": 2}  # Unchanged
        assert dict2 == {"c": 3}  # Unchanged
        assert result == {"a": 1, "b": 2, "c": 3}


class TestStringTruncation:
    """Test string truncation."""
    
    def test_truncate_string_no_truncation(self):
        """Test that short strings are not truncated."""
        text = "Short text"
        assert truncate_string(text, 100) == "Short text"
    
    def test_truncate_string_exact_length(self):
        """Test string at exact max length."""
        text = "a" * 100
        assert truncate_string(text, 100) == text
    
    def test_truncate_string_with_default_suffix(self):
        """Test truncation with default suffix."""
        text = "a" * 150
        result = truncate_string(text, 100)
        
        assert len(result) == 100
        assert result.endswith("...")
        assert result == "a" * 97 + "..."
    
    def test_truncate_string_with_custom_suffix(self):
        """Test truncation with custom suffix."""
        text = "a" * 150
        result = truncate_string(text, 100, suffix=" [more]")
        
        assert len(result) == 100
        assert result.endswith(" [more]")
    
    def test_truncate_string_empty_suffix(self):
        """Test truncation with empty suffix."""
        text = "a" * 150
        result = truncate_string(text, 100, suffix="")
        
        assert len(result) == 100
        assert result == "a" * 100


class TestBytesFormatting:
    """Test bytes formatting."""
    
    def test_format_bytes_bytes(self):
        """Test formatting bytes."""
        assert format_bytes(0) == "0.0 B"
        assert format_bytes(100) == "100.0 B"
        assert format_bytes(1023) == "1023.0 B"
    
    def test_format_bytes_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1536) == "1.5 KB"
        assert format_bytes(10240) == "10.0 KB"
    
    def test_format_bytes_megabytes(self):
        """Test formatting megabytes."""
        assert format_bytes(1024 * 1024) == "1.0 MB"
        assert format_bytes(1024 * 1024 * 5) == "5.0 MB"
    
    def test_format_bytes_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_bytes(1024 * 1024 * 1024) == "1.0 GB"
        assert format_bytes(1024 * 1024 * 1024 * 2) == "2.0 GB"
    
    def test_format_bytes_terabytes(self):
        """Test formatting terabytes."""
        assert format_bytes(1024 * 1024 * 1024 * 1024) == "1.0 TB"
    
    def test_format_bytes_petabytes(self):
        """Test formatting petabytes."""
        assert format_bytes(1024 * 1024 * 1024 * 1024 * 1024) == "1.0 PB"


class TestURLExtraction:
    """Test base URL extraction."""
    
    def test_extract_base_url_simple(self):
        """Test extracting base URL from simple URLs."""
        assert extract_base_url("https://api.example.com/v1/users") == "https://api.example.com"
        assert extract_base_url("http://example.com/path") == "http://example.com"
    
    def test_extract_base_url_with_port(self):
        """Test extracting base URL with port."""
        assert extract_base_url("http://localhost:8000/api") == "http://localhost:8000"
        assert extract_base_url("https://api.example.com:443/v1") == "https://api.example.com:443"
    
    def test_extract_base_url_with_query(self):
        """Test extracting base URL with query parameters."""
        assert extract_base_url("https://api.example.com/search?q=test") == "https://api.example.com"
    
    def test_extract_base_url_with_fragment(self):
        """Test extracting base URL with fragment."""
        assert extract_base_url("https://example.com/page#section") == "https://example.com"
    
    def test_extract_base_url_ip_address(self):
        """Test extracting base URL from IP addresses."""
        assert extract_base_url("http://192.168.1.1:8080/api") == "http://192.168.1.1:8080"
        assert extract_base_url("https://127.0.0.1/path") == "https://127.0.0.1"

# Made with Bob
