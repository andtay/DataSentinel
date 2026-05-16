# Integration Tests

This directory contains comprehensive integration tests for DataSentinel's complete pipeline.

## Overview

Integration tests verify the end-to-end functionality of DataSentinel, from parsing API specifications to generating production-ready code artifacts.

## Test Files

### `test_json_flow.py`
Tests the complete JSON inference pipeline:
- ✅ Complete flow from JSON file to generated artifacts
- ✅ Type inference accuracy (int, str, bool, datetime, email, etc.)
- ✅ Generated code validity (syntax checking)
- ✅ Nested JSON structure handling
- ✅ Performance benchmarks
- ✅ Error handling (invalid JSON, empty JSON)
- ✅ Dry-run mode verification

### `test_openapi_flow.py`
Tests the OpenAPI/Swagger parsing pipeline:
- ✅ Complete flow from OpenAPI YAML/JSON to generated artifacts
- ✅ Schema extraction (models, fields, validation constraints)
- ✅ Endpoint extraction (paths, methods, parameters)
- ✅ $ref resolution (nested references)
- ✅ OpenAPI 3.x and Swagger 2.0 support
- ✅ Generated code matches specification
- ✅ Performance benchmarks
- ✅ Error handling (invalid specs, missing fields)

### `test_graphql_flow.py`
Tests the GraphQL introspection pipeline:
- ✅ Complete flow from GraphQL endpoint to generated artifacts
- ✅ Type extraction from introspection
- ✅ Query and mutation extraction
- ✅ Custom scalar handling (DateTime, UUID, etc.)
- ✅ Nested type handling
- ✅ Generated code validity
- ✅ Performance benchmarks
- ✅ Error handling (introspection disabled, network errors)

## Running Tests

### Run all integration tests:
```bash
pytest tests/integration/ -v
```

### Run specific test file:
```bash
pytest tests/integration/test_json_flow.py -v
pytest tests/integration/test_openapi_flow.py -v
pytest tests/integration/test_graphql_flow.py -v
```

### Run specific test:
```bash
pytest tests/integration/test_json_flow.py::TestJSONInferenceFlow::test_json_file_complete_flow -v
```

### Run with coverage:
```bash
pytest tests/integration/ --cov=. --cov-report=html
```

### Run performance tests only:
```bash
pytest tests/integration/ -v -k "performance"
```

### Run error handling tests only:
```bash
pytest tests/integration/ -v -k "error_handling"
```

## Test Coverage

The integration tests cover:

1. **Complete Pipeline Execution**
   - Input parsing (JSON, OpenAPI, GraphQL)
   - Schema normalization
   - Code generation (models, validators, tests, app, docs, Docker)
   - File creation verification

2. **Code Quality**
   - Generated code is valid Python (syntax checking)
   - Generated code is properly formatted
   - Generated code matches input specification
   - Generated code is importable

3. **Performance**
   - Parsing completes within acceptable time (< 5s)
   - Generation completes within acceptable time (< 10s)
   - Total pipeline completes within acceptable time (< 15s)

4. **Error Handling**
   - Invalid input formats
   - Missing required fields
   - Network errors (for remote endpoints)
   - Malformed specifications
   - Empty or minimal inputs

5. **Edge Cases**
   - Nested structures
   - Complex types (oneOf, anyOf, allOf)
   - Custom scalars
   - References ($ref)
   - Multiple input formats

## Test Fixtures

Test fixtures are located in `tests/fixtures/`:
- `sample_openapi.yaml` - Sample OpenAPI 3.0 specification
- `sample_response.json` - Sample JSON response with nested data
- `mock_graphql_schema.json` - Mock GraphQL introspection response

## Mocking Strategy

Integration tests use mocking for:
- **HTTP requests** - Mock async HTTP client for GraphQL introspection
- **External APIs** - Avoid dependency on external services
- **File system** - Use temporary directories for output

## Performance Thresholds

Default performance thresholds (configurable in `conftest.py`):
- Parse time: < 5 seconds
- Generate time: < 10 seconds
- Total time: < 15 seconds

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- No external dependencies required
- All network calls are mocked
- Temporary directories are cleaned up
- Exit codes indicate success/failure

## Adding New Tests

When adding new integration tests:

1. **Follow the pattern**: Use the existing test structure
2. **Use fixtures**: Leverage shared fixtures from `conftest.py`
3. **Mock external calls**: Don't depend on external services
4. **Clean up**: Use temporary directories that auto-cleanup
5. **Document**: Add docstrings explaining what the test verifies
6. **Performance**: Add performance benchmarks for new features
7. **Error handling**: Test both success and failure paths

## Example Test Structure

```python
@pytest.mark.asyncio
async def test_feature_name(self, temp_output_dir: Path, fixture_name: Dict[str, Any]):
    """Test description explaining what is being verified."""
    # Arrange: Set up test data
    input_file = temp_output_dir / "input.json"
    with open(input_file, "w") as f:
        json.dump(fixture_name, f)
    
    # Act: Execute the feature
    args = create_parser().parse_args([
        "--api", str(input_file),
        "--output", str(temp_output_dir / "generated")
    ])
    orchestrator = AutoSentinel(args)
    result = await orchestrator.run()
    
    # Assert: Verify results
    assert result.success
    assert (temp_output_dir / "generated" / "models.py").exists()
```

## Troubleshooting

### Tests fail with import errors
- Ensure all dependencies are installed: `pip install -r requirements-dev.txt`
- Check Python version: Python 3.9+ required

### Tests fail with permission errors
- Check write permissions in test directory
- Temporary directories should auto-cleanup

### Tests are slow
- Check performance thresholds in `conftest.py`
- Ensure mocking is working (no real HTTP calls)
- Run with `-v` flag to see which tests are slow

### Tests fail intermittently
- Check for race conditions in async code
- Ensure proper cleanup between tests
- Check for shared state between tests

## Future Enhancements

Planned improvements for integration tests:
- [ ] Real-world API testing (optional, with flag)
- [ ] Load testing with large specifications
- [ ] Parallel test execution
- [ ] Visual regression testing for generated docs
- [ ] Integration with external validation tools