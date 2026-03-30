/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [];
  },

  // TypeScript errors ignored at build time
 // Ignore ESLint errors
  eslint: {
    ignoreDuringBuilds: true,
  },

  // Ignore TypeScript errors
  typescript: {
    ignoreBuildErrors: true,
  },

  // Suppress strict warnings
  reactStrictMode: false,

  // Fix lockfile workspace warning
  outputFileTracingRoot: require('path').join(__dirname, '../../'),
  // Optional: reduce strict warnings
  reactStrictMode: false,
};

module.exports = nextConfig;
