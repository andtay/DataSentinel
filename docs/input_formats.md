# Input Formats Guide

DataSentinel supports three industry-standard input formats for API specifications. This guide explains each format in detail.

## Table of Contents

1. [Overview](#overview)
2. [JSON Inference](#json-inference)
3. [OpenAPI/Swagger](#openapiswagger)
4. [GraphQL](#graphql)
5. [Format Comparison](#format-comparison)
6. [Best Practices](#best-practices)

---

## Overview

DataSentinel automatically detects the input format based on:
- File extension (`.yaml`, `.yml`, `.json`)
- URL patterns (`/graphql`, `/swagger`, `/openapi`)
- Content structure

You can also explicitly specify the format using the `--format` flag.

---

## JSON Inference

### What is JSON Inference?

JSON inference analyzes sample JSON responses to automatically infer data types, structures, and validation rules. This is ideal when you don't have a formal API specification.

### When to Use

- ✅ No OpenAPI/GraphQL specification available
- ✅ Quick prototyping and exploration
- ✅ Legacy APIs without documentation
- ✅ REST APIs with JSON responses

### How It Works

1. **Fetch or Load** - Retrieves JSON from URL or file
2. **Analyze Structure** - Identifies objects, arrays, and primitives
3. **Infer Types** - Determines data types for each field
4. **Detect Patterns** - Recognizes emails, URLs, UUIDs, dates
5. **Generate Schema** - Creates normalized API schema

### Usage Examples

#### From URL Endpoint

```bash
python auto_sentinel.py \
  --api https://api.example.com/users \
  --format json
```

#### From Local File

```bash
python auto_sentinel.py \
  --api ./samples/user-response.json \
  --format json
```

#### With Authentication

```bash
python auto_sentinel.py \
  --api https://api.example.com/protected/data \
  --format json \
  --auth-type bearer \
  --auth-token YOUR_TOKEN
```

### Type Inference Rules

DataSentinel uses sophisticated pattern matching to infer types:

| Pattern | Inferred Type | Example |
|---------|---------------|---------|
| Integer | `int` | `42`, `-10`, `0` |
| Float | `float` | `3.14`, `-0.5`, `1.0` |
| Boolean | `bool` | `true`, `false` |
| Email | `EmailStr` | `user@example.com` |
| URL | `HttpUrl` | `https://example.com` |
| UUID | `UUID` | `550e8400-e29b-41d4-a716-446655440000` |
| ISO DateTime | `datetime` | `2024-01-15T10:30:00Z` |
| Date | `date` | `2024-01-15` |
| String | `str` | Any other string |

### Sample JSON Structure

```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "age": 30,
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "profile": {
        "bio": "Software engineer",
        "website": "https://johndoe.com"
      },
      "tags": ["developer", "python"]
    }
  ]
}
```

### Generated Schema

From the above JSON, DataSentinel generates:

**Models:**
- `User` - Main user model
- `Profile` - Nested profile model

**Fields with Validation:**
- `id: int` - Integer field
- `name: str` - String with min/max length
- `email: EmailStr` - Email validation
- `age: int` - Integer with range validation
- `is_active: bool` - Boolean field
- `created_at: datetime` - DateTime parsing
- `profile: Profile` - Nested model reference
- `tags: List[str]` - Array of strings

### Limitations

- ⚠️ **Single Sample** - Infers from one response (use multiple samples for better accuracy)
- ⚠️ **Optional Fields** - May not detect all optional fields
- ⚠️ **Complex Validation** - Cannot infer business logic constraints
- ⚠️ **Relationships** - May not capture all model relationships

### Tips for Better Inference

1. **Use Representative Data** - Include all field variations
2. **Multiple Samples** - Provide diverse examples
3. **Complete Records** - Include all possible fields
4. **Edge Cases** - Include null values and empty arrays

---

## OpenAPI/Swagger

### What is OpenAPI?

OpenAPI (formerly Swagger) is a specification for describing RESTful APIs. It provides a deterministic, machine-readable format for API documentation.

### When to Use

- ✅ Formal API specification exists
- ✅ Need precise validation rules
- ✅ API has complex schemas
- ✅ Multiple endpoints and operations

### Supported Versions

- ✅ **OpenAPI 3.0.x** - Full support
- ✅ **OpenAPI 3.1.x** - Full support
- ✅ **Swagger 2.0** - Full support

### Usage Examples

#### From YAML File

```bash
python auto_sentinel.py \
  --api ./specs/openapi.yaml \
  --format openapi
```

#### From JSON File

```bash
python auto_sentinel.py \
  --api ./specs/swagger.json \
  --format openapi
```

#### From URL

```bash
python auto_sentinel.py \
  --api https://api.example.com/openapi.json \
  --format openapi
```

### Sample OpenAPI Specification

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
servers:
  - url: https://api.example.com/v1
paths:
  /users:
    get:
      summary: List users
      operationId: listUsers
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
    post:
      summary: Create user
      operationId: createUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      required:
        - id
        - name
        - email
      properties:
        id:
          type: integer
        name:
          type: string
          minLength: 1
          maxLength: 100
        email:
          type: string
          format: email
        age:
          type: integer
          minimum: 0
          maximum: 150
    UserCreate:
      type: object
      required:
        - name
        - email
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 100
        email:
          type: string
          format: email
```

### Features Supported

#### Schema Features
- ✅ Object types
- ✅ Array types
- ✅ Primitive types (string, integer, number, boolean)
- ✅ Enums
- ✅ Nested objects
- ✅ $ref references
- ✅ allOf, oneOf, anyOf
- ✅ Discriminators

#### Validation Features
- ✅ Required fields
- ✅ String constraints (minLength, maxLength, pattern)
- ✅ Number constraints (minimum, maximum, multipleOf)
- ✅ Array constraints (minItems, maxItems, uniqueItems)
- ✅ Format validation (email, uri, uuid, date, date-time)
- ✅ Default values

#### Endpoint Features
- ✅ Path parameters
- ✅ Query parameters
- ✅ Request bodies
- ✅ Response schemas
- ✅ Multiple HTTP methods
- ✅ Operation IDs

### Reference Resolution

DataSentinel automatically resolves all `$ref` references:

```yaml
# Internal references
$ref: '#/components/schemas/User'

# External file references
$ref: './schemas/user.yaml'

# URL references
$ref: 'https://api.example.com/schemas/user.json'
```

### Tips for OpenAPI

1. **Use Operation IDs** - Provide clear operation IDs for better naming
2. **Document Everything** - Add descriptions for better generated docs
3. **Validate Spec** - Use tools like Swagger Editor to validate
4. **Version Control** - Keep specs in version control
5. **Examples** - Include examples for better understanding

---

## GraphQL

### What is GraphQL?

GraphQL is a query language for APIs with a strong type system. DataSentinel uses GraphQL introspection to extract the schema.

### When to Use

- ✅ GraphQL API with introspection enabled
- ✅ Need to validate GraphQL responses
- ✅ Want to generate REST-like validators from GraphQL

### Requirements

- ✅ GraphQL endpoint must have introspection enabled
- ✅ Endpoint must be accessible (authentication supported)

### Usage Examples

#### Basic Usage

```bash
python auto_sentinel.py \
  --api https://api.example.com/graphql \
  --format graphql
```

#### With Authentication

```bash
python auto_sentinel.py \
  --api https://api.example.com/graphql \
  --format graphql \
  --auth-type bearer \
  --auth-token YOUR_TOKEN
```

### How It Works

1. **Introspection Query** - Sends GraphQL introspection query
2. **Schema Extraction** - Parses type system
3. **Type Mapping** - Maps GraphQL types to Pydantic
4. **Endpoint Generation** - Converts queries/mutations to REST endpoints

### GraphQL to REST Mapping

| GraphQL | REST Equivalent |
|---------|----------------|
| Query | GET endpoint |
| Mutation | POST endpoint |
| Subscription | WebSocket (not yet supported) |

### Sample GraphQL Schema

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  age: Int
  isActive: Boolean!
  createdAt: DateTime!
}

type Query {
  users: [User!]!
  user(id: ID!): User
}

type Mutation {
  createUser(name: String!, email: String!, age: Int): User!
  updateUser(id: ID!, name: String, email: String): User!
  deleteUser(id: ID!): Boolean!
}

scalar DateTime
```

### Generated Endpoints

From the above schema, DataSentinel generates:

**GET Endpoints:**
- `GET /users` - List all users (from `users` query)
- `GET /user/{id}` - Get user by ID (from `user` query)

**POST Endpoints:**
- `POST /createUser` - Create user (from `createUser` mutation)
- `POST /updateUser` - Update user (from `updateUser` mutation)
- `POST /deleteUser` - Delete user (from `deleteUser` mutation)

### Type Mapping

| GraphQL Type | Pydantic Type |
|--------------|---------------|
| ID | `str` or `int` |
| String | `str` |
| Int | `int` |
| Float | `float` |
| Boolean | `bool` |
| DateTime | `datetime` |
| Date | `date` |
| UUID | `UUID` |
| Custom Scalar | `str` (with note) |

### Custom Scalars

DataSentinel handles custom scalars intelligently:

```graphql
scalar DateTime
scalar UUID
scalar Email
scalar URL
```

These are mapped to appropriate Pydantic types with validation.

### Limitations

- ⚠️ **Introspection Required** - API must allow introspection
- ⚠️ **No Subscriptions** - WebSocket subscriptions not yet supported
- ⚠️ **Directives** - Custom directives may not be fully supported
- ⚠️ **Interfaces/Unions** - Complex type relationships may need manual adjustment

### Tips for GraphQL

1. **Enable Introspection** - Ensure it's enabled in production (or use staging)
2. **Document Types** - Add descriptions to types and fields
3. **Use Standard Scalars** - Stick to common scalar types when possible
4. **Test Queries** - Verify queries work before generating
5. **Authentication** - Provide proper credentials for protected endpoints

---

## Format Comparison

| Feature | JSON Inference | OpenAPI | GraphQL |
|---------|---------------|---------|---------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Accuracy** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Validation Rules** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Documentation** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Setup Required** | None | Spec file | Introspection |
| **Best For** | Quick start | Production APIs | GraphQL APIs |

---

## Best Practices

### Choosing the Right Format

1. **Have OpenAPI Spec?** → Use OpenAPI format
2. **Have GraphQL API?** → Use GraphQL format
3. **No Spec Available?** → Use JSON inference

### Improving Results

#### For JSON Inference
- Provide multiple sample responses
- Include all field variations
- Use representative data

#### For OpenAPI
- Keep spec up to date
- Use validation constraints
- Add descriptions and examples

#### For GraphQL
- Enable introspection
- Document types thoroughly
- Use standard scalar types

### Validation

Always validate generated code:

```bash
# Run generated tests
pytest test_api.py -v

# Check code quality
black models.py validators.py
mypy models.py validators.py
```

---

## Next Steps

- 📖 [Generated Artifacts](generated_artifacts.md) - Understand generated code
- 🚀 [Deployment Guide](deployment.md) - Deploy your service
- 📚 [API Reference](api_reference.md) - Complete API documentation

---

## Need Help?

- 📝 [GitHub Issues](https://github.com/yourusername/datasentinel/issues)
- 💬 [Discussions](https://github.com/yourusername/datasentinel/discussions)
- 📧 Email: support@datasentinel.dev