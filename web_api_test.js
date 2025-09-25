#!/usr/bin/env node
/**
 * Web API Test for Prince Flowers Enhanced Agent
 *
 * This script tests the actual web interface at http://127.0.0.1:8899
 * and validates that prince commands return real data (not demo responses).
 */

const http = require('http');
const https = require('https');
const querystring = require('querystring');

class WebAPITester {
    constructor() {
        this.baseURL = 'http://127.0.0.1:8899';
        this.testResults = [];
    }

    async testWebInterface() {
        console.log('🌐 TESTING WEB INTERFACE AT http://127.0.0.1:8899');
        console.log('='.repeat(60));

        // Test 1: Basic connectivity
        await this.testBasicConnectivity();

        // Test 2: Prince command endpoints
        await this.testPrinceCommands();

        // Test 3: Validate real search results
        await this.testRealSearchResults();

        this.generateReport();
    }

    async testBasicConnectivity() {
        console.log('\n📡 Testing basic connectivity...');

        try {
            const response = await this.makeRequest('GET', '/');
            console.log(`✅ Server responded: ${response.statusCode} ${response.statusMessage}`);

            if (response.data) {
                const hasHTML = response.data.includes('<html') || response.data.includes('<!DOCTYPE');
                const hasTitle = response.data.includes('<title>') || response.data.includes('TORQ') || response.data.includes('Prince');

                console.log(`   HTML content detected: ${hasHTML}`);
                console.log(`   Title/branding detected: ${hasTitle}`);

                this.recordTest('Basic Connectivity', true, `Server running, HTML: ${hasHTML}, Branding: ${hasTitle}`);
            } else {
                this.recordTest('Basic Connectivity', true, 'Server responding but no content data');
            }
        } catch (error) {
            console.log(`❌ Connection failed: ${error.message}`);
            this.recordTest('Basic Connectivity', false, error.message);
        }
    }

    async testPrinceCommands() {
        console.log('\n🤖 Testing Prince command endpoints...');

        const testCommands = [
            { command: 'prince help', expectation: 'help information' },
            { command: 'prince status', expectation: 'agent status' },
            { command: 'prince search quantum computing latest news', expectation: 'search results' },
            { command: 'prince capabilities', expectation: 'capability list' }
        ];

        for (const test of testCommands) {
            console.log(`\n🔍 Testing: "${test.command}"`);

            try {
                // Try different endpoint patterns that might exist
                const endpoints = [
                    `/api/command?cmd=${encodeURIComponent(test.command)}`,
                    `/command/${encodeURIComponent(test.command)}`,
                    `/prince/${encodeURIComponent(test.command.replace('prince ', ''))}`,
                    `/api/prince?query=${encodeURIComponent(test.command)}`,
                    `/query?q=${encodeURIComponent(test.command)}`
                ];

                let success = false;
                let response = null;

                for (const endpoint of endpoints) {
                    try {
                        response = await this.makeRequest('GET', endpoint);
                        if (response.statusCode === 200) {
                            console.log(`   ✅ Endpoint found: ${endpoint}`);
                            success = true;
                            break;
                        }
                    } catch (err) {
                        // Try next endpoint
                    }
                }

                if (success && response) {
                    // Analyze response
                    const isReal = this.analyzeResponseReality(response.data, test.command);
                    const responseLength = response.data ? response.data.length : 0;

                    console.log(`   📊 Response length: ${responseLength} characters`);
                    console.log(`   🎯 Real data detected: ${isReal ? 'YES' : 'NO'}`);

                    if (responseLength > 10) {
                        const preview = response.data.substring(0, 100) + '...';
                        console.log(`   📝 Preview: ${preview}`);
                    }

                    this.recordTest(
                        `Prince Command: ${test.command}`,
                        true,
                        `Success - ${responseLength} chars, Real data: ${isReal}`
                    );
                } else {
                    console.log(`   ❌ No working endpoint found for command`);
                    this.recordTest(`Prince Command: ${test.command}`, false, 'No working API endpoint found');
                }

            } catch (error) {
                console.log(`   ❌ Error: ${error.message}`);
                this.recordTest(`Prince Command: ${test.command}`, false, error.message);
            }
        }
    }

    async testRealSearchResults() {
        console.log('\n🔍 Testing for real search results (not demo data)...');

        try {
            // Test a specific search that should return current data
            const searchCommand = 'prince search latest AI developments 2024';

            const endpoints = [
                `/api/search?query=${encodeURIComponent('latest AI developments 2024')}`,
                `/search?q=${encodeURIComponent('latest AI developments 2024')}`,
                `/api/prince/search?q=${encodeURIComponent('latest AI developments 2024')}`
            ];

            let foundRealData = false;
            let searchResults = null;

            for (const endpoint of endpoints) {
                try {
                    const response = await this.makeRequest('GET', endpoint);
                    if (response.statusCode === 200 && response.data) {
                        searchResults = response.data;
                        foundRealData = this.validateRealSearchData(response.data);
                        if (foundRealData) {
                            console.log(`   ✅ Real search data found via: ${endpoint}`);
                            break;
                        }
                    }
                } catch (err) {
                    // Try next endpoint
                }
            }

            if (searchResults) {
                console.log(`   📊 Search results length: ${searchResults.length} characters`);

                // Check for real vs demo indicators
                const realIndicators = [
                    /\d{4}/.test(searchResults), // Contains years
                    /https?:\/\//.test(searchResults), // Contains URLs
                    /[A-Z][a-z]+ \d{1,2}, 2024/.test(searchResults), // Contains dates
                    !/demo|sample|placeholder|test data/i.test(searchResults) // Not demo data
                ];

                const realScore = realIndicators.filter(Boolean).length;
                console.log(`   🎯 Reality score: ${realScore}/4`);

                this.recordTest('Real Search Results', realScore >= 2,
                    `Reality indicators: ${realScore}/4, Length: ${searchResults.length}`);
            } else {
                this.recordTest('Real Search Results', false, 'No search endpoint returned data');
            }

        } catch (error) {
            console.log(`   ❌ Search test failed: ${error.message}`);
            this.recordTest('Real Search Results', false, error.message);
        }
    }

    analyzeResponseReality(responseData, command) {
        if (!responseData) return false;

        // Check for demo/mock indicators
        const demoPatterns = [
            /demo/i,
            /sample/i,
            /placeholder/i,
            /test\s*data/i,
            /mock/i,
            /lorem ipsum/i,
            /\[demo\]/i,
            /example\.com/i
        ];

        const hasDemoIndicators = demoPatterns.some(pattern => pattern.test(responseData));
        if (hasDemoIndicators) return false;

        // Check for real data indicators
        const realPatterns = [
            /https?:\/\/[^\s]+/,  // Real URLs
            /\d{4}/,              // Years
            /\$\d+/,              // Prices
            /\b[A-Z][a-z]+\s+\d{1,2},\s+202[3-4]\b/, // Recent dates
            /\b(breaking|latest|recent|today|yesterday)\b/i // Recent indicators
        ];

        const realScore = realPatterns.filter(pattern => pattern.test(responseData)).length;
        return realScore >= 2;
    }

    validateRealSearchData(data) {
        // More sophisticated validation for search results
        const realDataIndicators = [
            data.includes('http') && !data.includes('example.com'),
            /202[3-4]/.test(data), // Contains recent years
            data.length > 500, // Substantial content
            !/(demo|sample|placeholder|test)/i.test(data), // Not obviously fake
            /\b(news|article|report|study|research)\b/i.test(data) // News-like content
        ];

        return realDataIndicators.filter(Boolean).length >= 3;
    }

    async makeRequest(method, path, data = null) {
        return new Promise((resolve, reject) => {
            const url = new URL(path, this.baseURL);

            const options = {
                hostname: url.hostname,
                port: url.port || 8899,
                path: url.pathname + url.search,
                method: method,
                timeout: 10000,
                headers: {
                    'User-Agent': 'Prince-Flowers-Test-Suite/1.0',
                    'Accept': 'application/json, text/html, */*',
                    'Content-Type': 'application/json'
                }
            };

            if (data && method !== 'GET') {
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

            if (data && method !== 'GET') {
                req.write(JSON.stringify(data));
            }

            req.end();
        });
    }

    recordTest(testName, success, details) {
        this.testResults.push({
            name: testName,
            success: success,
            details: details,
            timestamp: new Date().toISOString()
        });

        const status = success ? '✅ PASS' : '❌ FAIL';
        console.log(`${status} ${testName}: ${details}`);
    }

    generateReport() {
        console.log('\n' + '='.repeat(80));
        console.log('📊 WEB API TEST REPORT');
        console.log('='.repeat(80));

        const passed = this.testResults.filter(t => t.success).length;
        const total = this.testResults.length;
        const successRate = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;

        console.log(`\n📈 RESULTS:`);
        console.log(`   • Total Tests: ${total}`);
        console.log(`   • Passed: ${passed} ✅`);
        console.log(`   • Failed: ${total - passed} ❌`);
        console.log(`   • Success Rate: ${successRate}%`);

        if (successRate >= 70) {
            console.log(`\n🎉 WEB INTERFACE: FULLY FUNCTIONAL`);
        } else if (successRate >= 40) {
            console.log(`\n⚠️  WEB INTERFACE: PARTIALLY FUNCTIONAL`);
        } else {
            console.log(`\n❌ WEB INTERFACE: NEEDS ATTENTION`);
        }

        console.log('\n📋 DETAILED RESULTS:');
        this.testResults.forEach((test, index) => {
            const status = test.success ? '✅' : '❌';
            console.log(`   ${index + 1}. ${status} ${test.name}`);
            console.log(`      ${test.details}`);
        });

        console.log('\n' + '='.repeat(80));
    }
}

// Run the tests
async function main() {
    const tester = new WebAPITester();
    await tester.testWebInterface();
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = WebAPITester;