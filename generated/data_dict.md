# Query API - Data Dictionary

**Version:** 1.0.0  
**Base URL:** https://rickandmortyapi.com  
**Generated:** 2026-05-17T11:16:29.415525Z

## Description

GraphQL API

---

## Table of Contents

- [Overview](#overview)
- [Data Models](#data-models)
  - [Query](#query)
  - [Character](#character)
  - [Location](#location)
  - [Episode](#episode)
  - [FilterCharacter](#filtercharacter)
  - [Characters](#characters)
  - [Info](#info)
  - [FilterLocation](#filterlocation)
  - [FilterEpisode](#filterepisode)
- [API Endpoints](#api-endpoints)
  - [GET /query/character](#get-query-character)
  - [GET /query/characters](#get-query-characters)
  - [GET /query/charactersByIds](#get-query-charactersByIds)
  - [GET /query/location](#get-query-location)
  - [GET /query/locations](#get-query-locations)
  - [GET /query/locationsByIds](#get-query-locationsByIds)
  - [GET /query/episode](#get-query-episode)
  - [GET /query/episodes](#get-query-episodes)
  - [GET /query/episodesByIds](#get-query-episodesByIds)

---

## Overview

This document provides a comprehensive data dictionary for the Query API API. It includes detailed information about all data models, fields, validation rules, and API endpoints.

### Statistics

- **Total Models:** 9
- **Total Endpoints:** 9
- **Total Fields:** 48

---

## Data Models

### Query


**Fields:** 9

| Field Name | Type | Required | Description | Constraints | Example |
|------------|------|----------|-------------|-------------|---------|
| `character` | [Character](#character) | ✗ | Get a specific character by ID | None | N/A |
| `characters` | [Characters](#characters) | ✗ | Get the list of all characters | None | N/A |
| `characters_by_ids` | array[string] | ✗ | Get a list of characters selected by ids | None | N/A |
| `location` | [Location](#location) | ✗ | Get a specific locations by ID | None | N/A |
| `locations` | [Locations](#locations) | ✗ | Get the list of all locations | None | N/A |
| `locations_by_ids` | array[string] | ✗ | Get a list of locations selected by ids | None | N/A |
| `episode` | [Episode](#episode) | ✗ | Get a specific episode by ID | None | N/A |
| `episodes` | [Episodes](#episodes) | ✗ | Get the list of all episodes | None | N/A |
| `episodes_by_ids` | array[string] | ✗ | Get a list of episodes selected by ids | None | N/A |


---

### Character


**Fields:** 11

| Field Name | Type | Required | Description | Constraints | Example |
|------------|------|----------|-------------|-------------|---------|
| `id` | string | ✗ | The id of the character. | None | N/A |
| `name` | string | ✗ | The name of the character. | None | N/A |
| `status` | string | ✗ | The status of the character ('Alive', 'Dead' or 'unknown'). | None | N/A |
| `species` | string | ✗ | The species of the character. | None | N/A |
| `type` | string | ✗ | The type or subspecies of the character. | None | N/A |
| `gender` | string | ✗ | The gender of the character ('Female', 'Male', 'Genderless' or 'unknown'). | None | N/A |
| `origin` | [Location](#location) | ✗ | The character's origin location | None | N/A |
| `location` | [Location](#location) | ✗ | The character's last known location | None | N/A |
| `image` | string | ✗ | Link to the character's image.
All images are 300x300px and most are medium shots or portraits since they are intended to be used as avatars. | None | N/A |
| `episode` | array[string] | ✓ | Episodes in which this character appeared. | None | N/A |
| `created` | string | ✗ | Time at which the character was created in the database. | None | N/A |


---

### Location


**Fields:** 6

| Field Name | Type | Required | Description | Constraints | Example |
|------------|------|----------|-------------|-------------|---------|
| `id` | string | ✗ | The id of the location. | None | N/A |
| `name` | string | ✗ | The name of the location. | None | N/A |
| `type` | string | ✗ | The type of the location. | None | N/A |
| `dimension` | string | ✗ | The dimension in which the location is located. | None | N/A |
| `residents` | array[string] | ✓ | List of characters who have been last seen in the location. | None | N/A |
| `created` | string | ✗ | Time at which the location was created in the database. | None | N/A |


---

### Episode


**Fields:** 6

| Field Name | Type | Required | Description | Constraints | Example |
|------------|------|----------|-------------|-------------|---------|
| `id` | string | ✗ | The id of the episode. | None | N/A |
| `name` | string | ✗ | The name of the episode. | None | N/A |
| `air_date` | string | ✗ | The air date of the episode. | None | N/A |
| `episode` | string | ✗ | The code of the episode. | None | N/A |
| `characters` | array[string] | ✓ | List of characters who have been seen in the episode. | None | N/A |
| `created` | string | ✗ | Time at which the episode was created in the database. | None | N/A |


---

### FilterCharacter


**Fields:** 5

| Field Name | Type | Required | Description | Constraints | Example |
|------------|------|----------|-------------|-------------|---------|
| `name` | string | ✗ | N/A | None | N/A |
| `status` | string | ✗ | N/A | None | N/A |
| `species` | string | ✗ | N/A | None | N/A |
| `type` | string | ✗ | N/A | None | N/A |
| `gender` | string | ✗ | N/A | None | N/A |


---

### Characters


**Fields:** 2

| Field Name | Type | Required | Description | Constraints | Example |
|------------|------|----------|-------------|-------------|---------|
| `info` | [Info](#info) | ✗ | N/A | None | N/A |
| `results` | array[string] | ✗ | N/A | None | N/A |


---

### Info


**Fields:** 4

| Field Name | Type | Required | Description | Constraints | Example |
|------------|------|----------|-------------|-------------|---------|
| `count` | integer | ✗ | The length of the response. | None | N/A |
| `pages` | integer | ✗ | The amount of pages. | None | N/A |
| `next` | integer | ✗ | Number of the next page (if it exists) | None | N/A |
| `prev` | integer | ✗ | Number of the previous page (if it exists) | None | N/A |


---

### FilterLocation


**Fields:** 3

| Field Name | Type | Required | Description | Constraints | Example |
|------------|------|----------|-------------|-------------|---------|
| `name` | string | ✗ | N/A | None | N/A |
| `type` | string | ✗ | N/A | None | N/A |
| `dimension` | string | ✗ | N/A | None | N/A |


---

### FilterEpisode


**Fields:** 2

| Field Name | Type | Required | Description | Constraints | Example |
|------------|------|----------|-------------|-------------|---------|
| `name` | string | ✗ | N/A | None | N/A |
| `episode` | string | ✗ | N/A | None | N/A |


---


## API Endpoints

### GET /query/character

**Summary:** character

**Description:** Get a specific character by ID

**Method:** `GET`  
**Path:** `/query/character`  
**Operation ID:** `character`  
**Tags:** query  
**Authentication Required:** Yes  

#### Parameters

| Name | Location | Type | Required | Description | Constraints |
|------|----------|------|----------|-------------|-------------|
| `id` | query | string | ✓ | N/A | None |


#### Response

**Model:** [`Character`](#character)


#### Example Request

```bash
curl -X GET \
  "https://rickandmortyapi.com/query/character" \
```

---

### GET /query/characters

**Summary:** characters

**Description:** Get the list of all characters

**Method:** `GET`  
**Path:** `/query/characters`  
**Operation ID:** `characters`  
**Tags:** query  
**Authentication Required:** Yes  

#### Parameters

| Name | Location | Type | Required | Description | Constraints |
|------|----------|------|----------|-------------|-------------|
| `page` | query | integer | ✗ | N/A | None |
| `filter` | query | string | ✗ | N/A | None |


#### Response

**Model:** [`Characters`](#characters)


#### Example Request

```bash
curl -X GET \
  "https://rickandmortyapi.com/query/characters" \
```

---

### GET /query/charactersByIds

**Summary:** charactersByIds

**Description:** Get a list of characters selected by ids

**Method:** `GET`  
**Path:** `/query/charactersByIds`  
**Operation ID:** `charactersByIds`  
**Tags:** query  
**Authentication Required:** Yes  

#### Parameters

| Name | Location | Type | Required | Description | Constraints |
|------|----------|------|----------|-------------|-------------|
| `ids` | query | array | ✓ | N/A | None |


#### Response

**Model:** [`Character`](#character)


#### Example Request

```bash
curl -X GET \
  "https://rickandmortyapi.com/query/charactersByIds" \
```

---

### GET /query/location

**Summary:** location

**Description:** Get a specific locations by ID

**Method:** `GET`  
**Path:** `/query/location`  
**Operation ID:** `location`  
**Tags:** query  
**Authentication Required:** Yes  

#### Parameters

| Name | Location | Type | Required | Description | Constraints |
|------|----------|------|----------|-------------|-------------|
| `id` | query | string | ✓ | N/A | None |


#### Response

**Model:** [`Location`](#location)


#### Example Request

```bash
curl -X GET \
  "https://rickandmortyapi.com/query/location" \
```

---

### GET /query/locations

**Summary:** locations

**Description:** Get the list of all locations

**Method:** `GET`  
**Path:** `/query/locations`  
**Operation ID:** `locations`  
**Tags:** query  
**Authentication Required:** Yes  

#### Parameters

| Name | Location | Type | Required | Description | Constraints |
|------|----------|------|----------|-------------|-------------|
| `page` | query | integer | ✗ | N/A | None |
| `filter` | query | string | ✗ | N/A | None |


#### Response

**Model:** [`Locations`](#locations)


#### Example Request

```bash
curl -X GET \
  "https://rickandmortyapi.com/query/locations" \
```

---

### GET /query/locationsByIds

**Summary:** locationsByIds

**Description:** Get a list of locations selected by ids

**Method:** `GET`  
**Path:** `/query/locationsByIds`  
**Operation ID:** `locationsByIds`  
**Tags:** query  
**Authentication Required:** Yes  

#### Parameters

| Name | Location | Type | Required | Description | Constraints |
|------|----------|------|----------|-------------|-------------|
| `ids` | query | array | ✓ | N/A | None |


#### Response

**Model:** [`Location`](#location)


#### Example Request

```bash
curl -X GET \
  "https://rickandmortyapi.com/query/locationsByIds" \
```

---

### GET /query/episode

**Summary:** episode

**Description:** Get a specific episode by ID

**Method:** `GET`  
**Path:** `/query/episode`  
**Operation ID:** `episode`  
**Tags:** query  
**Authentication Required:** Yes  

#### Parameters

| Name | Location | Type | Required | Description | Constraints |
|------|----------|------|----------|-------------|-------------|
| `id` | query | string | ✓ | N/A | None |


#### Response

**Model:** [`Episode`](#episode)


#### Example Request

```bash
curl -X GET \
  "https://rickandmortyapi.com/query/episode" \
```

---

### GET /query/episodes

**Summary:** episodes

**Description:** Get the list of all episodes

**Method:** `GET`  
**Path:** `/query/episodes`  
**Operation ID:** `episodes`  
**Tags:** query  
**Authentication Required:** Yes  

#### Parameters

| Name | Location | Type | Required | Description | Constraints |
|------|----------|------|----------|-------------|-------------|
| `page` | query | integer | ✗ | N/A | None |
| `filter` | query | string | ✗ | N/A | None |


#### Response

**Model:** [`Episodes`](#episodes)


#### Example Request

```bash
curl -X GET \
  "https://rickandmortyapi.com/query/episodes" \
```

---

### GET /query/episodesByIds

**Summary:** episodesByIds

**Description:** Get a list of episodes selected by ids

**Method:** `GET`  
**Path:** `/query/episodesByIds`  
**Operation ID:** `episodesByIds`  
**Tags:** query  
**Authentication Required:** Yes  

#### Parameters

| Name | Location | Type | Required | Description | Constraints |
|------|----------|------|----------|-------------|-------------|
| `ids` | query | array | ✓ | N/A | None |


#### Response

**Model:** [`Episode`](#episode)


#### Example Request

```bash
curl -X GET \
  "https://rickandmortyapi.com/query/episodesByIds" \
```

---



## Field Type Reference

| Type | Description | Python Type | Validation |
|------|-------------|-------------|------------|
| `string` | Text string | `str` | Length, pattern |
| `integer` | Whole number | `int` | Min/max value |
| `float` | Decimal number | `float` | Min/max value |
| `boolean` | True/False value | `bool` | N/A |
| `array` | List of items | `list` | Min/max items |
| `object` | Nested object | `dict` | Additional properties |
| `date` | Date (YYYY-MM-DD) | `date` | Format |
| `datetime` | Date and time (ISO 8601) | `datetime` | Format |
| `uuid` | UUID string | `UUID` | Format |
| `email` | Email address | `EmailStr` | Format |
| `url` | URL string | `HttpUrl` | Format |

---

## Validation Rules

### String Validation

- **min_length**: Minimum string length
- **max_length**: Maximum string length
- **pattern**: Regular expression pattern

### Numeric Validation

- **min_value** (ge): Minimum value (greater than or equal)
- **max_value** (le): Maximum value (less than or equal)
- **multiple_of**: Value must be a multiple of this number

### Array Validation

- **min_items**: Minimum number of items
- **max_items**: Maximum number of items
- **unique_items**: Whether items must be unique

### Enum Validation

- **enum_values**: List of allowed values

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request

Invalid request parameters or body.

```json
{
  "error": "Bad Request",
  "message": "Invalid parameter value",
  "details": {}
}
```

### 401 Unauthorized

Authentication required or failed.

```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

### 404 Not Found

Resource not found.

```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 422 Unprocessable Entity

Validation failed.

```json
{
  "error": "Validation failed",
  "message": "Response validation failed: 2 errors",
  "details": [
    {
      "loc": ["field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

Server error.

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## Changelog

### Version 1.0.0

- Initial data dictionary generation
- 9 models documented
- 9 endpoints documented

---

**Generated by DataSentinel** | 2026-05-17T11:16:29.415525Z