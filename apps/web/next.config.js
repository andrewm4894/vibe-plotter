/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ["plotly.js-dist-min"],
  },
};

module.exports = nextConfig;
