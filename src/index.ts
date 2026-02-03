/**
 * Image Insights API - Cloudflare Workers Entry Point
 *
 * This Worker routes all incoming requests to the containerized FastAPI application.
 * Each container instance is backed by a Durable Object that manages its lifecycle.
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
 */
export class ImageInsightsContainer extends Container {
  // Port the FastAPI application listens on
  defaultPort = 8080;

  // Keep the container alive for 10 minutes of inactivity
  // After 10 minutes with no requests, the container will sleep
  sleepAfter = "10m";

  // Environment variables passed to the container at startup
  envVars = {
    // Enable detailed logging with request info and processing times
    ENABLE_DETAILED_LOGGING: "true",
  };

  /**
   * Called when the container successfully starts
   */
  override onStart() {
    console.log("🚀 Image Insights Container started successfully");
  }

  /**
   * Called when the container is shutting down
   */
  override onStop() {
    console.log("🛑 Image Insights Container shutting down");
  }

  /**
   * Called when the container encounters an error
   */
  override onError(error: unknown) {
    console.error("❌ Image Insights Container error:", error);
  }
}

/**
 * Durable Object binding for the container
 * Defined in wrangler.toml and bound as IMAGE_INSIGHTS_CONTAINER
 */
interface Env {
  IMAGE_INSIGHTS_CONTAINER: DurableObjectNamespace;
}

/**
 * Main Worker fetch handler
 * Routes all incoming requests to the container instance
 */
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
      // Use a default container instance named "default"
      // All requests are routed to this single container instance
      const container = env.IMAGE_INSIGHTS_CONTAINER.get(
        env.IMAGE_INSIGHTS_CONTAINER.idFromName("default")
      );

      // Forward the incoming request to the container
      // The container will handle the request and return a response
      return await container.fetch(request);
    } catch (error) {
      console.error("Worker error:", error);
      return new Response(
        JSON.stringify({
          error: "Internal Server Error",
          message:
            error instanceof Error ? error.message : "Unknown error occurred",
        }),
        {
          status: 500,
          headers: { "Content-Type": "application/json" },
        }
      );
    }
  },
};
