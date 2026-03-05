/**
 * Vercel Serverless Function: API Proxy to Railway
 * 
 * This function handles all /api/* requests and forwards them to Railway
 * with the TORQ_PROXY_SHARED_SECRET header injected server-side.
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';

const RAILWAY_URL = 'https://web-production-74ed0.up.railway.app';
const PROXY_SECRET = process.env.TORQ_PROXY_SHARED_SECRET;

export const config = {
  runtime: 'nodejs20.x',
};

export default async function handler(
  request: VercelRequest,
  response: VercelResponse
): Promise<VercelResponse> {
  // Handle CORS preflight
  if (request.method === 'OPTIONS') {
    return response.status(200)
      .header('Access-Control-Allow-Origin', '*')
      .header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
      .header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
      .send('');
  }

  // Extract path from request
  const path = request.url || '';
  const queryString = request.query || '';

  // Build Railway URL
  const railwayUrl = `${RAILWAY_URL}${path}${queryString}`;

  // Clone headers (remove host header)
  const headers: Record<string, string> = {};
  for (const [key, value] of Object.entries(request.headers)) {
    if (key.toLowerCase() !== 'host') {
      headers[key] = value;
    }
  }

  // Add proxy secret if configured
  if (PROXY_SECRET) {
    headers['x-torq-proxy-secret'] = PROXY_SECRET;
  }

  // Forward request to Railway
  try {
    const railwayResponse = await fetch(railwayUrl, {
      method: request.method,
      headers,
      body: request.body,
      // @ts-ignore
      duplex: 'half',
    });

    // Copy response headers
    const responseHeaders: Record<string, string> = {};
    railwayResponse.headers.forEach((value, key) => {
      responseHeaders[key] = value;
    });

    // Add CORS header
    responseHeaders['Access-Control-Allow-Origin'] = '*';

    return response.status(railwayResponse.status)
      .headers(responseHeaders)
      .send(railwayResponse.body);

  } catch (error) {
    console.error('Proxy error:', error);
    return response.status(500)
      .header('Access-Control-Allow-Origin', '*')
      .header('Content-Type', 'application/json')
      .send(JSON.stringify({
        error: 'Proxy error',
        message: (error as Error).message
      }));
  }
}
