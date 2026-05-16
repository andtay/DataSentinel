# Getting Started with DataSentinel

Welcome to DataSentinel! This guide will help you get up and running quickly.

## Table of Contents

1. [What is DataSentinel?](#what-is-datasentinel)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Basic Usage](#basic-usage)
5. [Your First Project](#your-first-project)
6. [Next Steps](#next-steps)

---

## What is DataSentinel?

DataSentinel is an agentic framework that automatically generates validation, testing, and documentation suites from API specifications. It eliminates manual coding by transforming API specs into production-ready code.

### Key Features

- 🚀 **Zero Manual Coding** - From API spec to production-ready validation service
- 🔄 **Three Input Formats** - OpenAPI/Swagger, GraphQL, or JSON samples
- 🛡️ **Automatic Validation** - Pydantic v2 models with comprehensive validators
- 🧪 **Test Generation** - Complete pytest suite with factories
- 📦 **FastAPI App** - Ready-to-deploy validation API
- 🐳 **Docker Ready** - Multi-stage Dockerfile included
- 📚 **Auto Documentation** - Markdown data dictionaries

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (optional, for cloning)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/datasentinel.git
cd datasentinel

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### Verify Installation

```bash
python auto_sentinel.py --version
```

You should see: `DataSentinel 1.0.0`

---

## Quick Start

### 1. Generate from JSON Endpoint

The simplest way to get started is with a JSON endpoint:

```bash
python auto_sentinel.py \
  --api https://jsonplaceholder.typicode.com/users \
  --output ./my-first-project
```

This will:
- Fetch the JSON response
- Infer data types and structure
- Generate all artifacts in `./my-first-project/`

### 2. Generate from OpenAPI Spec

If you have an OpenAPI/Swagger specification:

```bash
python auto_sentinel.py \
  --api ./specs/openapi.yaml \
  --output ./my-api-validator
```

### 3. Generate from GraphQL Endpoint

For GraphQL APIs with introspection enabled:

```bash
python auto_sentinel.py \
  --api https://api.example.com/graphql \
  --format graphql \
  --output ./graphql-validator
```

---

## Basic Usage

### Command-Line Interface

```bash
python auto_sentinel.py --api <SOURCE> [OPTIONS]
```

### Required Arguments

- `--api` - API source (URL, file path, or endpoint)

### Common Options

- `--output` / `-o` - Output directory (default: `./generated`)
- `--format` / `-f` - Input format: `json`, `openapi`, or `graphql` (auto-detected if not specified)
- `--verbose` / `-v` - Enable verbose logging
- `--dry-run` - Show what would be generated without creating files

### Authentication Options

```bash
# API Key authentication
python auto_sentinel.py \
  --api https://api.example.com/data \
  --auth-type api-key \
  --auth-token YOUR_API_KEY

# Bearer token authentication
python auto_sentinel.py \
  --api https://api.example.com/data \
  --auth-type bearer \
  --auth-token YOUR_BEARER_TOKEN

# Basic authentication
python auto_sentinel.py \
  --api https://api.example.com/data \
  --auth-type basic \
  --auth-username user \
  --auth-token password
```

### Generation Options

Skip specific generators:

```bash
python auto_sentinel.py \
  --api ./spec.yaml \
  --skip-tests \
  --skip-docker
```

Available skip options:
- `--skip-models` - Skip Pydantic models
- `--skip-validators` - Skip validators
- `--skip-tests` - Skip test suite
- `--skip-app` - Skip FastAPI app
- `--skip-docs` - Skip documentation
- `--skip-docker` - Skip Dockerfile

---

## Your First Project

Let's create a complete validation service from scratch!

### Step 1: Generate the Code

```bash
# Using a sample JSON endpoint
python auto_sentinel.py \
  --api https://jsonplaceholder.typicode.com/users \
  --output ./user-validator \
  --verbose
```

### Step 2: Explore Generated Files

```bash
cd user-validator
ls -la
```

You should see:
```
models.py          # Pydantic v2 models
validators.py      # Validation logic with retry
test_api.py        # Pytest test suite
app.py             # FastAPI application
data_dict.md       # Documentation
Dockerfile         # Docker configuration
.dockerignore      # Docker ignore file
```

### Step 3: Install Dependencies

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install required packages
pip install fastapi uvicorn pydantic httpx pytest
```

### Step 4: Run the Tests

```bash
pytest test_api.py -v
```

### Step 5: Start the API

```bash
uvicorn app:app --reload
```

Visit http://localhost:8000/docs to see the interactive API documentation!

### Step 6: Use the Validation API

```bash
# Validate data
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  }'
```

### Step 7: Build Docker Image (Optional)

```bash
docker build -t user-validator .
docker run -p 8000:8000 user-validator
```

---

## Next Steps

### Learn More

- 📖 [Input Formats Guide](input_formats.md) - Detailed guide for each input type
- 🎯 [Generated Artifacts](generated_artifacts.md) - Understanding generated code
- 🚀 [Deployment Guide](deployment.md) - Deploy to production
- 📚 [API Reference](api_reference.md) - Complete API documentation

### Example Projects

Check out the `examples/` directory for:
- OpenAPI/Swagger examples
- GraphQL examples
- JSON inference examples

### Advanced Features

- **Schema Drift Detection** - Automatically detect API changes
- **Batch Validation** - Validate multiple records efficiently
- **Custom Validators** - Extend generated validators
- **CI/CD Integration** - Automate validation in pipelines

### Get Help

- 📝 [GitHub Issues](https://github.com/yourusername/datasentinel/issues)
- 💬 [Discussions](https://github.com/yourusername/datasentinel/discussions)
- 📧 Email: support@datasentinel.dev

---

## Common Issues

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'pydantic'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Permission Errors

**Problem:** `PermissionError: [Errno 13] Permission denied`

**Solution:**
```bash
# Ensure output directory is writable
chmod +w ./output-directory
```

### API Authentication Fails

**Problem:** `401 Unauthorized`

**Solution:**
```bash
# Verify your authentication credentials
python auto_sentinel.py \
  --api https://api.example.com/data \
  --auth-type bearer \
  --auth-token YOUR_VALID_TOKEN \
  --verbose
```

### Generated Code Has Errors

**Problem:** Generated Python code has syntax errors

**Solution:**
1. Ensure you're using Python 3.9+
2. Update dependencies: `pip install --upgrade -r requirements.txt`
3. Report the issue with your input specification

---

## Tips and Best Practices

### 1. Use Dry-Run First

Before generating files, preview what will be created:

```bash
python auto_sentinel.py --api ./spec.yaml --dry-run
```

### 2. Version Control

Add generated code to version control to track changes:

```bash
git add generated/
git commit -m "Add generated validation code"
```

### 3. Customize Generated Code

Generated code is meant to be customized:
- Add business logic to validators
- Extend models with computed fields
- Add custom endpoints to the FastAPI app

### 4. Keep Specs Updated

Regenerate code when your API specification changes:

```bash
python auto_sentinel.py --api ./updated-spec.yaml --output ./validator
```

### 5. Use Environment Variables

Store sensitive data in environment variables:

```bash
export API_TOKEN="your-secret-token"
python auto_sentinel.py \
  --api https://api.example.com/data \
  --auth-type bearer \
  --auth-token $API_TOKEN
```

---

## What's Next?

Now that you have DataSentinel running, explore:

1. **[Input Formats](input_formats.md)** - Learn about supported input formats
2. **[Generated Artifacts](generated_artifacts.md)** - Understand the generated code
3. **[Deployment](deployment.md)** - Deploy your validation service
4. **[API Reference](api_reference.md)** - Dive into the API details

Happy validating! 🎉