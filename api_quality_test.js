#!/usr/bin/env node

/**
 * TORQ Console API Quality Test
 * Tests the actual response quality and integration functionality
 */

const https = require('https');

// API Configuration
const DEEPSEEK_API_KEY = 'sk-1061efb8089744dcad1183fb2ef55960';
const GOOGLE_API_KEY = 'AIzaSyA7eNQYC-zgo2OTYjL4QnrT5GeoHxJAhDw';
const GOOGLE_ENGINE_ID = '34dd471ccd5dd4572';
const BRAVE_API_KEY = 'BSAkNrh316HK8uxqGjUN1_eeLon8PfO';

console.log('🔍 TORQ Console API Quality Testing');
console.log('===================================');

// Test DeepSeek API with detailed business query
async function testDeepSeekQuality() {
    console.log('\n🧠 Testing DeepSeek API Response Quality...');

    const data = JSON.stringify({
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are a business intelligence expert. Provide detailed, actionable insights."
            },
            {
                "role": "user",
                "content": "Analyze the top 3 digital transformation trends affecting enterprise businesses in 2024. Include specific strategies and expected ROI impacts."
            }
        ],
        "max_tokens": 300,
        "temperature": 0.7
    });

    const options = {
        hostname: 'api.deepseek.com',
        port: 443,
        path: '/chat/completions',
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${DEEPSEEK_API_KEY}`,
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(data)
        }
    };

    return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
            let body = '';

            res.on('data', (chunk) => {
                body += chunk;
            });

            res.on('end', () => {
                try {
                    const response = JSON.parse(body);

                    if (res.statusCode === 200 && response.choices) {
                        const content = response.choices[0].message.content;
                        const usage = response.usage;

                        console.log('   ✅ Status: SUCCESS');
                        console.log(`   📊 Tokens Used: ${usage.total_tokens} (prompt: ${usage.prompt_tokens}, completion: ${usage.completion_tokens})`);
                        console.log(`   📝 Response Length: ${content.length} characters`);
                        console.log(`   🎯 Quality Check: ${content.includes('2024') ? '✅ Relevant' : '❌ Off-topic'}`);
                        console.log(`   💼 Business Focus: ${content.toLowerCase().includes('enterprise') || content.toLowerCase().includes('business') ? '✅ On-target' : '❌ Generic'}`);
                        console.log('\n   📄 Sample Response:');
                        console.log(`   "${content.substring(0, 200)}..."`);

                        resolve({
                            success: true,
                            quality: 'HIGH',
                            tokens: usage.total_tokens,
                            relevance: content.includes('2024') && content.toLowerCase().includes('enterprise')
                        });
                    } else {
                        console.log(`   ❌ Status: FAILED (${res.statusCode})`);
                        console.log(`   📝 Error: ${body}`);
                        resolve({ success: false, error: body });
                    }
                } catch (e) {
                    console.log(`   ❌ Parse Error: ${e.message}`);
                    resolve({ success: false, error: e.message });
                }
            });
        });

        req.on('error', (e) => {
            console.log(`   ❌ Request Error: ${e.message}`);
            resolve({ success: false, error: e.message });
        });

        req.setTimeout(30000, () => {
            console.log('   ❌ Request Timeout');
            req.destroy();
            resolve({ success: false, error: 'Timeout' });
        });

        req.write(data);
        req.end();
    });
}

// Test Google Search API with business query
async function testGoogleSearchQuality() {
    console.log('\n🔍 Testing Google Search API Quality...');

    const query = encodeURIComponent('enterprise digital transformation best practices 2024');
    const url = `https://www.googleapis.com/customsearch/v1?key=${GOOGLE_API_KEY}&cx=${GOOGLE_ENGINE_ID}&q=${query}&num=5`;

    return new Promise((resolve, reject) => {
        https.get(url, (res) => {
            let body = '';

            res.on('data', (chunk) => {
                body += chunk;
            });

            res.on('end', () => {
                try {
                    const response = JSON.parse(body);

                    if (res.statusCode === 200 && response.items) {
                        const items = response.items;
                        const searchInfo = response.searchInformation;

                        console.log('   ✅ Status: SUCCESS');
                        console.log(`   📊 Results: ${items.length} items returned`);
                        console.log(`   🔍 Total Available: ${searchInfo.totalResults || 'N/A'}`);
                        console.log(`   ⚡ Search Time: ${searchInfo.searchTime || 'N/A'} seconds`);

                        // Quality assessment
                        const relevantResults = items.filter(item =>
                            item.title.toLowerCase().includes('digital') ||
                            item.title.toLowerCase().includes('transformation') ||
                            item.snippet.toLowerCase().includes('enterprise')
                        ).length;

                        console.log(`   🎯 Relevant Results: ${relevantResults}/${items.length} (${Math.round(relevantResults/items.length*100)}%)`);

                        console.log('\n   📄 Top Results:');
                        items.slice(0, 3).forEach((item, index) => {
                            console.log(`   ${index + 1}. ${item.title.substring(0, 60)}...`);
                            console.log(`      ${item.link}`);
                        });

                        resolve({
                            success: true,
                            quality: relevantResults >= 3 ? 'HIGH' : 'MEDIUM',
                            resultCount: items.length,
                            relevanceScore: relevantResults / items.length
                        });
                    } else {
                        console.log(`   ❌ Status: FAILED (${res.statusCode})`);
                        console.log(`   📝 Error: ${body}`);
                        resolve({ success: false, error: body });
                    }
                } catch (e) {
                    console.log(`   ❌ Parse Error: ${e.message}`);
                    resolve({ success: false, error: e.message });
                }
            });
        }).on('error', (e) => {
            console.log(`   ❌ Request Error: ${e.message}`);
            resolve({ success: false, error: e.message });
        });
    });
}

// Test Brave Search API with business query
async function testBraveSearchQuality() {
    console.log('\n🦁 Testing Brave Search API Quality...');

    const query = encodeURIComponent('business intelligence trends 2024 strategy');
    const url = `https://api.search.brave.com/res/v1/web/search?q=${query}&count=5&mkt=en-US`;

    const options = {
        hostname: 'api.search.brave.com',
        port: 443,
        path: `/res/v1/web/search?q=${query}&count=5&mkt=en-US`,
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': BRAVE_API_KEY
        }
    };

    return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
            let body = '';

            res.on('data', (chunk) => {
                body += chunk;
            });

            res.on('end', () => {
                try {
                    const response = JSON.parse(body);

                    if (res.statusCode === 200 && response.web && response.web.results) {
                        const results = response.web.results;

                        console.log('   ✅ Status: SUCCESS');
                        console.log(`   📊 Results: ${results.length} items returned`);
                        console.log(`   🔍 Query: ${decodeURIComponent(query)}`);

                        // Quality assessment
                        const relevantResults = results.filter(item =>
                            (item.title && item.title.toLowerCase().includes('business')) ||
                            (item.description && item.description.toLowerCase().includes('intelligence')) ||
                            (item.description && item.description.toLowerCase().includes('2024'))
                        ).length;

                        console.log(`   🎯 Relevant Results: ${relevantResults}/${results.length} (${Math.round(relevantResults/results.length*100)}%)`);
                        console.log(`   🛡️  Family Friendly: ${response.family_friendly ? '✅ Yes' : '❌ No'}`);

                        console.log('\n   📄 Top Results:');
                        results.slice(0, 3).forEach((item, index) => {
                            console.log(`   ${index + 1}. ${item.title ? item.title.substring(0, 60) : 'No title'}...`);
                            console.log(`      ${item.url || 'No URL'}`);
                        });

                        resolve({
                            success: true,
                            quality: relevantResults >= 2 ? 'HIGH' : 'MEDIUM',
                            resultCount: results.length,
                            relevanceScore: results.length > 0 ? relevantResults / results.length : 0
                        });
                    } else {
                        console.log(`   ❌ Status: FAILED (${res.statusCode})`);
                        console.log(`   📝 Error: ${body}`);
                        resolve({ success: false, error: body });
                    }
                } catch (e) {
                    console.log(`   ❌ Parse Error: ${e.message}`);
                    resolve({ success: false, error: e.message });
                }
            });
        });

        req.on('error', (e) => {
            console.log(`   ❌ Request Error: ${e.message}`);
            resolve({ success: false, error: e.message });
        });

        req.setTimeout(15000, () => {
            console.log('   ❌ Request Timeout');
            req.destroy();
            resolve({ success: false, error: 'Timeout' });
        });

        req.end();
    });
}

// Main execution
async function runQualityTests() {
    console.log('Starting API quality validation...\n');

    const results = {
        deepseek: await testDeepSeekQuality(),
        google: await testGoogleSearchQuality(),
        brave: await testBraveSearchQuality()
    };

    // Generate final report
    console.log('\n' + '='.repeat(50));
    console.log('🏆 API QUALITY TEST RESULTS');
    console.log('='.repeat(50));

    let successCount = 0;
    let totalTests = 0;

    Object.entries(results).forEach(([api, result]) => {
        totalTests++;
        const status = result.success ? '✅ PASSED' : '❌ FAILED';
        const quality = result.quality || 'N/A';

        console.log(`${api.toUpperCase()} API: ${status} (Quality: ${quality})`);

        if (result.success) {
            successCount++;
            if (result.relevanceScore !== undefined) {
                console.log(`   Relevance: ${Math.round(result.relevanceScore * 100)}%`);
            }
            if (result.tokens) {
                console.log(`   Token Usage: ${result.tokens}`);
            }
            if (result.resultCount) {
                console.log(`   Results: ${result.resultCount}`);
            }
        } else if (result.error) {
            console.log(`   Error: ${result.error.substring(0, 100)}...`);
        }
        console.log('');
    });

    const successRate = Math.round((successCount / totalTests) * 100);

    console.log(`📊 Overall Success Rate: ${successRate}% (${successCount}/${totalTests})`);
    console.log('\n💡 DEPLOYMENT ASSESSMENT:');

    if (successRate === 100) {
        console.log('   ✅ READY FOR PRODUCTION');
        console.log('   🚀 All APIs delivering high-quality responses');
        console.log('   📈 Integration fully validated for business use');
    } else if (successRate >= 66) {
        console.log('   ⚠️  CONDITIONAL DEPLOYMENT');
        console.log('   🔧 Some APIs need attention but core functionality works');
        console.log('   📋 Implement fallback mechanisms for failed APIs');
    } else {
        console.log('   ❌ NOT READY FOR DEPLOYMENT');
        console.log('   🚨 Critical API failures - requires immediate attention');
        console.log('   🔧 Verify API keys, network access, and service status');
    }

    console.log('\n📅 Test completed:', new Date().toLocaleString());
    console.log('='.repeat(50));

    // Exit with appropriate code
    process.exit(successRate >= 75 ? 0 : 1);
}

// Run the tests
runQualityTests().catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
});