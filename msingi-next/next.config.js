/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow your FastAPI backend during development
  async rewrites() {
    return [];
  },
};

module.exports = nextConfig;
