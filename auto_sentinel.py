#!/usr/bin/env python3
"""
DataSentinel - Automated API Validation & Documentation Generator

Main CLI entry point for the DataSentinel framework.
Orchestrates the complete pipeline from API specification to generated code.

Usage:
    python auto_sentinel.py --api <URL|FILE|ENDPOINT> [OPTIONS]

Examples:
    # JSON endpoint
    python auto_sentinel.py --api https://api.example.com/users

    # OpenAPI file
    python auto_sentinel.py --api ./specs/openapi.yaml --output ./generated

    # GraphQL endpoint
    python auto_sentinel.py --api https://api.example.com/graphql --format graphql

    # With authentication
    python auto_sentinel.py --api https://api.example.com/users \
        --auth-type bearer --auth-token $TOKEN
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from loguru import logger

from config.settings import Settings
from config.logging_config import setup_logging
from core.auth_manager import AuthHandler, APIKeyAuth, BearerAuth
from core.exceptions import (
    DataSentinelError,
    ConfigurationError,
    ParsingError,
    GenerationError,
)
from schemas.api_schema import APISchema
from schemas.config_schema import AuthConfig, AuthType
from parsers.json_inference_parser import JSONInferenceParser
from parsers.openapi_parser import OpenAPIParser
from parsers.graphql_parser import GraphQLParser
from parsers.base_parser import BaseParser
from generators.models_generator import ModelsGenerator
from generators.validators_generator import ValidatorsGenerator
from generators.tests_generator import TestsGenerator
from generators.app_generator import AppGenerator
from generators.docs_generator import DocsGenerator
from generators.dockerfile_generator import DockerfileGenerator


class GenerationResult:
    """Result of the generation pipeline."""

    def __init__(self):
        self.success: bool = False
        self.api_schema: Optional[APISchema] = None
        self.generated_files: Dict[str, Path] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration_seconds: float = 0.0

    def mark_complete(self):
        """Mark the generation as complete and calculate duration."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.success = len(self.errors) == 0

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        logger.error(error)

    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
        logger.warning(warning)

    def add_generated_file(self, name: str, path: Path):
        """Add a generated file to the result."""
        self.generated_files[name] = path
        logger.info(f"Generated {name}: {path}")


class AutoSentinel:
    """
    Main orchestrator for the DataSentinel generation pipeline.

    Coordinates the flow from API specification input through parsing,
    normalization, and code generation.
    """

    def __init__(self, args: argparse.Namespace):
        """
        Initialize the orchestrator.

        Args:
            args: Parsed command-line arguments
        """
        self.args = args
        self.settings = Settings()
        self.result = GenerationResult()

        # Setup logging
        setup_logging(
            level="DEBUG" if args.verbose else "INFO",
            log_file=args.log_file if hasattr(args, "log_file") else None,
        )

        logger.info("=" * 70)
        logger.info("DataSentinel - Automated API Validation Generator")
        logger.info("=" * 70)
        logger.info(f"API Source: {args.api}")
        logger.info(f"Output Directory: {args.output}")
        logger.info(f"Format: {args.format or 'auto-detect'}")

    async def run(self) -> GenerationResult:
        """
        Execute the complete generation pipeline.

        Returns:
            GenerationResult with success status and generated files
        """
        try:
            # Step 1: Validate configuration
            logger.info("\n[Step 1/5] Validating configuration...")
            self._validate_configuration()

            # Step 2: Detect input format
            logger.info("\n[Step 2/5] Detecting input format...")
            format_type = self._detect_format()
            logger.info(f"Detected format: {format_type}")

            # Step 3: Parse API specification
            logger.info("\n[Step 3/5] Parsing API specification...")
            parser = self._get_parser(format_type)
            api_schema = await parser.parse()
            self.result.api_schema = api_schema
            logger.success(
                f"Parsed API: {api_schema.title} v{api_schema.version} "
                f"({len(api_schema.endpoints)} endpoints, {len(api_schema.models)} models)"
            )

            # Step 4: Generate code
            if not self.args.dry_run:
                logger.info("\n[Step 4/5] Generating code...")
                await self._run_generators(api_schema)
            else:
                logger.info("\n[Step 4/5] Skipping code generation (dry-run mode)")
                self._show_dry_run_preview(api_schema)

            # Step 5: Report results
            logger.info("\n[Step 5/5] Finalizing...")
            self.result.mark_complete()
            self._report_results()

            return self.result

        except DataSentinelError as e:
            self.result.add_error(f"DataSentinel error: {e}")
            self.result.mark_complete()
            return self.result
        except Exception as e:
            self.result.add_error(f"Unexpected error: {e}")
            logger.exception("Unexpected error occurred")
            self.result.mark_complete()
            return self.result

    def _validate_configuration(self):
        """Validate the configuration and arguments."""
        # Validate API source
        if not self.args.api:
            raise ConfigurationError("API source is required (--api)")

        # Validate output directory
        output_dir = Path(self.args.output)
        if output_dir.exists() and not output_dir.is_dir():
            raise ConfigurationError(f"Output path exists but is not a directory: {output_dir}")

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Output directory: {output_dir.absolute()}")

        # Validate authentication configuration
        if self.args.auth_type and self.args.auth_type != "none":
            if not self.args.auth_token and self.args.auth_type != "basic":
                raise ConfigurationError(
                    f"Authentication token required for auth type: {self.args.auth_type}"
                )

    def _detect_format(self) -> str:
        """
        Auto-detect the input format based on the API source.

        Returns:
            Format type: 'json', 'openapi', or 'graphql'
        """
        if self.args.format:
            return self.args.format.lower()

        api_source = str(self.args.api).lower()

        # Check file extensions
        if api_source.endswith((".yaml", ".yml")):
            return "openapi"
        elif api_source.endswith(".json"):
            # Could be OpenAPI or raw JSON - check content later
            return "openapi"  # Try OpenAPI first

        # Check URL patterns
        if "graphql" in api_source:
            return "graphql"
        elif "swagger" in api_source or "openapi" in api_source:
            return "openapi"

        # Default to JSON inference
        return "json"

    def _get_parser(self, format_type: str) -> BaseParser:
        """
        Get the appropriate parser for the format type.

        Args:
            format_type: Format type ('json', 'openapi', 'graphql')

        Returns:
            Parser instance

        Raises:
            ConfigurationError: If format type is unknown
        """
        parsers = {
            "json": JSONInferenceParser,
            "openapi": OpenAPIParser,
            "graphql": GraphQLParser,
        }

        parser_class = parsers.get(format_type)
        if not parser_class:
            raise ConfigurationError(f"Unknown format type: {format_type}")

        return parser_class(self.args.api, auth_handler=self._build_auth_handler())

    def _build_auth_handler(self) -> AuthHandler | None:
        """
        Construct an AuthHandler from the CLI auth flags.

        Returns:
            AuthHandler for bearer/api-key, or None when no auth is requested
            (the provider then falls back to NoAuth).

        Raises:
            ConfigurationError: For auth types whose wiring isn't implemented
                yet (oauth2, basic) — those need extra CLI args this command
                does not expose.
        """
        auth_type = (self.args.auth_type or "none").lower()

        if auth_type == "none":
            return None

        if auth_type == "bearer":
            return BearerAuth(token=self.args.auth_token)

        if auth_type == "api-key":
            header_name = self.args.auth_header or "X-API-Key"
            return APIKeyAuth(api_key=self.args.auth_token, header_name=header_name)

        raise ConfigurationError(
            f"Auth type '{auth_type}' is not wired to the parser yet. "
            f"Supported: none, bearer, api-key."
        )

    async def _run_generators(self, api_schema: APISchema):
        """
        Run all code generators.

        Args:
            api_schema: Parsed and normalized API schema
        """
        output_dir = Path(self.args.output)

        # Define generators to run
        generators = []

        if not self.args.skip_models:
            generators.append(("Models", ModelsGenerator(api_schema, output_dir)))

        if not self.args.skip_validators:
            generators.append(("Validators", ValidatorsGenerator(api_schema, output_dir)))

        if not self.args.skip_tests:
            generators.append(("Tests", TestsGenerator(api_schema, output_dir)))

        if not self.args.skip_app:
            generators.append(("FastAPI App", AppGenerator(api_schema, output_dir)))

        if not self.args.skip_docs:
            generators.append(("Documentation", DocsGenerator(api_schema, output_dir)))

        if not self.args.skip_docker:
            generators.append(("Docker", DockerfileGenerator(api_schema, output_dir)))

        # Run generators
        total = len(generators)
        for idx, (name, generator) in enumerate(generators, 1):
            try:
                logger.info(f"  [{idx}/{total}] Generating {name}...")
                result = generator.generate()

                # Handle different return types
                if isinstance(result, dict):
                    for file_name, file_path in result.items():
                        self.result.add_generated_file(f"{name} - {file_name}", file_path)
                else:
                    self.result.add_generated_file(name, result)

                logger.success(f"  ✓ {name} generated successfully")

            except GenerationError as e:
                self.result.add_error(f"Failed to generate {name}: {e}")
            except Exception as e:
                self.result.add_error(f"Unexpected error generating {name}: {e}")
                logger.exception(f"Error generating {name}")

    def _show_dry_run_preview(self, api_schema: APISchema):
        """
        Show what would be generated in dry-run mode.

        Args:
            api_schema: Parsed API schema
        """
        logger.info("\nDry-run mode - showing what would be generated:\n")

        logger.info(f"API: {api_schema.title} v{api_schema.version}")
        logger.info(f"Base URL: {api_schema.base_url}")
        logger.info(f"Endpoints: {len(api_schema.endpoints)}")
        logger.info(f"Models: {len(api_schema.models)}")

        logger.info("\nFiles that would be generated:")
        output_dir = Path(self.args.output)

        files = []
        if not self.args.skip_models:
            files.append(output_dir / "models.py")
        if not self.args.skip_validators:
            files.append(output_dir / "validators.py")
        if not self.args.skip_tests:
            files.append(output_dir / "test_api.py")
        if not self.args.skip_app:
            files.append(output_dir / "app.py")
        if not self.args.skip_docs:
            files.append(output_dir / "data_dict.md")
        if not self.args.skip_docker:
            files.append(output_dir / "Dockerfile")
            files.append(output_dir / ".dockerignore")

        for file_path in files:
            logger.info(f"  - {file_path}")

    def _report_results(self):
        """Report the final results of the generation."""
        logger.info("\n" + "=" * 70)
        logger.info("GENERATION COMPLETE")
        logger.info("=" * 70)

        if self.result.success:
            logger.success(f"✓ Successfully generated {len(self.result.generated_files)} files")
            logger.info(f"Duration: {self.result.duration_seconds:.2f} seconds")

            if self.result.generated_files:
                logger.info("\nGenerated files:")
                for name, path in self.result.generated_files.items():
                    logger.info(f"  - {name}: {path}")

            if self.result.warnings:
                logger.warning(f"\n⚠ {len(self.result.warnings)} warnings:")
                for warning in self.result.warnings:
                    logger.warning(f"  - {warning}")

            logger.info("\nNext steps:")
            logger.info("  1. Review generated files")
            logger.info("  2. Install dependencies: pip install -r requirements.txt")
            logger.info("  3. Run tests: pytest test_api.py")
            logger.info("  4. Start API: python -m uvicorn app:app --reload")
            logger.info("  5. Build Docker: docker build -t api-validator .")

        else:
            logger.error(f"✗ Generation failed with {len(self.result.errors)} errors")
            logger.info(f"Duration: {self.result.duration_seconds:.2f} seconds")

            for error in self.result.errors:
                logger.error(f"  - {error}")

            if self.result.generated_files:
                logger.info(f"\nPartially generated {len(self.result.generated_files)} files:")
                for name, path in self.result.generated_files.items():
                    logger.info(f"  - {name}: {path}")


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="DataSentinel - Automated API Validation & Documentation Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from JSON endpoint
  %(prog)s --api https://api.example.com/users

  # Generate from OpenAPI file
  %(prog)s --api ./specs/openapi.yaml --output ./generated

  # Generate from GraphQL endpoint
  %(prog)s --api https://api.example.com/graphql --format graphql

  # With authentication
  %(prog)s --api https://api.example.com/users --auth-type bearer --auth-token $TOKEN

  # Dry-run mode (show what would be generated)
  %(prog)s --api https://api.example.com/users --dry-run

For more information, visit: https://github.com/yourusername/datasentinel
        """,
    )

    # Required arguments
    parser.add_argument(
        "--api",
        required=True,
        help="API source: URL, file path, or endpoint",
    )

    # Output options
    parser.add_argument(
        "--output",
        "-o",
        default="./generated",
        help="Output directory for generated files (default: ./generated)",
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "openapi", "graphql"],
        help="Input format (auto-detected if not specified)",
    )

    # Authentication options
    auth_group = parser.add_argument_group("authentication options")
    auth_group.add_argument(
        "--auth-type",
        choices=["none", "api-key", "bearer", "oauth2", "basic"],
        default="none",
        help="Authentication type (default: none)",
    )
    auth_group.add_argument(
        "--auth-token",
        help="Authentication token or API key",
    )
    auth_group.add_argument(
        "--auth-header",
        help="Custom authentication header name",
    )
    auth_group.add_argument(
        "--auth-username",
        help="Username for basic authentication",
    )

    # Generation options
    gen_group = parser.add_argument_group("generation options")
    gen_group.add_argument(
        "--skip-models",
        action="store_true",
        help="Skip models.py generation",
    )
    gen_group.add_argument(
        "--skip-validators",
        action="store_true",
        help="Skip validators.py generation",
    )
    gen_group.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test_api.py generation",
    )
    gen_group.add_argument(
        "--skip-app",
        action="store_true",
        help="Skip app.py generation",
    )
    gen_group.add_argument(
        "--skip-docs",
        action="store_true",
        help="Skip documentation generation",
    )
    gen_group.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip Dockerfile generation",
    )

    # Other options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without creating files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--log-file",
        help="Write logs to file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="DataSentinel 1.0.0",
    )

    return parser


async def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Create and run orchestrator
    orchestrator = AutoSentinel(args)
    result = await orchestrator.run()

    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
