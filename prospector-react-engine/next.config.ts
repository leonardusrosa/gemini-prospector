import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/clientes/dallas-detailing-and-buffing",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
