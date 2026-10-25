import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The phone pages can also be opened through a tunnel to `next dev` (instead of the Vercel deploy)
  allowedDevOrigins: ["*.trycloudflare.com", "*.ngrok-free.app", "*.ngrok.app"],
};

export default nextConfig;
