#!/usr/bin/env node

const https = require('https');
const zlib = require('zlib');

const BRAVE_API_KEY = 'BSAkNrh316HK8uxqGjUN1_eeLon8PfO';

console.log('🦁 Testing Brave Search API with Proper Decompression');

async function testBraveSearchFixed() {
    const query = encodeURIComponent('business intelligence trends 2024');

    const options = {
        hostname: 'api.search.brave.com',
        port: 443,
        path: `/res/v1/web/search?q=${query}&count=3&mkt=en-US`,
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'X-Subscription-Token': BRAVE_API_KEY
            // Removed Accept-Encoding: gzip to avoid compression issues
        }
    };

    return new Promise((resolve) => {
        const req = https.request(options, (res) => {
            let body = '';

            res.on('data', (chunk) => {
                body += chunk;
            });

            res.on('end', () => {
                try {
                    console.log(`Response Status: ${res.statusCode}`);
                    console.log(`Response Headers:`, res.headers);

                    if (res.statusCode === 200) {
                        const response = JSON.parse(body);

                        if (response.web && response.web.results) {
                            const results = response.web.results;
                            console.log('✅ Brave Search API: SUCCESS');
                            console.log(`📊 Results: ${results.length} items returned`);

                            results.forEach((item, index) => {
                                console.log(`${index + 1}. ${item.title || 'No title'}`);
                                console.log(`   ${item.url || 'No URL'}`);
                                console.log(`   ${(item.description || '').substring(0, 100)}...`);
                            });

                            resolve({ success: true, count: results.length });
                        } else {
                            console.log('❌ No results in response structure');
                            console.log('Response body:', body.substring(0, 500));
                            resolve({ success: false, error: 'No results structure' });
                        }
                    } else {
                        console.log(`❌ HTTP Error ${res.statusCode}`);
                        console.log('Response body:', body);
                        resolve({ success: false, error: `HTTP ${res.statusCode}` });
                    }
                } catch (e) {
                    console.log(`❌ Parse Error: ${e.message}`);
                    console.log('Raw response:', body.substring(0, 200));
                    resolve({ success: false, error: e.message });
                }
            });
        });

        req.on('error', (e) => {
            console.log(`❌ Request Error: ${e.message}`);
            resolve({ success: false, error: e.message });
        });

        req.setTimeout(15000, () => {
            console.log('❌ Request Timeout');
            req.destroy();
            resolve({ success: false, error: 'Timeout' });
        });

        req.end();
    });
}

// Run the test
testBraveSearchFixed().then(result => {
    console.log('\n' + '='.repeat(40));
    console.log(`Final Result: ${result.success ? '✅ SUCCESS' : '❌ FAILED'}`);
    if (result.error) {
        console.log(`Error: ${result.error}`);
    }
    if (result.count) {
        console.log(`Results returned: ${result.count}`);
    }
    console.log('='.repeat(40));
});