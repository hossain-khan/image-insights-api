# PRD: Image Analysis API

## 1. Overview

**Product Name:** Image Insights API
**Repository:** `image-insights-api`
**Type:** Stateless REST microservice
**Deployment:** Docker / OCI-compatible runtime

The Image Analysis API provides fast, deterministic image analysis metrics via a simple REST interface. The initial release focuses on perceptual brightness (darkness) analysis, with a clear path to expand into additional image quality and computer vision tools.

---

## 2. Goals & Non-Goals

### Goals

* Provide accurate perceptual brightness scoring
* Be lightweight, fast, and portable
* Require zero external dependencies (no DB, no cloud services)
* Be easy to extend with new analysis metrics

### Non-Goals

* No user authentication (v1)
* No persistent storage
* No ML model hosting (v1)

---

## 3. API Requirements

### Endpoint

**Upload-based analysis:**
```
POST /v1/image/analysis
```

**URL-based analysis:**
```
POST /v1/image/analysis/url
```

### Request

* Content-Type: `multipart/form-data` (for upload) or `application/json` (for URL)
* Field: `image` (JPEG or PNG) for upload, or JSON body with `url` field
* Optional query parameters (upload) or JSON fields (URL):

  * `metrics` (comma-separated)

    * `brightness` (default)
    * `median`
    * `histogram`
  * `edge_mode` (optional)

    * `left_right`
    * `top_bottom`
    * `all`

### Response

* JSON
* Deterministic output
* Includes metadata

Example:

```json
{
  "brightness_score": 73,
  "average_luminance": 186.3,
  "median_luminance": 172.4,
  "histogram": [...],
  "width": 512,
  "height": 341,
  "algorithm": "rec709"
}
```

---

## 4. Brightness Algorithm

* Convert image to RGB
* Apply Rec. 709 luminance formula:

  ```
  L = 0.2126R + 0.7152G + 0.0722B
  ```
* Compute average luminance
* Normalize to scale 0–100

---

## 5. Performance & Accuracy

### Image Resizing

* Max dimension: **512px**
* Aspect ratio preserved
* High-quality resampling

### Expected Performance

* < 100ms for typical images
* < 2s hard timeout

---

## 6. Safety & Validation

| Rule            | Value     |
| --------------- | --------- |
| Max file size   | 5MB       |
| Allowed formats | JPEG, PNG |
| Timeout         | 2 seconds |
| Error format    | JSON      |

---

## 7. Architecture

### Tech Stack

* Python 3.10+
* FastAPI
* Pillow
* NumPy
* Uvicorn

### Deployment

* Docker container
* No environment-specific configuration
* Exposes port `8080`

---

## 8. Extensibility Strategy

* Metric-based internal modules
* Query-driven metric selection
* Versioned API (`/v1`)
* No breaking changes in minor releases

Planned future metrics:

* Contrast
* Sharpness / blur detection
* Dominant color extraction
* Edge density

---

## 9. Deliverables

* Fully working Docker container
* OpenAPI documentation
* README with usage examples
* URL-based image analysis with SSRF protection
* Edge-based brightness analysis
* Production-safe defaults

---

## 10. Success Criteria

* Can be deployed locally with one `docker run`
* Handles invalid inputs gracefully
* Produces consistent brightness scores across environments
* Easy to add a new metric in under 1 hour

