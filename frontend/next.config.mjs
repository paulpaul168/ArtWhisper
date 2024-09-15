/** @type {import('next').NextConfig} */
const nextConfig = {
  async redirects() {
    return [
      {
        source: "/",
        destination: "/camera",
        permanent: false,
      },
      {
        source: "/auth",
        destination: "/camera",
        permanent: false,
        has: [
          {
            type: "cookie",
            key: "authToken",
          },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/:path*'
      },
    ];
  },
};

export default nextConfig;
