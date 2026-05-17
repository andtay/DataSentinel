You are acting as a senior Python architect and Data Engineer Senior. I need you to create a complete 
architectural plan for a tool called Data Sentinel.

## What Data Sentinel does

Data Sentinel takes an API specification as input (REST endpoint URL, Swagger/
OpenAPI file, or raw JSON example) and automatically generates a full validation 
and documentation suite for that API — with zero manual coding required.

## Expected outputs (files to generate)

1. models.py       — Pydantic v2 models with field types, validators, and 
                     business rules inferred from the API spec
2. validators.py   — Validation logic with retry handling, error reporting, 
                     and schema drift detection
3. test_api.py     — Pytest test suite covering all endpoints and edge cases
4. app.py          — FastAPI app that exposes the validator as a REST service
5. data_dict.md    — Auto-generated data dictionary documenting every field
6. Dockerfile      — Container ready for deployment on AWS / GCP / Azure

## Tech stack

- Python 3+
- Pydantic v2 (data contracts and validation)
- httpx (async HTTP calls)
- polyfactory (mock data generation from Pydantic models)
- FastAPI + uvicorn (REST service layer)
- pytest + pytest-asyncio (test suite)
- Docker (containerization)

## What I need from you in Plan Mode

1. Define the full modular architecture of the project — folder structure, 
   responsibilities of each file, and how they interact with each other.

2. Identify the main classes and functions needed in each file, with a detailed 
   description of what each one does.

3. Define the input interface: how auto_sentinel.py accepts --api (URL or 
   file path) and orchestrates the full generation pipeline.

4. Flag any architectural decisions or trade-offs I should be aware of before 
   we start coding (e.g., sync vs async, OpenAPI parsing strategy, error 
   handling approach).

5. Produce a prioritized list of files to generate in order, so we can 
   tackle them one by one in Code Mode next.

Do not write any code yet. Focus entirely on the plan.