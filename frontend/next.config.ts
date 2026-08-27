import type { NextConfig } from "next";
import withSerwistInit from "@serwist/next";

const withSerwist = withSerwistInit({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  disable: process.env.NODE_ENV === "development",
  register: false,
});

const nextConfig: NextConfig = {
  ...(process.env.OUTPUT_STANDALONE === "1" ? { output: "standalone" as const } : {}),
  // Serwist adds a webpack plugin; Next 16 Turbopack needs an explicit turbopack key
  // (or --webpack) when any webpack config is present.
  turbopack: {},
};

export default withSerwist(nextConfig);
