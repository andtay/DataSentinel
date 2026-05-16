# 🛡️ DataSentinel: Agentic API Validation Framework

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**DataSentinel** is an agentic framework that automatically generates validation, testing, and documentation suites from API specifications. Transform any API spec into production-ready validation services with zero manual coding.

---

## 🚀 The Problem

Data Scientists and Engineers spend up to **80% of their time** on "data plumbing":
- 📖 Reading API documentation
- ✍️ Writing manual data models
- 🐛 Debugging schema drift
- 🧪 Creating test suites
- 📝 Maintaining documentation

**DataSentinel eliminates this overhead entirely.**

---

## 🧠 The Agentic Solution

DataSentinel uses **IBM Bob** as a proactive architect that:

1. **🔍 Scans & Maps** - Analyzes any endpoint (REST/GraphQL/JSON) and auto-generates robust data contracts
2. **✅ Guarantees Quality** - Implements real-time validation with Pydantic V2
3. **⚡ Accelerates Development** - Creates complete test suites with mock factories
4. **📚 Self-Documents** - Generates technical documentation automatically
5. **🐳 Deploys Instantly** - Produces Docker-ready FastAPI services

---

## ✨ Key Features

### Three Input Formats
- **OpenAPI/Swagger** - Deterministic parsing with full $ref resolution
- **GraphQL** - Introspection-based schema extraction
- **JSON Samples** - Intelligent type inference engine

### Generated Artifacts
- **Pydantic V2 Models** - Type-safe data models with validation
- **Validators** - Retry logic and schema drift detection
- **Pytest Suite** - Comprehensive tests with factories
- **FastAPI App** - Production-ready validation API
- **Documentation** - Markdown data dictionaries
- **Docker** - Multi-stage optimized containers

### Production Features
- ✅ Exponential backoff retry logic
- ✅ Multiple authentication strategies (API Key, Bearer, OAuth2, Basic)
- ✅ Schema drift detection and alerting
- ✅ Batch validation support
- ✅ Async/await throughout
- ✅ Comprehensive error handling
- ✅ Structured logging with Loguru

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Agentic Engine** | IBM Bob |
| **Validation** | Pydantic V2 (Strict Mode) |
| **Networking** | HTTPX (Async) |
| **API Framework** | FastAPI |
| **Testing** | Pytest + Polyfactory |
| **Logging** | Loguru |
| **Parsing** | Prance (OpenAPI), GraphQL Introspection |
| **Templating** | Jinja2 |
| **Code Formatting** | Black |

---

## 📦 Installation

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/datasentinel.git
cd datasentinel

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
python auto_sentinel.py --version
# Output: DataSentinel 1.0.0
```

---

## 🚀 Quick Start

### Generate from JSON Endpoint

```bash
python auto_sentinel.py \
  --api https://jsonplaceholder.typicode.com/users \
  --output ./my-validator
```

### Generate from OpenAPI Spec

```bash
python auto_sentinel.py \
  --api ./specs/openapi.yaml \
  --output ./api-validator
```

### Generate from GraphQL

```bash
python auto_sentinel.py \
  --api https://api.example.com/graphql \
  --format graphql \
  --output ./graphql-validator
```

### Run Generated Service

```bash
cd my-validator
pip install -r requirements.txt
pytest test_api.py -v
uvicorn app:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation!

---

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting_started.md) | Installation, quick start, first project |
| [Input Formats](docs/input_formats.md) | JSON, OpenAPI, GraphQL format guides |
| [Generated Artifacts](docs/generated_artifacts.md) | Understanding generated code |
| [Deployment](docs/deployment.md) | Local, Docker, and cloud deployment |
| [API Reference](docs/api_reference.md) | Complete API documentation |

---

## 🏗️ Architecture

DataSentinel follows a modular, provider-based architecture:

```
DataSentinel/
├── auto_sentinel.py       # CLI entry point & orchestrator
├── config/                # Configuration management
│   ├── settings.py        # Pydantic settings
│   └── logging_config.py  # Loguru configuration
├── core/                  # Core infrastructure
│   ├── base_provider.py   # Abstract base for providers
│   ├── retry_handler.py   # Exponential backoff
│   ├── auth_manager.py    # Authentication strategies
│   └── exceptions.py      # Custom exceptions
├── parsers/               # API specification parsers
│   ├── json_inference_parser.py
│   ├── openapi_parser.py
│   └── graphql_parser.py
├── generators/            # Code generation engines
│   ├── models_generator.py
│   ├── validators_generator.py
│   ├── tests_generator.py
│   ├── app_generator.py
│   ├── docs_generator.py
│   └── dockerfile_generator.py
├── schemas/               # Internal data structures
│   ├── api_schema.py
│   ├── field_schema.py
│   └── config_schema.py
└── templates/             # Jinja2 templates
    ├── models.py.jinja2
    ├── validators.py.jinja2
    ├── test_api.py.jinja2
    └── app.py.jinja2
```

---

## 💡 Usage Examples

### With Authentication

```bash
# API Key
python auto_sentinel.py \
  --api https://api.example.com/data \
  --auth-type api-key \
  --auth-token YOUR_API_KEY

# Bearer Token
python auto_sentinel.py \
  --api https://api.example.com/data \
  --auth-type bearer \
  --auth-token YOUR_TOKEN

# OAuth2
python auto_sentinel.py \
  --api https://api.example.com/data \
  --auth-type oauth2 \
  --auth-token YOUR_TOKEN
```

### Selective Generation

```bash
# Skip tests and Docker
python auto_sentinel.py \
  --api ./spec.yaml \
  --skip-tests \
  --skip-docker

# Only generate models and validators
python auto_sentinel.py \
  --api ./spec.yaml \
  --skip-tests \
  --skip-app \
  --skip-docs \
  --skip-docker
```

### Dry Run Mode

```bash
# Preview what would be generated
python auto_sentinel.py \
  --api ./spec.yaml \
  --dry-run
```

---

## 🧪 Testing

DataSentinel includes comprehensive test coverage:

```bash
# Run all tests
pytest tests/ -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/integration/test_json_flow.py -v
```

### Test Coverage
- ✅ Unit tests for all modules
- ✅ Integration tests for complete pipelines
- ✅ Performance benchmarks
- ✅ Error handling tests
- ✅ 90%+ code coverage

---

## 🐳 Docker Deployment

### Build and Run

```bash
cd generated/
docker build -t my-validator .
docker run -p 8000:8000 my-validator
```

### Docker Compose

```yaml
version: '3.8'
services:
  validator:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

```bash
docker-compose up -d
```

---

## ☁️ Cloud Deployment

### AWS ECS

```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag my-validator:latest <account>.dkr.ecr.us-east-1.amazonaws.com/my-validator:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/my-validator:latest
```

### Google Cloud Run

```bash
gcloud run deploy my-validator \
  --image gcr.io/<project>/my-validator:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name my-validator \
  --image <registry>.azurecr.io/my-validator:latest \
  --ports 8000
```

---

## 🗺️ Project Status

### ✅ Completed Features

#### Phase 1: Foundation
- ✅ Core infrastructure with async support
- ✅ Configuration management (Pydantic Settings)
- ✅ Logging system (Loguru)
- ✅ Exception hierarchy
- ✅ Retry handler with exponential backoff
- ✅ Authentication manager (API Key, Bearer, OAuth2, Basic)
- ✅ Base provider pattern

#### Phase 2: Parsers
- ✅ JSON inference parser with pattern detection
- ✅ OpenAPI parser (3.x and Swagger 2.0)
- ✅ GraphQL introspection parser
- ✅ Schema normalizer

#### Phase 3: Generators
- ✅ Pydantic V2 models generator
- ✅ Validators generator with retry and drift detection
- ✅ Pytest test suite generator with factories
- ✅ FastAPI app generator
- ✅ Documentation generator
- ✅ Dockerfile generator

#### Phase 4: Integration & Documentation
- ✅ CLI orchestrator
- ✅ Comprehensive integration tests (45+ tests)
- ✅ Complete documentation suite
- ✅ Example projects
- ✅ Production deployment guides

### 🚧 Future Enhancements

#### Phase 5: Advanced Features
- [ ] Schema versioning and migration
- [ ] Multi-sample JSON inference
- [ ] GraphQL subscription support
- [ ] Webhook listener generation
- [ ] Data profiling and statistics

#### Phase 6: Enterprise Features
- [ ] Web UI for management
- [ ] CI/CD integration
- [ ] Monitoring and alerting
- [ ] Multi-tenant support
- [ ] Enterprise authentication (SAML, LDAP)

---

## 📊 Performance

DataSentinel is designed for speed:

| Operation | Time |
|-----------|------|
| Parse OpenAPI spec | < 5 seconds |
| Generate all artifacts | < 10 seconds |
| Complete pipeline | < 15 seconds |
| Validation (single) | < 10ms |
| Validation (batch 100) | < 100ms |

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Format code
black .

# Type checking
mypy .

# Linting
flake8 .
```

---

## 📝 Examples

Check out the `examples/` directory for:
- OpenAPI/Swagger examples
- GraphQL examples
- JSON inference examples
- Real-world API integrations

---

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```bash
pip install -r requirements.txt
```

**Port Already in Use**
```bash
lsof -i :8000
kill -9 <PID>
```

**Docker Build Fails**
```bash
docker system prune -a
docker build --no-cache -t my-validator .
```

See [Deployment Guide](docs/deployment.md) for more troubleshooting tips.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

- **Andrew Rober Taylor** - *Lead Data Architect & AI Automation*  
  Focus: Designing agentic data ingestion pipelines, schema validation with Pydantic, and bridging the gap between raw API data and production-ready Data Science environments.

- **Vicente García Sánchez** - *Reliability & Integration Engineer*  
  Focus: Robust API consumption, error handling strategies (retries/backoff), and automated testing suites.

---

## 🙏 Acknowledgments

- **IBM Bob** - Agentic reasoning engine
- **Pydantic** - Data validation framework
- **FastAPI** - Modern web framework
- **HTTPX** - Async HTTP client
- **Pytest** - Testing framework

---

## 📞 Support

- 📝 [GitHub Issues](https://github.com/yourusername/datasentinel/issues)
- 💬 [Discussions](https://github.com/yourusername/datasentinel/discussions)
- 📧 Email: support@datasentinel.dev
- 📖 [Documentation](docs/)

---

## ⭐ Star History

If you find DataSentinel useful, please consider giving it a star! ⭐

---

**Made with ❤️ by the DataSentinel Team**

*Powered by IBM Bob - Transforming API specifications into production-ready validation services*
