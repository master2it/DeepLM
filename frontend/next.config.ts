import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker image uses standalone; Vercel needs the default tracing files.
  ...(process.env.OUTPUT_STANDALONE === "1" ? { output: "standalone" as const } : {}),
};

export default nextConfig;
