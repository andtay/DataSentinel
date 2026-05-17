# 🛡️ DataSentinel: Complete Architecture & Development Plan

## Table of Contents
1. [Project Overview](#project-overview)
2. [Complete Folder Structure](#complete-folder-structure)
3. [File Responsibilities](#file-responsibilities)
4. [Data Structures & Interfaces](#data-structures--interfaces)
5. [Implementation Roadmap](#implementation-roadmap)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Guidelines](#deployment-guidelines)

---

## Project Overview

**DataSentinel** is an agentic framework that automatically generates validation, testing, and documentation suites from API specifications. It supports three industry-standard input formats:

1. **OpenAPI/Swagger Specifications** (deterministic parsing)
2. **GraphQL Endpoints** (introspection-based)
3. **JSON Samples/REST URLs** (type inference engine)

**Core Philosophy:** Zero manual coding required - from API spec to production-ready validation service.

---

## Complete Folder Structure

```
DataSentinel/
│
├── auto_sentinel.py              # CLI entry point & orchestrator
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
├── setup.py                      # Package configuration
├── pyproject.toml               # Modern Python project config
├── .env.example                 # Environment variables template
├── .gitignore                   # Git exclusions
├── LICENSE                      # MIT License
├── README.md                    # Project documentation
├── ARCHITECTURE.md              # This file
├── CHANGELOG.md                 # Version history
│
├── config/                      # Configuration files
│   ├── __init__.py
│   ├── settings.py              # Pydantic settings management
│   └── logging_config.py        # Loguru configuration
│
├── core/                        # Core infrastructure (reusable)
│   ├── __init__.py
│   ├── base_provider.py         # Abstract base for API providers
│   ├── retry_handler.py         # Exponential backoff & retry logic
│   ├── auth_manager.py          # Authentication strategies
│   ├── exceptions.py            # Custom exception hierarchy
│   └── utils.py                 # Shared utility functions
│
├── parsers/                     # API specification parsers
│   ├── __init__.py
│   ├── base_parser.py           # Abstract parser interface
│   ├── openapi_parser.py        # OpenAPI/Swagger deterministic parser
│   ├── graphql_parser.py        # GraphQL introspection parser
│   ├── json_inference_parser.py # Type inference engine
│   └── schema_normalizer.py     # Normalize all inputs to APISchema
│
├── generators/                  # Code generation engines
│   ├── __init__.py
│   ├── base_generator.py        # Abstract generator interface
│   ├── model_generator.py       # Pydantic v2 model generation
│   ├── validator_generator.py   # Validation logic generation
│   ├── test_generator.py        # Pytest suite generation
│   ├── app_generator.py         # FastAPI app generation
│   ├── doc_generator.py         # Markdown documentation generation
│   └── docker_generator.py      # Dockerfile generation
│
├── templates/                   # Jinja2 templates for code generation
│   ├── model.py.j2              # Pydantic model template
│   ├── validator.py.j2          # Validator class template
│   ├── test.py.j2               # Pytest test template
│   ├── app.py.j2                # FastAPI app template
│   ├── data_dict.md.j2          # Data dictionary template
│   ├── Dockerfile.j2            # Dockerfile template
│   └── README.md.j2             # Generated project README
│
├── schemas/                     # Internal data structures
│   ├── __init__.py
│   ├── api_schema.py            # APISchema, Endpoint, ModelSchema
│   ├── field_schema.py          # FieldSchema, FieldType, Validators
│   └── config_schema.py         # Configuration models
│
├── output/                      # Generated artifacts (gitignored)
│   └── .gitkeep
│
├── examples/                    # Example API specifications
│   ├── openapi/
│   │   ├── petstore.yaml
│   │   └── meteomatics_swagger_definition.yaml.txt
│   ├── graphql/
│   │   └── github_graphql.txt
│   └── json/
│       ├── user_sample.json
│       └── product_sample.json
│
├── tests/                       # Unit & integration tests
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_parsers.py
│   │   ├── test_generators.py
│   │   └── test_core.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_openapi_flow.py
│   │   ├── test_graphql_flow.py
│   │   └── test_json_flow.py
│   └── fixtures/
│       ├── sample_openapi.yaml
│       ├── sample_response.json
│       └── mock_graphql_schema.json
│
├── docs/                        # Documentation
│   ├── getting_started.md
│   ├── input_formats.md
│   ├── generated_artifacts.md
│   ├── deployment.md
│   └── api_reference.md
│
└── scripts/                     # Utility scripts
    ├── setup_dev.sh             # Development environment setup
    ├── run_tests.sh             # Test runner
    └── build_docker.sh          # Docker build script
```

---

## File Responsibilities

See [FILE_RESPONSIBILITIES.md](FILE_RESPONSIBILITIES.md) for detailed documentation of each file's purpose, key classes, and functions.

---

## Data Structures & Interfaces

See [DATA_STRUCTURES.md](DATA_STRUCTURES.md) for complete schema definitions and interface contracts.

---

## Implementation Roadmap

See [ROADMAP.md](ROADMAP.md) for the detailed, prioritized implementation plan with sprints and deliverables.

---

## Testing Strategy

See [TESTING.md](TESTING.md) for comprehensive testing approach, coverage goals, and test examples.

---

## Deployment Guidelines

See [DEPLOYMENT.md](DEPLOYMENT.md) for local development setup, Docker deployment, and cloud deployment instructions.