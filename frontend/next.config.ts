import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server output; consumed by the container image (SHOP-122).
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  // Scaffold defaults for this Next.js release; kept as generated.
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
