# Image Insights API Documentation

## Base URL

```
http://localhost:8080
```

---

## Endpoints

### Health Check

#### `GET /`

Root endpoint for basic health check.

**Response:**
```json
{
  "service": "image-insights-api",
  "version": "1.0.0",
  "status": "healthy"
}
```

#### `GET /health`

Detailed health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "image-insights-api",
  "version": "1.0.0"
}
```

---

### Image Analysis

#### `POST /v1/image/analysis`

Analyze an image and return brightness metrics.

**Request:**

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `image` | file | form-data | Yes | JPEG or PNG image file |
| `metrics` | string | query | No | Comma-separated list of metrics |

**Supported Metrics:**

| Metric | Description |
|--------|-------------|
| `brightness` | Brightness score (0-100) and average luminance. **Default if not specified.** |
| `median` | Median luminance value |
| `histogram` | Distribution of luminance values across 10 buckets |

---

## Usage Examples

### Basic Request (cURL)

```bash
curl -X POST http://localhost:8080/v1/image/analysis \
  -F "image=@photo.jpg"
```

**Response:**
```json
{
  "brightness_score": 73,
  "average_luminance": 186.3,
  "width": 1920,
  "height": 1080,
  "algorithm": "rec709"
}
```

### Request with Specific Metrics

```bash
curl -X POST "http://localhost:8080/v1/image/analysis?metrics=brightness,median" \
  -F "image=@photo.jpg"
```

**Response:**
```json
{
  "brightness_score": 73,
  "average_luminance": 186.3,
  "median_luminance": 172.4,
  "width": 1920,
  "height": 1080,
  "algorithm": "rec709"
}
```

### Request with All Metrics

```bash
curl -X POST "http://localhost:8080/v1/image/analysis?metrics=brightness,median,histogram" \
  -F "image=@photo.jpg"
```

**Response:**
```json
{
  "brightness_score": 73,
  "average_luminance": 186.3,
  "median_luminance": 172.4,
  "histogram": [
    { "range": "0-25", "percent": 2.1 },
    { "range": "26-51", "percent": 5.3 },
    { "range": "52-76", "percent": 8.7 },
    { "range": "77-102", "percent": 12.4 },
    { "range": "103-127", "percent": 15.2 },
    { "range": "128-153", "percent": 18.6 },
    { "range": "154-178", "percent": 14.3 },
    { "range": "179-204", "percent": 10.8 },
    { "range": "205-229", "percent": 7.1 },
    { "range": "230-255", "percent": 5.5 }
  ],
  "width": 1920,
  "height": 1080,
  "algorithm": "rec709"
}
```

### Python Example

```python
import requests

url = "http://localhost:8080/v1/image/analysis"
params = {"metrics": "brightness,median,histogram"}

with open("photo.jpg", "rb") as f:
    response = requests.post(url, params=params, files={"image": f})

data = response.json()
print(f"Brightness Score: {data['brightness_score']}")
print(f"Average Luminance: {data['average_luminance']}")
```

### JavaScript/Node.js Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('image', fs.createReadStream('photo.jpg'));

axios.post('http://localhost:8080/v1/image/analysis?metrics=brightness', form, {
  headers: form.getHeaders()
}).then(response => {
  console.log('Brightness Score:', response.data.brightness_score);
});
```

---

## Response Fields

### Brightness Metric

| Field | Type | Description |
|-------|------|-------------|
| `brightness_score` | integer | Brightness score from 0 (black) to 100 (white) |
| `average_luminance` | float | Average luminance value (0-255) |

### Median Metric

| Field | Type | Description |
|-------|------|-------------|
| `median_luminance` | float | Median luminance value (0-255) |

### Histogram Metric

| Field | Type | Description |
|-------|------|-------------|
| `histogram` | array | Array of 10 bucket objects |
| `histogram[].range` | string | Luminance range (e.g., "0-25") |
| `histogram[].percent` | float | Percentage of pixels in this range |

### Metadata (Always Included)

| Field | Type | Description |
|-------|------|-------------|
| `width` | integer | Original image width in pixels |
| `height` | integer | Original image height in pixels |
| `algorithm` | string | Algorithm used (`rec709`) |

---

## Error Responses

### 400 Bad Request

Invalid or corrupted image file.

```json
{
  "detail": {
    "error": "Invalid or corrupted image file",
    "details": "cannot identify image file"
  }
}
```

Empty file uploaded.

```json
{
  "detail": {
    "error": "Empty image file"
  }
}
```

Invalid metrics requested.

```json
{
  "detail": {
    "error": "Invalid metrics requested",
    "invalid_metrics": ["invalid_metric"],
    "valid_metrics": ["brightness", "median", "histogram"]
  }
}
```

### 413 Payload Too Large

File exceeds 5MB limit.

```json
{
  "detail": {
    "error": "Image exceeds maximum allowed size (5MB)",
    "max_size_bytes": 5242880,
    "received_size_bytes": 6291456
  }
}
```

### 415 Unsupported Media Type

Unsupported image format.

```json
{
  "detail": {
    "error": "Unsupported image type",
    "allowed_types": ["image/jpeg", "image/png"],
    "received_type": "image/gif"
  }
}
```

### 422 Unprocessable Entity

Missing required `image` field.

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "image"],
      "msg": "Field required"
    }
  ]
}
```

### 500 Internal Server Error

Unexpected server error.

```json
{
  "error": "Internal server error",
  "details": "..."
}
```

---

## Algorithm

The API uses the **ITU-R BT.709 (Rec. 709)** standard for perceptual luminance calculation:

```
L = 0.2126 × R + 0.7152 × G + 0.0722 × B
```

This formula weights green more heavily than red or blue, matching human visual perception.

### Brightness Score Calculation

```
brightness_score = round((average_luminance / 255) × 100)
```

| Score | Interpretation |
|-------|----------------|
| 0 | Pure black |
| 25 | Very dark |
| 50 | Medium gray |
| 75 | Bright |
| 100 | Pure white |

---

## Constraints

| Constraint | Value |
|------------|-------|
| Maximum file size | 5 MB |
| Supported formats | JPEG, PNG |
| Maximum dimension | 512 px (auto-resized) |
| Request timeout | 2 seconds |

**Note:** Images larger than 512px in either dimension are automatically resized while preserving aspect ratio. Original dimensions are reported in the response.

---

## Interactive Documentation

When the API is running, interactive documentation is available at:

- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc
- **OpenAPI JSON:** http://localhost:8080/openapi.json
