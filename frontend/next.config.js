/** @type {import('next').NextConfig} */
const nextConfig = {
  // Commented out static export as it conflicts with dynamic routes and authentication
  // output: 'export',
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: { unoptimized: true },
  trailingSlash: true,
};

module.exports = nextConfig;
