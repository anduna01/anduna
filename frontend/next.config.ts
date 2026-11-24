import type { NextConfig } from "next";

// El navegador sólo habla con Next (/api/*). Next reenvía al backend FastAPI.
// BACKEND_URL es una variable de servidor: nunca se expone al cliente.
const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
};

export default nextConfig;
