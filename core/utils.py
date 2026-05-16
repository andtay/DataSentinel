"""
Shared utility functions for DataSentinel.

This module provides common helper functions used throughout the framework.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml


def load_json_file(path: Path) -> dict:
    """
    Load and parse JSON file.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_yaml_file(path: Path) -> dict:
    """
    Load and parse YAML file.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Parsed YAML data as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If file is not valid YAML
    """
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def write_json_file(path: Path, data: dict, indent: int = 2) -> None:
    """
    Write data to JSON file.
    
    Args:
        path: Path to output file
        data: Data to write
        indent: Indentation level for pretty printing
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def write_yaml_file(path: Path, data: dict) -> None:
    """
    Write data to YAML file.
    
    Args:
        path: Path to output file
        data: Data to write
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def calculate_schema_hash(schema: dict) -> str:
    """
    Calculate SHA256 hash of schema for drift detection.
    
    The schema is serialized to JSON with sorted keys to ensure
    consistent hashing regardless of key order.
    
    Args:
        schema: Schema dictionary to hash
        
    Returns:
        Hexadecimal hash string
    """
    schema_json = json.dumps(schema, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(schema_json.encode('utf-8')).hexdigest()


def normalize_field_name(name: str) -> str:
    """
    Convert field name to snake_case.
    
    Examples:
        - "userId" -> "user_id"
        - "UserID" -> "user_id"
        - "user-name" -> "user_name"
        - "user.name" -> "user_name"
        - "user name" -> "user_name"
    
    Args:
        name: Field name to normalize
        
    Returns:
        Normalized field name in snake_case
    """
    # Replace hyphens, dots, and spaces with underscores
    name = name.replace('-', '_').replace('.', '_').replace(' ', '_')
    
    # Insert underscore before uppercase letters
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove multiple consecutive underscores
    name = re.sub('_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    return name


def is_url(source: str) -> bool:
    """
    Check if source is a URL.
    
    Args:
        source: String to check
        
    Returns:
        True if source is a URL, False otherwise
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return bool(url_pattern.match(source))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def deep_merge(dict1: dict, dict2: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Values from dict2 override values from dict1.
    Nested dictionaries are merged recursively.
    
    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes as human-readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    size = float(bytes_value)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def extract_base_url(url: str) -> str:
    """
    Extract base URL from full URL.
    
    Examples:
        - "https://api.example.com/v1/users" -> "https://api.example.com"
        - "http://localhost:8000/api" -> "http://localhost:8000"
    
    Args:
        url: Full URL
        
    Returns:
        Base URL (scheme + netloc)
    """
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

# Made with Bob
