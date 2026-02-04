# Cloudflare Containers Deployment Guide

This directory contains the configuration for deploying **Image Insights API** to **Cloudflare Containers**.

**Official Documentation:**
- [Cloudflare Containers Documentation](https://developers.cloudflare.com/containers/)
- [Architecture & Concepts](https://developers.cloudflare.com/containers/architecture/)
- [Configuration Reference](https://developers.cloudflare.com/containers/configuration/)
- [Deployment Guide](https://developers.cloudflare.com/containers/deploy/)

## Architecture Overview

The deployment consists of:

1. **Cloudflare Worker** (`src/index.ts`) - Entry point that routes requests globally
2. **Container Instance** (FastAPI app) - Processes image analysis requests
3. **Durable Object** - Manages container lifecycle and state
4. **Cloudflare Container Registry** - Stores the Docker image

```
User Request
    ↓
Cloudflare Edge (global)
    ↓
Worker (fast HTTP routing)
    ↓
Durable Object (lifecycle management)
    ↓
Container Instance (FastAPI on port 8080)
    ↓
Response (brightness analysis results)
```

## Prerequisites

Before deploying, ensure you have:

- **Docker** installed and running locally
  - Verify: `docker info`
- **Node.js** and **npm** installed
  - Verify: `node --version && npm --version`
- **Wrangler CLI** installed
  - Install: `npm install -g wrangler@latest`
- **Cloudflare Account** on Workers Paid plan
  - Sign up: https://dash.cloudflare.com/
- **Cloudflare API Token** with Workers permissions
  - Create: https://dash.cloudflare.com/profile/api-tokens

### Setup Cloudflare Authentication

```bash
# Authenticate with Cloudflare
wrangler login

# Or set environment variables
export CLOUDFLARE_API_TOKEN=<your_token>
export CLOUDFLARE_ACCOUNT_ID=<your_account_id>
```

## Project Structure

```
.
├── src/
│   └── index.ts                 # Worker entry point
├── app/                          # Python FastAPI application (unchanged)
│   ├── __version__.py
│   ├── main.py
│   ├── api/
│   └── core/
├── Dockerfile                    # Container image definition
├── wrangler.toml                 # Workers & Containers configuration
├── package.json                  # Node.js dependencies
├── tsconfig.json                 # TypeScript configuration
├── .dockerignore                 # Files to exclude from Docker image
└── README.md
```

## Configuration Files

### `wrangler.toml`

Main configuration for Workers and Containers:

- **Container Configuration**
  - `image`: Path to Dockerfile
  - `class_name`: Durable Object class name
  - `instance_type`: `basic` (recommended for image processing)
  - `max_instances`: Maximum concurrent instances (default: 10)

- **Durable Objects**
  - Binding name: `IMAGE_INSIGHTS_CONTAINER`
  - Maps to: `ImageInsightsContainer` class

- **Migrations**
  - Required for container-enabled Durable Objects
  - Tracks schema changes during updates

### `src/index.ts`

### `src/index.ts`

Worker entry point that:

- Defines `ImageInsightsContainer` class configuration
- Implements `fetch()` handler to route requests
- Manages container lifecycle (startup, shutdown, errors)
- Handles error cases gracefully

**References:**
- [Container Lifecycle Events](https://developers.cloudflare.com/containers/configuration/lifecycle-events/)
- [Request Handling](https://developers.cloudflare.com/workers/runtime-apis/request/)
- [Error Handling](https://developers.cloudflare.com/workers/platform/errors/)

### `wrangler.toml`

Cloudflare configuration specifying:

- Container image location and class name
- Instance type (basic: 1/4 vCPU, 1 GiB RAM, 4 GB disk)
- Maximum number of concurrent instances (10)
- Durable Object bindings and migrations

**References:**
- [Wrangler Configuration](https://developers.cloudflare.com/workers/wrangler/configuration/)
- [Container Reference](https://developers.cloudflare.com/containers/reference/configuration/)
- [Durable Objects Configuration](https://developers.cloudflare.com/durable-objects/configuration/)

### `package.json`

Dependencies:
- `@cloudflare/containers`: Container class and helpers
- `wrangler`: Cloudflare CLI ([Wrangler Documentation](https://developers.cloudflare.com/workers/wrangler/))
- `@cloudflare/workers-types`: TypeScript types for Workers ([Types Reference](https://developers.cloudflare.com/workers/runtime-apis/))

## Local Development

### Install Dependencies

```bash
npm install
```

### Run Local Development Server

```bash
npm run dev
# or
wrangler dev
```

This will:
1. Build the Docker image
2. Start a local Wrangler dev server (usually `http://localhost:8787`)
3. Spin up a container instance
4. Make the FastAPI app available through the Worker

**Reference:** [Local Development with Wrangler](https://developers.cloudflare.com/workers/wrangler/commands/#dev)

### Test Locally

While `wrangler dev` is running:

```bash
# Basic health check
curl http://localhost:8787/health

# Analyze an image
curl -X POST http://localhost:8787/v1/image/analysis \
  -F "image=@/path/to/photo.jpg"

# With metrics
curl -X POST "http://localhost:8787/v1/image/analysis?metrics=brightness,median,histogram" \
  -F "image=@/path/to/photo.jpg"
```

### Verify Container is Running

During local development, you can:

```bash
# Check Docker containers
docker ps

# View container logs
docker logs <container_id>
```

## Deployment

### Build and Deploy

```bash
npm run deploy
# or
wrangler deploy
```

**Reference:** [Deploying with Wrangler](https://developers.cloudflare.com/containers/deploy/)

This will:

1. **Build** the Docker image using your Dockerfile
2. **Push** the image to Cloudflare's Container Registry
3. **Deploy** the Worker code
4. **Configure** Durable Objects and migrations

### First Deployment

⚠️ **Important**: The first deployment may take 5-10 minutes because:
- Docker image is being built and pushed
- Container instances are being provisioned globally
- Durable Objects are being initialized

### Monitor Deployment Status

```bash
# Check deployment status
wrangler deployments list

# View container status
wrangler containers list

# View deployed images
wrangler containers images list
```

**Reference:** [Wrangler Commands](https://developers.cloudflare.com/workers/wrangler/commands/) | [Managing Containers](https://developers.cloudflare.com/containers/manage/)

## Production Deployment

After deploying, your API will be available at:

```
https://image-insights-api.<your-account>.workers.dev
```

### Test Production

```bash
# Replace with your actual Workers.dev URL
WORKER_URL="https://image-insights-api.YOUR_ACCOUNT.workers.dev"

# Health check
curl $WORKER_URL/health

# Analyze image
curl -X POST "$WORKER_URL/v1/image/analysis?metrics=brightness" \
  -F "image=@/path/to/photo.jpg"
```

### Monitor Production

**Reference:** [Cloudflare Analytics](https://developers.cloudflare.com/workers/observability/logging/) | [Real-time Logs](https://developers.cloudflare.com/workers/observability/logging/real-time-logs/)

View logs and metrics:

1. **Cloudflare Dashboard**
   - https://dash.cloudflare.com/ → Workers & Pages → image-insights-api
   - View real-time logs and metrics
   - Check error rates and performance

2. **Wrangler CLI**
   ```bash
   # Tail logs
   wrangler tail

   # View specific container logs
   wrangler tail --filter '{ "where": { "ServiceName": "IMAGE_INSIGHTS_CONTAINER" } }'
   ```

   **Reference:** [Wrangler Tail Command](https://developers.cloudflare.com/workers/wrangler/commands/#tail) | [Tail API](https://developers.cloudflare.com/workers/reference/tail-api/)

## Instance Types and Scaling

### Current Configuration: `basic`

- **vCPU**: 1/4 (256 millicores)
- **Memory**: 1 GiB
- **Disk**: 4 GB
- **Cost**: Refer to [Cloudflare Containers Pricing](https://developers.cloudflare.com/containers/platform-details/pricing/)
- **Best for**: Image processing at moderate scale

### Scaling Options

If you need more resources, update `wrangler.toml`:

```toml
# For higher throughput
instance_type = "standard-1"   # 1/2 vCPU, 4 GiB RAM, 8 GB disk

# For very high throughput
instance_type = "standard-2"   # 1 vCPU, 6 GiB RAM, 12 GB disk
```

Increase `max_instances` for more concurrent requests:

```toml
max_instances = 20   # Handle 20 concurrent image analysis requests
```

**Reference:** [Instance Types & Scaling](https://developers.cloudflare.com/containers/platform-details/instance-types/) | [Scaling Guide](https://developers.cloudflare.com/containers/manage/scaling/)

## Environment Variables and Secrets

### Container Environment Variables

Configured in `src/index.ts`:

```typescript
envVars: Record<string, string> = {
  // Configure environment variables based on your needs
  // Example: ENABLE_DETAILED_LOGGING: "true"
};
```

**Reference:** [Container Configuration](https://developers.cloudflare.com/containers/configuration/#environment-variables)

### Secret Bindings

For sensitive data (API keys, etc.), use Wrangler secrets:

```bash
# Set a secret
wrangler secret put MY_SECRET

# Use in Worker code
const secret = env.MY_SECRET;
```

**Reference:** [Secrets Management](https://developers.cloudflare.com/workers/configuration/secrets/) | [Environment Variables](https://developers.cloudflare.com/workers/configuration/environment-variables/)

## Troubleshooting

### Container fails to start

```bash
# Check logs
wrangler tail

# Verify Dockerfile runs on linux/amd64
docker build --platform linux/amd64 .

# Test locally first
wrangler dev
```

**Reference:** [Debugging Workers](https://developers.cloudflare.com/workers/platform/debugging-guide/) | [Tail Logs](https://developers.cloudflare.com/workers/observability/logging/real-time-logs/)

### Image is too large

Cloudflare Container images have a **20 GB limit per image**. The `.dockerignore` file helps reduce size by excluding:

- Testing files and directories
- Git history
- Documentation

**Reference:** [Image Size Limits](https://developers.cloudflare.com/containers/platform-details/limits/)
- Python caches

Current estimated size: ~150-200 MB

### Cold starts are slow

Cold starts (2-3 seconds) are normal for containers. To improve:

1. Increase `max_instances` to keep more running
2. Use a smaller base image (e.g., Python Alpine)
3. Optimize application startup time

**Reference:** [Performance Optimization](https://developers.cloudflare.com/containers/manage/performance/) | [Cold Start Guide](https://developers.cloudflare.com/containers/troubleshooting/cold-starts/)

### Authentication issues

```bash
# Check authentication status
wrangler whoami

# Re-authenticate
wrangler login

# Or use API token
export CLOUDFLARE_API_TOKEN=<token>
```

**Reference:** [Wrangler Authentication](https://developers.cloudflare.com/workers/wrangler/commands/#login) | [API Token Management](https://dash.cloudflare.com/profile/api-tokens)

## Cost Estimation

### Typical Usage

For moderate traffic (around 100 requests/day):

| Component | Cost/Month |
|-----------|----------|
| Workers | Typically free for low-volume workloads (see [Workers Pricing](https://developers.cloudflare.com/workers/platform/pricing/)) |
| Container instances | ~$5-15 (usage-based, depends on runtime hours) |
| Image storage | <$1 |
| **Total** | **~$5-20** |

### Factors

- **Container runtime pricing**: Usage-based billing (per vCPU / runtime) — see [Cloudflare Containers pricing](https://developers.cloudflare.com/containers/platform-details/pricing/) for current rates
- **Pay only for running instances** (not provisioned/sleeping)
- **Free tiers**: Cloudflare offers generous free tiers — always confirm current limits in the [dashboard](https://dash.cloudflare.com/) and [official pricing docs](https://developers.cloudflare.com/containers/platform-details/pricing/)

**Reference:** [Containers Pricing](https://developers.cloudflare.com/containers/platform-details/pricing/) | [Billing Overview](https://developers.cloudflare.com/billing/)

## Next Steps

1. ✅ Review and customize configuration in `wrangler.toml`
2. ✅ Test locally: `npm run dev`
3. ✅ Deploy to production: `npm run deploy`
4. ✅ Monitor in [Cloudflare Dashboard](https://dash.cloudflare.com/)

## Additional Resources

- **Getting Started**: [Cloudflare Containers Quickstart](https://developers.cloudflare.com/containers/get-started/)
- **API Reference**: [REST API Documentation](https://developers.cloudflare.com/api/resources/)
- **Community**: [Cloudflare Community Forums](https://community.cloudflare.com/)
- **Support**: [Cloudflare Support](https://support.cloudflare.com/)
5. ✅ Optimize based on metrics and usage

## Useful Resources

- [Cloudflare Containers Docs](https://developers.cloudflare.com/containers/)
- [Getting Started Guide](https://developers.cloudflare.com/containers/get-started/)
- [Container Limits](https://developers.cloudflare.com/containers/platform-details/limits/)
- [Wrangler Configuration](https://developers.cloudflare.com/workers/wrangler/configuration/#containers)
- [Wrangler Commands](https://developers.cloudflare.com/workers/wrangler/commands/#containers)

## Support

For issues or questions:

- 🐛 Check [GitHub Issues](https://github.com/hossain-khan/image-insights-api/issues)
- 💬 Join [Cloudflare Discord](https://discord.cloudflare.com/)
- 📖 Read [Official Docs](https://developers.cloudflare.com/containers/)
