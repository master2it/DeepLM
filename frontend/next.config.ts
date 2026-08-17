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
};

export default withSerwist(nextConfig);
