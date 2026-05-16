"""
Dockerfile generator for DataSentinel.

Generates Dockerfile and .dockerignore for containerized deployment.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from schemas.api_schema import APISchema


class DockerfileGenerator:
    """
    Generates Dockerfile and .dockerignore from APISchema.
    
    Creates:
    - Multi-stage Dockerfile with builder and runtime stages
    - .dockerignore file to optimize build context
    - Non-root user for security
    - Health check configuration
    - Environment variable configuration
    """
    
    def __init__(
        self,
        api_schema: APISchema,
        output_dir: Path,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize the Dockerfile generator.
        
        Args:
            api_schema: Normalized API schema
            output_dir: Directory to write Dockerfile
            template_dir: Directory containing Jinja2 templates
        """
        self.api_schema = api_schema
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 environment
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"
        
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        logger.info(f"Initialized DockerfileGenerator for {api_schema.title}")
    
    def _prepare_template_context(self) -> Dict[str, Any]:
        """
        Prepare context data for Jinja2 template.
        
        Returns:
            Template context dictionary
        """
        return {
            "api_schema": self.api_schema,
            "generation_timestamp": datetime.utcnow().isoformat() + "Z",
        }
    
    def generate_dockerfile(self) -> Path:
        """
        Generate Dockerfile.
        
        Returns:
            Path to generated Dockerfile
        
        Raises:
            Exception: If generation fails
        """
        logger.info("Generating Dockerfile...")
        
        try:
            # Load template
            template = self.env.get_template("Dockerfile.jinja2")
            
            # Prepare context
            context = self._prepare_template_context()
            
            # Render template
            content = template.render(**context)
            
            # Write to file
            output_file = self.output_dir / "Dockerfile"
            output_file.write_text(content, encoding="utf-8")
            
            logger.success(f"Generated Dockerfile at {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate Dockerfile: {e}")
            raise
    
    def generate_dockerignore(self) -> Path:
        """
        Generate .dockerignore file.
        
        Returns:
            Path to generated .dockerignore
        
        Raises:
            Exception: If generation fails
        """
        logger.info("Generating .dockerignore...")
        
        try:
            # Load template
            template = self.env.get_template(".dockerignore.jinja2")
            
            # Prepare context
            context = self._prepare_template_context()
            
            # Render template
            content = template.render(**context)
            
            # Write to file
            output_file = self.output_dir / ".dockerignore"
            output_file.write_text(content, encoding="utf-8")
            
            logger.success(f"Generated .dockerignore at {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate .dockerignore: {e}")
            raise
    
    def generate(self) -> Dict[str, Path]:
        """
        Generate both Dockerfile and .dockerignore.
        
        Returns:
            Dictionary with paths to generated files
        
        Raises:
            Exception: If generation fails
        """
        dockerfile = self.generate_dockerfile()
        dockerignore = self.generate_dockerignore()
        
        return {
            "dockerfile": dockerfile,
            "dockerignore": dockerignore,
        }
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about what will be generated.
        
        Returns:
            Dictionary with generation statistics
        """
        return {
            "api_title": self.api_schema.title,
            "api_version": self.api_schema.version,
            "base_image": "python:3.11-slim",
            "multi_stage": True,
            "non_root_user": True,
            "health_check": True,
            "files_generated": ["Dockerfile", ".dockerignore"],
        }
    
    def get_docker_commands(self) -> Dict[str, str]:
        """
        Get Docker commands for building and running.
        
        Returns:
            Dictionary with Docker commands
        """
        image_name = self.api_schema.title.lower().replace(" ", "-")
        
        return {
            "build": f"docker build -t {image_name}:{self.api_schema.version} .",
            "run": f"docker run -p 8000:8000 {image_name}:{self.api_schema.version}",
            "run_detached": f"docker run -d -p 8000:8000 --name {image_name} {image_name}:{self.api_schema.version}",
            "stop": f"docker stop {image_name}",
            "logs": f"docker logs {image_name}",
            "exec": f"docker exec -it {image_name} /bin/bash",
        }
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """
        Get deployment information.
        
        Returns:
            Dictionary with deployment info
        """
        return {
            "port": 8000,
            "health_check_endpoint": "/health",
            "environment_variables": {
                "PORT": "Application port (default: 8000)",
                "HOST": "Application host (default: 0.0.0.0)",
                "LOG_LEVEL": "Logging level (default: info)",
            },
            "volumes": {
                "/app/logs": "Application logs directory",
            },
            "resource_limits": {
                "memory": "512MB recommended",
                "cpu": "0.5 CPU recommended",
            },
        }


def generate_dockerfile(
    api_schema: APISchema,
    output_dir: Path,
    template_dir: Optional[Path] = None,
) -> Dict[str, Path]:
    """
    Convenience function to generate Dockerfile and .dockerignore.
    
    Args:
        api_schema: Normalized API schema
        output_dir: Directory to write files
        template_dir: Directory containing Jinja2 templates
    
    Returns:
        Dictionary with paths to generated files
    """
    generator = DockerfileGenerator(api_schema, output_dir, template_dir)
    return generator.generate()

# Made with Bob
