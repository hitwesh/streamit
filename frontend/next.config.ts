import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://image.tmdb.org; connect-src 'self' http://127.0.0.1:8000 http://localhost:8000 ws://127.0.0.1:8000 ws://localhost:8000; frame-src 'self' http://127.0.0.1:8000 http://localhost:8000 https://watch.embed-api.stream https://multiembed.mov https://*.multiembed.mov https://getsuperembed.link https://*.getsuperembed.link https:; child-src 'self' http://127.0.0.1:8000 http://localhost:8000 https://watch.embed-api.stream https://multiembed.mov https://*.multiembed.mov https://getsuperembed.link https://*.getsuperembed.link https:; object-src 'none'; base-uri 'self'; frame-ancestors 'self'",
          },
        ],
      },
    ]
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "image.tmdb.org",
        pathname: "/t/p/**",
      },
    ],
  },
}

export default nextConfig
