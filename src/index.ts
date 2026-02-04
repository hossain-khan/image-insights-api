/**
 * Image Insights API - Cloudflare Workers Entry Point
 *
 * This Worker routes all incoming requests to the containerized FastAPI application.
 * Each container instance is backed by a Durable Object that manages its lifecycle.
 *
 * Official Documentation:
 * - Cloudflare Containers: https://developers.cloudflare.com/containers/
 * - Workers & Containers Architecture: https://developers.cloudflare.com/containers/architecture/
 * - Getting Started: https://developers.cloudflare.com/containers/get-started/
 * - Managing Containers: https://developers.cloudflare.com/containers/manage/
 * - Durable Objects: https://developers.cloudflare.com/durable-objects/
 *
 * Architecture:
 * - Worker receives incoming HTTP request
 * - Routes request to Container instance via Durable Object
 * - Container (FastAPI app on port 8080) processes request
 * - Response is returned to client
 */

import { Container } from "@cloudflare/containers";

/**
 * ImageInsightsContainer Configuration
 *
 * This class extends the Container class to configure how the containerized
 * FastAPI application runs on Cloudflare.
 *
 * Container Lifecycle: https://developers.cloudflare.com/containers/configuration/lifecycle-events/
 * Container Configuration: https://developers.cloudflare.com/containers/configuration/
 */
export class ImageInsightsContainer extends Container {
  // Port the FastAPI application listens on
  defaultPort = 8080;

  // Keep the container alive for 10 minutes of inactivity
  // After 10 minutes with no requests, the container will sleep
  sleepAfter = "10m";

  // Environment variables passed to the container at startup
  // Note: ENABLE_DETAILED_LOGGING can be configured via environment variables
  // It defaults to the FastAPI app's default behavior if not explicitly set
  envVars: Record<string, string> = {};

  /**
   * Called when the container successfully starts
   */
  onStart() {
    console.log("🚀 Image Insights Container started successfully");
  }

  /**
   * Called when the container is shutting down
   */
  onStop() {
    console.log("🛑 Image Insights Container shutting down");
  }

  /**
   * Called when the container encounters an error
   */
  onError(error: unknown) {
    console.error("❌ Image Insights Container error:", error);
  }
}

/**
 * Durable Object binding for the container
 * Defined in wrangler.toml and bound as IMAGE_INSIGHTS_CONTAINER
 *
 * Bindings Reference: https://developers.cloudflare.com/workers/runtime-apis/durable-objects/
 */
interface Env {
  IMAGE_INSIGHTS_CONTAINER: DurableObjectNamespace;
}

/**
 * Main Worker fetch handler
 * Routes all incoming requests to the container instance
 *
 * Request Handling: https://developers.cloudflare.com/workers/runtime-apis/web-crypto/
 * Error Handling Best Practices: https://developers.cloudflare.com/workers/platform/errors/
 */
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
      // Shard requests across multiple Durable Object instances for better concurrency
      // This enables Cloudflare to spin up multiple container instances under load
      // Use a hash of the request path to distribute traffic across N buckets
      const url = new URL(request.url);
      const pathHash = url.pathname
        .split("")
        .reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const shardCount = 10; // Match max_instances in wrangler.toml
      const shardId = pathHash % shardCount;
      const containerId = `container-${shardId}`;

      const container = env.IMAGE_INSIGHTS_CONTAINER.get(
        env.IMAGE_INSIGHTS_CONTAINER.idFromName(containerId)
      );

      // Forward the incoming request to the container
      // The container will handle the request and return a response
      return await container.fetch(request);
    } catch (error) {
      // Generate a request ID for troubleshooting
      const requestId =
        typeof crypto !== "undefined" && "randomUUID" in crypto
          ? crypto.randomUUID()
          : Date.now().toString(36);

      // Log detailed error server-side
      console.error("Worker error:", {
        requestId,
        url: request.url,
        method: request.method,
        error: error instanceof Error ? error.message : String(error),
      });

      // Return generic error to client with request ID for troubleshooting
      return new Response(
        JSON.stringify({
          error: "Internal Server Error",
          message: "An unexpected error occurred. Please try again later.",
          requestId,
        }),
        {
          status: 500,
          headers: { "Content-Type": "application/json" },
        }
      );
    }
  },
};
