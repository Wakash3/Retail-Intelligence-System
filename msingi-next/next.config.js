/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [];
  },

  // Ignore TypeScript errors at build time
  typescript: {
    ignoreBuildErrors: true,
  },

  // Suppress strict warnings
  reactStrictMode: false,

  // Fix lockfile workspace warning
  outputFileTracingRoot: require('path').join(__dirname, '../../'),
};

module.exports = nextConfig;
