const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');
const https = require('node:https');
const config = getDefaultConfig(__dirname);
config.watchFolders = [path.resolve(__dirname, '../shared')];
config.resolver.sourceExts = [...new Set([...config.resolver.sourceExts, 'mjs'])];
// Local browser review only. Native builds call the public HTTPS API directly.
const enhance = config.server?.enhanceMiddleware;
config.server = { ...config.server, enhanceMiddleware(middleware, server) {
  const nextMiddleware = enhance ? enhance(middleware, server) : middleware;
  if (process.env.GRAPHISCAN_EXPO_PREVIEW_PROXY !== '1') return nextMiddleware;
  return (req, res, next) => {
    if (!req.url?.startsWith('/api/v1/')) return nextMiddleware(req, res, next);
    const target = new URL(req.url, 'https://graphiscan-admin-api.onrender.com');
    if (target.origin !== 'https://graphiscan-admin-api.onrender.com' || !target.pathname.startsWith('/api/v1/')) {
      res.writeHead(400, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      return res.end(JSON.stringify({error:{code:'INVALID_REQUEST',message:'Invalid preview request.'}}));
    }
    const headers = {};
    for (const key of ['accept', 'authorization', 'content-type', 'idempotency-key']) {
      if (req.headers[key]) headers[key] = req.headers[key];
    }
    const upstream = https.request(target, { method: req.method, headers, timeout: 120000 }, response => {
      res.writeHead(response.statusCode || 502, {
        'Content-Type': response.headers['content-type'] || 'application/json',
        'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'
      });
      response.on('error', () => res.destroy());
      response.pipe(res);
    });
    upstream.on('timeout', () => upstream.destroy());
    upstream.on('error', () => {
      if (res.headersSent) return res.destroy();
      res.writeHead(503, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({error:{code:'BACKEND_UNAVAILABLE',message:'The server is unavailable. Try again shortly.'}}));
    });
    req.on('aborted', () => upstream.destroy());
    res.on('close', () => { if (!res.writableEnded) upstream.destroy(); });
    req.pipe(upstream);
  };
} };
module.exports = config;
