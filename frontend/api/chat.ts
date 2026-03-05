/**
 * Vercel Edge Function: API Proxy to Railway
 * 
 * Proxies /api/chat/* requests to Railway with authentication.
 * This is the reliable way to handle API proxying with Vercel.
 */

const RAILWAY_URL = 'https://web-production-74ed0.up.railway.app';

export const config = {
  runtime: 'edge',
};

export default async function handler(request: Request) {
  // Handle CORS preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  }

  try {
    const url = new URL(request.url);
    const path = url.pathname + url.search;

    // Build Railway URL
    const railwayUrl = `${RAILWAY_URL}${path}`;

    // Clone headers
    const headers = new Headers();
    request.headers.forEach((value, key) => {
      headers.set(key, value);
    });

    // Add proxy secret from environment
    const proxySecret = process.env.TORQ_PROXY_SHARED_SECRET;
    if (proxySecret) {
      headers.set('x-torq-proxy-secret', proxySecret);
    }

    // Forward request to Railway
    const response = await fetch(railwayUrl, {
      method: request.method,
      headers,
      body: request.body,
      // @ts-ignore - duplex is required for streaming
      duplex: 'half',
    });

    // Clone response headers
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
      responseHeaders.set(key, value);
    });

    // Add CORS headers
    responseHeaders.set('Access-Control-Allow-Origin', '*');

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });

  } catch (error) {
    console.error('Proxy error:', error);
    return new Response(
      JSON.stringify({ error: 'Proxy error', message: (error as Error).message }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  }
}
