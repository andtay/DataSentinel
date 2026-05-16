# DataSentinel Examples

This directory contains example API specifications and usage demonstrations for DataSentinel.

## Directory Structure

```
examples/
├── openapi/          # OpenAPI/Swagger examples
├── graphql/          # GraphQL examples
├── json/             # JSON inference examples
└── README.md         # This file
```

## Quick Start Examples

### 1. OpenAPI Example

Generate validation service from OpenAPI specification:

```bash
python auto_sentinel.py \
  --api examples/openapi/petstore.yaml \
  --output ./output/petstore \
  --verbose
```

### 2. GraphQL Example

Generate from GraphQL endpoint (requires introspection):

```bash
python auto_sentinel.py \
  --api https://api.spacex.land/graphql \
  --format graphql \
  --output ./output/spacex \
  --verbose
```

### 3. JSON Example

Generate from JSON sample:

```bash
python auto_sentinel.py \
  --api examples/json/user_sample.json \
  --format json \
  --output ./output/users \
  --verbose
```

## Example Specifications

### OpenAPI Examples

- **petstore.yaml** - Classic Petstore API (OpenAPI 3.0)
- **meteomatics_swagger_definition.yaml.txt** - Real-world weather API

### GraphQL Examples

- **github_graphql.txt** - GitHub GraphQL schema example
- Public endpoints that support introspection

### JSON Examples

- **user_sample.json** - User data with nested structures
- **product_sample.json** - E-commerce product data

## Testing Examples

After generating code, test it:

```bash
cd output/petstore
pip install -r requirements.txt
pytest test_api.py -v
uvicorn app:app --reload
```

## Real-World APIs

### Public APIs for Testing

1. **JSONPlaceholder** (JSON)
   ```bash
   python auto_sentinel.py \
     --api https://jsonplaceholder.typicode.com/users \
     --output ./output/jsonplaceholder
   ```

2. **SpaceX GraphQL** (GraphQL)
   ```bash
   python auto_sentinel.py \
     --api https://api.spacex.land/graphql \
     --format graphql \
     --output ./output/spacex
   ```

3. **Swagger Petstore** (OpenAPI)
   ```bash
   python auto_sentinel.py \
     --api https://petstore.swagger.io/v2/swagger.json \
     --output ./output/petstore
   ```

## Custom Examples

### Creating Your Own Examples

1. **For OpenAPI:**
   - Create a YAML or JSON file following OpenAPI 3.0 spec
   - Include schemas, paths, and components
   - Add validation constraints

2. **For GraphQL:**
   - Ensure your endpoint has introspection enabled
   - Test with GraphQL Playground first
   - Provide authentication if needed

3. **For JSON:**
   - Create representative JSON samples
   - Include all field variations
   - Use realistic data types

## Example Workflows

### Workflow 1: API Exploration

```bash
# 1. Fetch sample data
curl https://api.example.com/users > examples/json/api_sample.json

# 2. Generate validation service
python auto_sentinel.py \
  --api examples/json/api_sample.json \
  --output ./output/api_validator

# 3. Test generated code
cd output/api_validator
pytest test_api.py -v
```

### Workflow 2: OpenAPI Integration

```bash
# 1. Download OpenAPI spec
curl https://api.example.com/openapi.json > examples/openapi/api_spec.json

# 2. Generate with authentication
python auto_sentinel.py \
  --api examples/openapi/api_spec.json \
  --output ./output/api_validator \
  --auth-type bearer \
  --auth-token $API_TOKEN

# 3. Deploy with Docker
cd output/api_validator
docker build -t api-validator .
docker run -p 8000:8000 api-validator
```

### Workflow 3: GraphQL Schema

```bash
# 1. Generate from GraphQL endpoint
python auto_sentinel.py \
  --api https://api.example.com/graphql \
  --format graphql \
  --output ./output/graphql_validator \
  --auth-type bearer \
  --auth-token $GRAPHQL_TOKEN

# 2. Run generated service
cd output/graphql_validator
uvicorn app:app --reload

# 3. Test validation
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "name": "Test"}'
```

## Tips for Examples

### Best Practices

1. **Use Representative Data**
   - Include all field types
   - Show optional and required fields
   - Include nested structures

2. **Add Documentation**
   - Comment your examples
   - Explain special cases
   - Document authentication needs

3. **Test Thoroughly**
   - Verify generated code works
   - Test edge cases
   - Check error handling

### Common Patterns

#### Nested Objects
```json
{
  "user": {
    "id": 1,
    "profile": {
      "name": "John",
      "email": "john@example.com"
    }
  }
}
```

#### Arrays
```json
{
  "users": [
    {"id": 1, "name": "John"},
    {"id": 2, "name": "Jane"}
  ]
}
```

#### Optional Fields
```json
{
  "id": 1,
  "name": "John",
  "email": "john@example.com",
  "phone": null,
  "address": {
    "street": "123 Main St",
    "city": "Springfield"
  }
}
```

## Troubleshooting

### Example Not Working?

1. **Check Format**
   - Verify JSON is valid
   - Ensure OpenAPI spec is valid
   - Test GraphQL endpoint manually

2. **Authentication Issues**
   - Verify credentials are correct
   - Check token hasn't expired
   - Ensure proper auth type

3. **Generation Fails**
   - Run with `--verbose` flag
   - Check error messages
   - Verify input file exists

## Contributing Examples

Want to add your own examples?

1. Create example file in appropriate directory
2. Add README section describing it
3. Test generation works
4. Submit pull request

## Resources

- [OpenAPI Specification](https://swagger.io/specification/)
- [GraphQL Documentation](https://graphql.org/learn/)
- [JSON Schema](https://json-schema.org/)
- [DataSentinel Docs](../docs/)

## Need Help?

- 📝 [GitHub Issues](https://github.com/yourusername/datasentinel/issues)
- 💬 [Discussions](https://github.com/yourusername/datasentinel/discussions)
- 📖 [Documentation](../docs/getting_started.md)