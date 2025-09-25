#!/usr/bin/env node
/**
 * API Discovery Tool
 *
 * Reads the OpenAPI spec from the running server and tests the actual API endpoints
 * for Prince Flowers commands.
 */

const http = require('http');

class APIDiscovery {
    constructor() {
        this.baseURL = 'http://127.0.0.1:8899';
    }

    async discoverAPI() {
        console.log('🔍 DISCOVERING API ENDPOINTS FROM OPENAPI SPEC');
        console.log('='.repeat(60));

        // Get OpenAPI spec
        const spec = await this.getOpenAPISpec();
        if (!spec) {
            console.log('❌ Could not retrieve OpenAPI spec');
            return;
        }

        // Analyze endpoints
        await this.analyzeEndpoints(spec);

        // Test Prince-related endpoints
        await this.testPrinceEndpoints(spec);
    }

    async getOpenAPISpec() {
        console.log('\n📋 Retrieving OpenAPI specification...');

        try {
            const response = await this.makeRequest('GET', '/openapi.json');
            if (response.statusCode === 200) {
                const spec = JSON.parse(response.data);
                console.log(`✅ OpenAPI spec retrieved`);
                console.log(`   Title: ${spec.info.title}`);
                console.log(`   Version: ${spec.info.version}`);
                console.log(`   Description: ${spec.info.description}`);
                console.log(`   Endpoints: ${Object.keys(spec.paths || {}).length}`);
                return spec;
            } else {
                console.log(`❌ Failed to get spec: ${response.statusCode}`);
                return null;
            }
        } catch (error) {
            console.log(`❌ Error retrieving spec: ${error.message}`);
            return null;
        }
    }

    async analyzeEndpoints(spec) {
        console.log('\n🔍 Analyzing available endpoints...');

        const paths = spec.paths || {};
        const endpoints = Object.keys(paths);

        console.log(`\nFound ${endpoints.length} API endpoints:`);

        const relevantEndpoints = [];

        endpoints.forEach(path => {
            const methods = Object.keys(paths[path]);
            methods.forEach(method => {
                const endpoint = paths[path][method];
                const summary = endpoint.summary || '';
                const description = endpoint.description || '';

                console.log(`\n• ${method.toUpperCase()} ${path}`);
                console.log(`  Summary: ${summary}`);
                if (description && description !== summary) {
                    console.log(`  Description: ${description}`);
                }

                // Check if this might be Prince-related
                const isPrinceRelated = (
                    path.toLowerCase().includes('prince') ||
                    path.toLowerCase().includes('command') ||
                    path.toLowerCase().includes('search') ||
                    path.toLowerCase().includes('query') ||
                    summary.toLowerCase().includes('prince') ||
                    description.toLowerCase().includes('prince')
                );

                if (isPrinceRelated) {
                    relevantEndpoints.push({
                        method: method.toUpperCase(),
                        path: path,
                        summary: summary,
                        description: description
                    });
                    console.log(`  🎯 PRINCE-RELATED ENDPOINT`);
                }
            });
        });

        console.log(`\n🎯 Found ${relevantEndpoints.length} potentially Prince-related endpoints:`);
        relevantEndpoints.forEach(ep => {
            console.log(`   • ${ep.method} ${ep.path} - ${ep.summary}`);
        });

        return relevantEndpoints;
    }

    async testPrinceEndpoints(spec) {
        console.log('\n🧪 Testing API endpoints for Prince commands...');

        const paths = spec.paths || {};
        const testCommands = [
            { command: 'prince help', description: 'Help command test' },
            { command: 'prince status', description: 'Status command test' },
            { command: 'prince search AI news', description: 'Search command test' },
            { command: 'prince capabilities', description: 'Capabilities command test' }
        ];

        // Test various endpoint patterns
        const endpointPatterns = [
            '/api/console/command',
            '/api/console/process',
            '/api/command',
            '/api/process',
            '/api/mcp/command',
            '/api/mcp/process',
            '/console/command',
            '/console/process',
            '/api/chat/message',
            '/api/chat/send'
        ];

        console.log('\n🔧 Testing common command patterns...');

        for (const pattern of endpointPatterns) {
            if (paths[pattern]) {
                console.log(`\n🎯 Testing endpoint: ${pattern}`);

                for (const test of testCommands) {
                    await this.testCommandEndpoint(pattern, test.command, test.description);
                }
            }
        }

        // Test POST to discovered endpoints
        console.log('\n📤 Testing POST requests to command endpoints...');

        const postEndpoints = Object.keys(paths).filter(path => {
            return paths[path].post && (
                path.includes('command') ||
                path.includes('process') ||
                path.includes('execute') ||
                path.includes('chat') ||
                path.includes('message')
            );
        });

        for (const endpoint of postEndpoints) {
            console.log(`\n🔄 Testing POST ${endpoint}...`);

            const testPayloads = [
                { message: 'prince help' },
                { command: 'prince help' },
                { query: 'prince help' },
                { input: 'prince help' },
                { text: 'prince help' },
                { content: 'prince help' }
            ];

            for (const payload of testPayloads) {
                try {
                    const response = await this.makeRequest('POST', endpoint, payload);

                    if (response.statusCode === 200) {
                        console.log(`   ✅ Success with payload: ${JSON.stringify(payload)}`);
                        console.log(`   📊 Response length: ${response.data.length}`);

                        if (response.data.length > 50) {
                            const preview = response.data.substring(0, 200);
                            console.log(`   📝 Preview: ${preview}...`);
                        }

                        // Check if response looks like Prince Flowers output
                        const isPrinceResponse = this.analyzePrinceResponse(response.data);
                        console.log(`   🤖 Prince response detected: ${isPrinceResponse ? 'YES' : 'NO'}`);

                        if (isPrinceResponse) {
                            console.log(`   🎉 WORKING PRINCE ENDPOINT FOUND!`);
                            console.log(`      Endpoint: POST ${endpoint}`);
                            console.log(`      Payload: ${JSON.stringify(payload)}`);
                            return; // Found working endpoint, stop testing
                        }

                        break; // This payload format works, try next endpoint

                    } else if (response.statusCode !== 422) { // 422 is expected for wrong payload format
                        console.log(`   ⚠️  Status ${response.statusCode}: ${response.statusMessage}`);
                    }

                } catch (error) {
                    // Skip errors for payload testing
                }
            }
        }
    }

    async testCommandEndpoint(endpoint, command, description) {
        console.log(`   Testing: "${command}"`);

        const testMethods = [
            { method: 'GET', params: `?command=${encodeURIComponent(command)}` },
            { method: 'GET', params: `?message=${encodeURIComponent(command)}` },
            { method: 'GET', params: `?q=${encodeURIComponent(command)}` },
            { method: 'POST', data: { command: command } },
            { method: 'POST', data: { message: command } },
            { method: 'POST', data: { query: command } }
        ];

        for (const test of testMethods) {
            try {
                const path = endpoint + (test.params || '');
                const response = await this.makeRequest(test.method, path, test.data);

                if (response.statusCode === 200 && response.data) {
                    console.log(`     ✅ ${test.method} worked - ${response.data.length} chars`);

                    if (this.analyzePrinceResponse(response.data)) {
                        console.log(`     🎉 PRINCE RESPONSE DETECTED!`);
                        console.log(`        Method: ${test.method} ${path}`);
                        if (test.data) {
                            console.log(`        Data: ${JSON.stringify(test.data)}`);
                        }
                        return true;
                    }
                }
            } catch (error) {
                // Continue testing other methods
            }
        }

        return false;
    }

    analyzePrinceResponse(responseData) {
        if (!responseData) return false;

        const princeIndicators = [
            /prince[\s-_]*flowers?/i,
            /enhanced[\s-_]*agent/i,
            /agentic[\s-_]*rl/i,
            /reinforcement[\s-_]*learning/i,
            /capabilities/i,
            /status.*available/i,
            /search.*results/i,
            /agent.*ready/i,
            /torq.*console/i
        ];

        return princeIndicators.some(pattern => pattern.test(responseData));
    }

    async makeRequest(method, path, data = null) {
        return new Promise((resolve, reject) => {
            const url = new URL(path, this.baseURL);

            const options = {
                hostname: url.hostname,
                port: url.port || 8899,
                path: url.pathname + url.search,
                method: method,
                timeout: 8000,
                headers: {
                    'User-Agent': 'Prince-Flowers-API-Discovery/1.0',
                    'Accept': 'application/json, text/plain, */*',
                    'Content-Type': 'application/json'
                }
            };

            if (data) {
                const postData = JSON.stringify(data);
                options.headers['Content-Length'] = Buffer.byteLength(postData);
            }

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

            if (data) {
                req.write(JSON.stringify(data));
            }

            req.end();
        });
    }
}

// Run the discovery
async function main() {
    const discovery = new APIDiscovery();
    await discovery.discoverAPI();
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = APIDiscovery;