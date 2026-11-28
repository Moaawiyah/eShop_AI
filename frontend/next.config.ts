import type { NextConfig } from "next";

import { securityHeaders } from "./src/lib/security/headers";

const nextConfig: NextConfig = {
  // Self-contained server output; consumed by the container image (SHOP-122).
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  // Scaffold defaults for this Next.js release; kept as generated.
  cacheComponents: true,
  partialPrefetching: true,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders({
          dev: process.env.NODE_ENV !== "production",
        }),
      },
    ];
  },
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
