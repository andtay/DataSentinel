# Architecture Diagrams

Visual documentation of DataSentinel's architecture and workflows.

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Parser Pipeline](#parser-pipeline)
5. [Generator Pipeline](#generator-pipeline)
6. [Deployment Architecture](#deployment-architecture)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DataSentinel                              │
│                   Agentic API Validation Framework               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │         Input Sources                    │
        ├─────────────────────────────────────────┤
        │  • OpenAPI/Swagger (YAML/JSON)          │
        │  • GraphQL Endpoint (Introspection)     │
        │  • JSON Samples (Type Inference)        │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │         Parsing Layer                    │
        ├─────────────────────────────────────────┤
        │  • OpenAPIParser                         │
        │  • GraphQLParser                         │
        │  • JSONInferenceParser                   │
        │  • SchemaNormalizer                      │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Normalized APISchema                │
        │    (Internal Representation)             │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │       Generation Layer                   │
        ├─────────────────────────────────────────┤
        │  • ModelsGenerator                       │
        │  • ValidatorsGenerator                   │
        │  • TestsGenerator                        │
        │  • AppGenerator                          │
        │  • DocsGenerator                         │
        │  • DockerfileGenerator                   │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Generated Artifacts                 │
        ├─────────────────────────────────────────┤
        │  • models.py (Pydantic V2)              │
        │  • validators.py (with retry)           │
        │  • test_api.py (Pytest suite)           │
        │  • app.py (FastAPI)                     │
        │  • data_dict.md (Documentation)         │
        │  • Dockerfile (Container)               │
        └─────────────────────────────────────────┘
```

---

## Component Architecture

```
DataSentinel/
│
├─── CLI Layer (auto_sentinel.py)
│    └─── Orchestrates entire pipeline
│
├─── Configuration Layer
│    ├─── settings.py (Pydantic Settings)
│    └─── logging_config.py (Loguru)
│
├─── Core Infrastructure
│    ├─── base_provider.py
│    │    ├─── HTTP client (httpx)
│    │    ├─── Retry logic
│    │    └─── Authentication
│    │
│    ├─── retry_handler.py
│    │    ├─── Exponential backoff
│    │    ├─── Jitter
│    │    └─── Max retries
│    │
│    ├─── auth_manager.py
│    │    ├─── API Key
│    │    ├─── Bearer Token
│    │    ├─── OAuth2
│    │    └─── Basic Auth
│    │
│    └─── exceptions.py
│         └─── Custom exception hierarchy
│
├─── Parsing Layer
│    ├─── base_parser.py (Abstract)
│    │
│    ├─── json_inference_parser.py
│    │    ├─── Type inference
│    │    ├─── Pattern detection
│    │    └─── Nested structure handling
│    │
│    ├─── openapi_parser.py
│    │    ├─── $ref resolution (prance)
│    │    ├─── OpenAPI 3.x support
│    │    └─── Swagger 2.0 support
│    │
│    ├─── graphql_parser.py
│    │    ├─── Introspection query
│    │    ├─── Type mapping
│    │    └─── Custom scalars
│    │
│    └─── schema_normalizer.py
│         ├─── Field normalization
│         ├─── Type conflict resolution
│         └─── Model deduplication
│
├─── Schema Layer
│    ├─── api_schema.py
│    │    ├─── APISchema
│    │    ├─── Endpoint
│    │    └─── ModelSchema
│    │
│    ├─── field_schema.py
│    │    ├─── FieldSchema
│    │    ├─── FieldType
│    │    └─── Validator
│    │
│    └─── config_schema.py
│         └─── Configuration models
│
├─── Generation Layer
│    ├─── base_generator.py (Abstract)
│    │    └─── Jinja2 environment
│    │
│    ├─── models_generator.py
│    │    ├─── Pydantic V2 models
│    │    ├─── Field validators
│    │    └─── Nested models
│    │
│    ├─── validators_generator.py
│    │    ├─── Validation logic
│    │    ├─── Retry integration
│    │    └─── Drift detection
│    │
│    ├─── tests_generator.py
│    │    ├─── Pytest tests
│    │    ├─── Polyfactory factories
│    │    └─── Mock setup
│    │
│    ├─── app_generator.py
│    │    ├─── FastAPI app
│    │    ├─── Endpoints
│    │    └─── CORS config
│    │
│    ├─── docs_generator.py
│    │    └─── Markdown data dictionary
│    │
│    └─── dockerfile_generator.py
│         ├─── Multi-stage build
│         └─── Health checks
│
└─── Templates Layer
     └─── Jinja2 templates for code generation
```

---

## Data Flow

### Complete Pipeline Flow

```
┌──────────────┐
│ User Input   │
│ (CLI Args)   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ 1. Configuration & Validation            │
│    • Parse CLI arguments                 │
│    • Load settings                       │
│    • Setup logging                       │
│    • Validate configuration              │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ 2. Input Format Detection                │
│    • Check file extension                │
│    • Analyze URL patterns                │
│    • Inspect content structure           │
│    • Select appropriate parser           │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ 3. Parsing Phase                         │
│    ┌────────────────────────────────┐   │
│    │ OpenAPI Parser                  │   │
│    │  • Load spec (YAML/JSON)       │   │
│    │  • Resolve $ref                │   │
│    │  • Extract schemas             │   │
│    │  • Extract endpoints           │   │
│    └────────────────────────────────┘   │
│    ┌────────────────────────────────┐   │
│    │ GraphQL Parser                  │   │
│    │  • Execute introspection       │   │
│    │  • Parse types                 │   │
│    │  • Map queries/mutations       │   │
│    │  • Handle custom scalars       │   │
│    └────────────────────────────────┘   │
│    ┌────────────────────────────────┐   │
│    │ JSON Inference Parser           │   │
│    │  • Load JSON sample            │   │
│    │  • Infer types                 │   │
│    │  • Detect patterns             │   │
│    │  • Build structure             │   │
│    └────────────────────────────────┘   │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ 4. Schema Normalization                  │
│    • Normalize field names               │
│    • Resolve type conflicts              │
│    • Merge duplicate models              │
│    • Validate schema integrity           │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ 5. APISchema (Normalized)                │
│    • Unified data structure              │
│    • All models defined                  │
│    • All endpoints mapped                │
│    • Validation rules extracted          │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ 6. Code Generation Phase                 │
│    ┌────────────────────────────────┐   │
│    │ Models Generator                │   │
│    │  • Render Jinja2 template      │   │
│    │  • Generate Pydantic models    │   │
│    │  • Add field validators        │   │
│    │  • Format with Black           │   │
│    └────────────────────────────────┘   │
│    ┌────────────────────────────────┐   │
│    │ Validators Generator            │   │
│    │  • Generate validator classes  │   │
│    │  • Add retry logic             │   │
│    │  • Add drift detection         │   │
│    │  • Format code                 │   │
│    └────────────────────────────────┘   │
│    ┌────────────────────────────────┐   │
│    │ Tests Generator                 │   │
│    │  • Generate test cases         │   │
│    │  • Create factories            │   │
│    │  • Add fixtures                │   │
│    │  • Format code                 │   │
│    └────────────────────────────────┘   │
│    ┌────────────────────────────────┐   │
│    │ App Generator                   │   │
│    │  • Generate FastAPI app        │   │
│    │  • Create endpoints            │   │
│    │  • Add middleware              │   │
│    │  • Format code                 │   │
│    └────────────────────────────────┘   │
│    ┌────────────────────────────────┐   │
│    │ Docs Generator                  │   │
│    │  • Generate data dictionary    │   │
│    │  • Add examples                │   │
│    │  • Format markdown             │   │
│    └────────────────────────────────┘   │
│    ┌────────────────────────────────┐   │
│    │ Dockerfile Generator            │   │
│    │  • Generate Dockerfile         │   │
│    │  • Generate .dockerignore      │   │
│    │  • Add health checks           │   │
│    └────────────────────────────────┘   │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ 7. Output Artifacts                      │
│    • models.py                           │
│    • validators.py                       │
│    • test_api.py                         │
│    • app.py                              │
│    • data_dict.md                        │
│    • Dockerfile                          │
│    • .dockerignore                       │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ 8. Completion Report                     │
│    • Success/failure status              │
│    • Generated files list                │
│    • Warnings and errors                 │
│    • Next steps guidance                 │
└──────────────────────────────────────────┘
```

---

## Parser Pipeline

### OpenAPI Parser Flow

```
OpenAPI Spec (YAML/JSON)
         │
         ▼
┌─────────────────────┐
│ Load Specification  │
│  • Read file/URL    │
│  • Parse YAML/JSON  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Resolve References  │
│  • Find all $refs   │
│  • Load external    │
│  • Inline refs      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Extract Schemas     │
│  • Parse components │
│  • Map types        │
│  • Extract rules    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Extract Endpoints   │
│  • Parse paths      │
│  • Map operations   │
│  • Extract params   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Build APISchema     │
│  • Create models    │
│  • Create endpoints │
│  • Add metadata     │
└──────┬──────────────┘
       │
       ▼
    APISchema
```

### GraphQL Parser Flow

```
GraphQL Endpoint
         │
         ▼
┌─────────────────────┐
│ Execute             │
│ Introspection Query │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Parse Schema        │
│  • Extract types    │
│  • Parse fields     │
│  • Map scalars      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Extract Operations  │
│  • Parse queries    │
│  • Parse mutations  │
│  • Map to REST      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Build APISchema     │
│  • Create models    │
│  • Create endpoints │
│  • Add metadata     │
└──────┬──────────────┘
       │
       ▼
    APISchema
```

### JSON Inference Flow

```
JSON Sample
         │
         ▼
┌─────────────────────┐
│ Load JSON           │
│  • Read file/URL    │
│  • Parse JSON       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Analyze Structure   │
│  • Find objects     │
│  • Find arrays      │
│  • Find primitives  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Infer Types         │
│  • Detect patterns  │
│  • Map to types     │
│  • Handle nulls     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Build Models        │
│  • Create schemas   │
│  • Add validators   │
│  • Handle nesting   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Build APISchema     │
│  • Create models    │
│  • Infer endpoints  │
│  • Add metadata     │
└──────┬──────────────┘
       │
       ▼
    APISchema
```

---

## Generator Pipeline

```
APISchema
    │
    ├─────────────────────────────────────┐
    │                                     │
    ▼                                     ▼
┌─────────────┐                   ┌─────────────┐
│   Models    │                   │ Validators  │
│  Generator  │                   │  Generator  │
└──────┬──────┘                   └──────┬──────┘
       │                                 │
       ▼                                 ▼
  models.py                        validators.py
       │                                 │
       └─────────────┬───────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌─────────┐    ┌─────────┐    ┌──────────┐
│  Tests  │    │   App   │    │   Docs   │
│Generator│    │Generator│    │Generator │
└────┬────┘    └────┬────┘    └────┬─────┘
     │              │              │
     ▼              ▼              ▼
test_api.py      app.py      data_dict.md
     │              │              │
     └──────────────┼──────────────┘
                    │
                    ▼
            ┌───────────────┐
            │  Dockerfile   │
            │   Generator   │
            └───────┬───────┘
                    │
                    ▼
              Dockerfile
            .dockerignore
```

---

## Deployment Architecture

### Local Development

```
┌─────────────────────────────────────┐
│     Developer Machine               │
│                                     │
│  ┌───────────────────────────────┐ │
│  │   DataSentinel CLI            │ │
│  │   (auto_sentinel.py)          │ │
│  └───────────┬───────────────────┘ │
│              │                      │
│              ▼                      │
│  ┌───────────────────────────────┐ │
│  │   Generated Service           │ │
│  │   ├─ models.py                │ │
│  │   ├─ validators.py            │ │
│  │   ├─ test_api.py              │ │
│  │   └─ app.py                   │ │
│  └───────────┬───────────────────┘ │
│              │                      │
│              ▼                      │
│  ┌───────────────────────────────┐ │
│  │   Uvicorn Server              │ │
│  │   localhost:8000              │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Docker Deployment

```
┌─────────────────────────────────────┐
│     Docker Container                │
│                                     │
│  ┌───────────────────────────────┐ │
│  │   Python 3.11 Runtime         │ │
│  └───────────┬───────────────────┘ │
│              │                      │
│              ▼                      │
│  ┌───────────────────────────────┐ │
│  │   Generated Service           │ │
│  │   (All artifacts)             │ │
│  └───────────┬───────────────────┘ │
│              │                      │
│              ▼                      │
│  ┌───────────────────────────────┐ │
│  │   Uvicorn Server              │ │
│  │   0.0.0.0:8000                │ │
│  └───────────┬───────────────────┘ │
│              │                      │
└──────────────┼──────────────────────┘
               │
               ▼
        Host Port 8000
```

### Cloud Deployment (AWS ECS)

```
┌─────────────────────────────────────────────────┐
│              AWS Cloud                          │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │   Application Load Balancer               │ │
│  │   (HTTPS/TLS)                             │ │
│  └───────────┬───────────────────────────────┘ │
│              │                                  │
│              ▼                                  │
│  ┌───────────────────────────────────────────┐ │
│  │   ECS Service (Fargate)                   │ │
│  │   ┌─────────────┐  ┌─────────────┐       │ │
│  │   │  Task 1     │  │  Task 2     │       │ │
│  │   │  Container  │  │  Container  │  ...  │ │
│  │   └─────────────┘  └─────────────┘       │ │
│  └───────────────────────────────────────────┘ │
│              │                                  │
│              ▼                                  │
│  ┌───────────────────────────────────────────┐ │
│  │   CloudWatch Logs                         │ │
│  │   (Monitoring & Logging)                  │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## Request Flow

### Validation Request Flow

```
Client Request
      │
      ▼
┌─────────────────┐
│  FastAPI App    │
│  (app.py)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Endpoint       │
│  Handler        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validator      │
│  (validators.py)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pydantic Model │
│  (models.py)    │
└────────┬────────┘
         │
         ├─── Valid ────────┐
         │                  │
         └─── Invalid ──┐   │
                        │   │
                        ▼   ▼
                   ┌─────────────┐
                   │  Response   │
                   │  (JSON)     │
                   └─────────────┘
```

---

## Technology Stack Diagram

```
┌─────────────────────────────────────────────────┐
│              Application Layer                   │
│  ┌──────────────────────────────────────────┐  │
│  │  DataSentinel CLI (auto_sentinel.py)     │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│              Framework Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ FastAPI  │  │ Pydantic │  │  Pytest  │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│              Library Layer                       │
│  ┌──────┐  ┌──────┐  ┌────────┐  ┌─────────┐  │
│  │ HTTPX│  │Jinja2│  │ Prance │  │ Loguru  │  │
│  └──────┘  └──────┘  └────────┘  └─────────┘  │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│              Runtime Layer                       │
│  ┌──────────────────────────────────────────┐  │
│  │         Python 3.9+                      │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## Next Steps

- 📖 [Getting Started](getting_started.md) - Quick start guide
- 🎯 [Input Formats](input_formats.md) - Supported formats
- 🚀 [Deployment](deployment.md) - Deploy your service
- 📚 [API Reference](api_reference.md) - Complete API docs

---

**Made with ❤️ by the DataSentinel Team**