#!/usr/bin/env node
/**
 * Server Analysis Tool
 *
 * Analyzes what's actually running on port 8899 and determines
 * the correct API endpoints for Prince Flowers commands.
 */

const http = require('http');

class ServerAnalyzer {
    constructor() {
        this.baseURL = 'http://127.0.0.1:8899';
    }

    async analyzeServer() {
        console.log('🔍 ANALYZING SERVER AT http://127.0.0.1:8899');
        console.log('='.repeat(60));

        // Get the main page
        await this.analyzeMainPage();

        // Try to discover API endpoints
        await this.discoverEndpoints();

        // Check for websocket support
        await this.checkWebSocketSupport();
    }

    async analyzeMainPage() {
        console.log('\n📄 Analyzing main page...');

        try {
            const response = await this.makeRequest('GET', '/');
            console.log(`Status: ${response.statusCode} ${response.statusMessage}`);
            console.log(`Content-Type: ${response.headers['content-type']}`);
            console.log(`Content-Length: ${response.headers['content-length']}`);

            if (response.data) {
                console.log(`\n📊 Content Analysis:`);
                console.log(`   Total length: ${response.data.length} characters`);

                // Check for framework indicators
                const frameworks = {
                    'React': /react/i.test(response.data),
                    'Vue': /vue/i.test(response.data),
                    'Angular': /angular/i.test(response.data),
                    'Express': /express/i.test(response.data),
                    'FastAPI': /fastapi/i.test(response.data),
                    'Flask': /flask/i.test(response.data),
                    'Django': /django/i.test(response.data)
                };

                console.log(`\n🛠️  Framework Detection:`);
                for (const [framework, detected] of Object.entries(frameworks)) {
                    if (detected) {
                        console.log(`   ✅ ${framework} detected`);
                    }
                }

                // Look for API endpoint patterns
                const apiPatterns = [
                    /\/api\/[a-zA-Z]+/g,
                    /\/[a-zA-Z]+\/api/g,
                    /endpoint[s]?\s*:\s*['"`]([^'"`]+)['"`]/g,
                    /url[s]?\s*:\s*['"`]([^'"`]+)['"`]/g,
                    /fetch\s*\(\s*['"`]([^'"`]+)['"`]/g
                ];

                console.log(`\n🔗 API Endpoint Discovery:`);
                const foundEndpoints = new Set();

                for (const pattern of apiPatterns) {
                    let match;
                    while ((match = pattern.exec(response.data)) !== null) {
                        foundEndpoints.add(match[0] || match[1]);
                    }
                }

                if (foundEndpoints.size > 0) {
                    console.log(`   Found ${foundEndpoints.size} potential endpoints:`);
                    Array.from(foundEndpoints).slice(0, 10).forEach(endpoint => {
                        console.log(`   • ${endpoint}`);
                    });
                } else {
                    console.log(`   No API endpoints found in HTML`);
                }

                // Look for Prince Flowers references
                const princeRefs = [
                    /prince[\\s_-]*flowers?/gi,
                    /prince[\\s_-]*command/gi,
                    /torq[\\s_-]*console/gi,
                    /enhanced[\\s_-]*agent/gi
                ];

                console.log(`\n🤖 Prince Flowers References:`);
                let foundRefs = false;
                for (const pattern of princeRefs) {
                    const matches = response.data.match(pattern);
                    if (matches && matches.length > 0) {
                        console.log(`   • Found "${matches[0]}" (${matches.length} occurrences)`);
                        foundRefs = true;
                    }
                }

                if (!foundRefs) {
                    console.log(`   No Prince Flowers references found`);
                }

                // Show a relevant excerpt
                console.log(`\n📝 Content Preview (first 300 chars):`);
                console.log(response.data.substring(0, 300) + '...');
            }

        } catch (error) {
            console.log(`❌ Error analyzing main page: ${error.message}`);
        }
    }

    async discoverEndpoints() {
        console.log('\n🕵️  Discovering API endpoints...');

        const commonEndpoints = [
            '/',
            '/api',
            '/api/health',
            '/api/status',
            '/health',
            '/status',
            '/docs',
            '/api/docs',
            '/swagger',
            '/openapi.json',
            '/api.json',
            '/version',
            '/api/version',
            '/ping',
            '/api/ping',
            '/command',
            '/api/command',
            '/prince',
            '/api/prince',
            '/search',
            '/api/search',
            '/query',
            '/api/query',
            '/chat',
            '/api/chat'
        ];

        console.log(`Testing ${commonEndpoints.length} common endpoints...`);

        const workingEndpoints = [];

        for (const endpoint of commonEndpoints) {
            try {
                const response = await this.makeRequest('GET', endpoint);
                if (response.statusCode === 200) {
                    workingEndpoints.push({
                        path: endpoint,
                        contentType: response.headers['content-type'],
                        length: response.data ? response.data.length : 0,
                        preview: response.data ? response.data.substring(0, 100) : ''
                    });
                }
            } catch (error) {
                // Endpoint not available
            }
        }

        console.log(`\n✅ Found ${workingEndpoints.length} working endpoints:`);
        workingEndpoints.forEach(ep => {
            console.log(`   • ${ep.path}`);
            console.log(`     Content-Type: ${ep.contentType}`);
            console.log(`     Length: ${ep.length} chars`);
            if (ep.preview) {
                console.log(`     Preview: ${ep.preview.replace(/\s+/g, ' ').trim()}...`);
            }
            console.log();
        });
    }

    async checkWebSocketSupport() {
        console.log('\n🔌 Checking WebSocket support...');

        try {
            // Try to upgrade to WebSocket
            const response = await this.makeRequest('GET', '/', null, {
                'Upgrade': 'websocket',
                'Connection': 'Upgrade',
                'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
                'Sec-WebSocket-Version': '13'
            });

            if (response.statusCode === 101) {
                console.log('   ✅ WebSocket upgrade successful');
            } else {
                console.log(`   ❌ WebSocket upgrade failed (${response.statusCode})`);
            }
        } catch (error) {
            console.log(`   ❌ WebSocket test failed: ${error.message}`);
        }
    }

    async makeRequest(method, path, data = null, extraHeaders = {}) {
        return new Promise((resolve, reject) => {
            const url = new URL(path, this.baseURL);

            const options = {
                hostname: url.hostname,
                port: url.port || 8899,
                path: url.pathname + url.search,
                method: method,
                timeout: 5000,
                headers: {
                    'User-Agent': 'Prince-Flowers-Server-Analyzer/1.0',
                    'Accept': 'text/html,application/json,*/*',
                    ...extraHeaders
                }
            };

            const req = http.request(options, (res) => {
                let responseData = '';

                res.on('data', (chunk) => {
                    responseData += chunk;
                });

                res.on('end', () => {
                    resolve({
                        statusCode: res.statusCode,
                        statusMessage: res.statusMessage,
                        headers: res.headers,
                        data: responseData
                    });
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.on('timeout', () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            if (data && method !== 'GET') {
                req.write(typeof data === 'string' ? data : JSON.stringify(data));
            }

            req.end();
        });
    }
}

// Run the analysis
async function main() {
    const analyzer = new ServerAnalyzer();
    await analyzer.analyzeServer();
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = ServerAnalyzer;