"""
Tests for Dockerfile generator.
"""

from pathlib import Path

import pytest

from generators.dockerfile_generator import DockerfileGenerator
from schemas.api_schema import APISchema, ModelSchema
from schemas.field_schema import FieldSchema, FieldType


@pytest.fixture
def sample_api_schema():
    """Create a sample API schema for testing."""
    user_model = ModelSchema(
        name="User",
        fields=[
            FieldSchema(name="id", type=FieldType.INTEGER, required=True),
        ],
    )
    
    return APISchema(
        title="Test API",
        version="1.0.0",
        base_url="https://api.example.com",
        endpoints=[],
        models={"User": user_model},
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


def test_dockerfile_generator_basic(sample_api_schema, temp_output_dir):
    """Test basic Dockerfile generation."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    files = generator.generate()
    
    assert "dockerfile" in files
    assert "dockerignore" in files
    assert files["dockerfile"].exists()
    assert files["dockerignore"].exists()


def test_dockerfile_generator_dockerfile_content(sample_api_schema, temp_output_dir):
    """Test Dockerfile content."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    dockerfile = generator.generate_dockerfile()
    
    content = dockerfile.read_text(encoding="utf-8")
    
    # Check for multi-stage build
    assert "FROM python:3.11-slim as builder" in content
    assert "FROM python:3.11-slim" in content
    
    # Check for labels
    assert "LABEL maintainer=" in content
    assert "LABEL version=" in content
    
    # Check for non-root user
    assert "RUN groupadd -r appuser" in content
    assert "USER appuser" in content
    
    # Check for health check
    assert "HEALTHCHECK" in content
    
    # Check for exposed port
    assert "EXPOSE" in content
    
    # Check for CMD
    assert "CMD" in content
    assert "uvicorn" in content


def test_dockerfile_generator_dockerignore_content(sample_api_schema, temp_output_dir):
    """Test .dockerignore content."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    dockerignore = generator.generate_dockerignore()
    
    content = dockerignore.read_text(encoding="utf-8")
    
    # Check for common ignores
    assert "__pycache__/" in content
    assert "*.py[cod]" in content  # Covers .pyc, .pyo, .pyd
    assert ".git/" in content
    assert "tests/" in content
    assert ".pytest_cache/" in content


def test_dockerfile_generator_multi_stage(sample_api_schema, temp_output_dir):
    """Test multi-stage build configuration."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    dockerfile = generator.generate_dockerfile()
    
    content = dockerfile.read_text(encoding="utf-8")
    
    # Check for builder stage
    assert "as builder" in content
    
    # Check for copying from builder
    assert "COPY --from=builder" in content


def test_dockerfile_generator_security(sample_api_schema, temp_output_dir):
    """Test security features."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    dockerfile = generator.generate_dockerfile()
    
    content = dockerfile.read_text(encoding="utf-8")
    
    # Check for non-root user
    assert "appuser" in content
    assert "USER appuser" in content
    
    # Check for ownership
    assert "chown" in content


def test_dockerfile_generator_environment_variables(sample_api_schema, temp_output_dir):
    """Test environment variables."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    dockerfile = generator.generate_dockerfile()
    
    content = dockerfile.read_text(encoding="utf-8")
    
    # Check for environment variables
    assert "ENV PYTHONUNBUFFERED=1" in content
    assert "ENV" in content


def test_dockerfile_generator_statistics(sample_api_schema, temp_output_dir):
    """Test generation statistics."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    
    stats = generator.get_generation_stats()
    
    assert stats["api_title"] == "Test API"
    assert stats["api_version"] == "1.0.0"
    assert stats["base_image"] == "python:3.11-slim"
    assert stats["multi_stage"] is True
    assert stats["non_root_user"] is True
    assert stats["health_check"] is True
    assert "Dockerfile" in stats["files_generated"]
    assert ".dockerignore" in stats["files_generated"]


def test_dockerfile_generator_docker_commands(sample_api_schema, temp_output_dir):
    """Test Docker commands generation."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    
    commands = generator.get_docker_commands()
    
    assert "build" in commands
    assert "run" in commands
    assert "run_detached" in commands
    assert "stop" in commands
    assert "logs" in commands
    assert "exec" in commands
    
    # Check command format
    assert "docker build" in commands["build"]
    assert "docker run" in commands["run"]
    assert "-p 8000:8000" in commands["run"]


def test_dockerfile_generator_deployment_info(sample_api_schema, temp_output_dir):
    """Test deployment information."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    
    info = generator.get_deployment_info()
    
    assert info["port"] == 8000
    assert info["health_check_endpoint"] == "/health"
    assert "environment_variables" in info
    assert "PORT" in info["environment_variables"]
    assert "resource_limits" in info


def test_dockerfile_generator_workdir(sample_api_schema, temp_output_dir):
    """Test working directory configuration."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    dockerfile = generator.generate_dockerfile()
    
    content = dockerfile.read_text(encoding="utf-8")
    
    # Check for WORKDIR
    assert "WORKDIR /app" in content


def test_dockerfile_generator_copy_files(sample_api_schema, temp_output_dir):
    """Test file copying."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    dockerfile = generator.generate_dockerfile()
    
    content = dockerfile.read_text(encoding="utf-8")
    
    # Check for copying application files
    assert "COPY models.py" in content
    assert "COPY validators.py" in content
    assert "COPY app.py" in content
    assert "COPY core/" in content


def test_dockerfile_generator_pip_install(sample_api_schema, temp_output_dir):
    """Test pip installation."""
    generator = DockerfileGenerator(sample_api_schema, temp_output_dir)
    dockerfile = generator.generate_dockerfile()
    
    content = dockerfile.read_text(encoding="utf-8")
    
    # Check for pip install
    assert "pip install" in content
    assert "requirements.txt" in content
    assert "--no-cache-dir" in content

# Made with Bob
