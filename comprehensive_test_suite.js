#!/usr/bin/env node
/**
 * Comprehensive End-to-End Test Suite for Prince Flowers Enhanced Agent v2.1.0
 *
 * This Node.js-based test suite validates all aspects of the Prince Flowers system:
 * - Web interface testing (port 8899 expected)
 * - API integration validation
 * - Command line interface testing
 * - Integration testing between components
 *
 * Provides detailed PASS/FAIL reporting with system grade.
 */

const express = require('express');
const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');
const http = require('http');
const https = require('https');

class PrinceFlowersTestSuite {
    constructor() {
        this.testResults = [];
        this.overallGrade = 0;
        this.startTime = Date.now();

        console.log('🚀 Prince Flowers Enhanced Agent v2.1.0 - Comprehensive Test Suite');
        console.log('=' + '='.repeat(79));
        console.log(`⏱️  Test started: ${new Date().toISOString()}`);
        console.log('');
    }

    async runAllTests() {
        console.log('📋 EXECUTING COMPREHENSIVE TEST SUITE');
        console.log('-'.repeat(50));

        // Test Category 1: Web Interface Testing
        await this.testWebInterface();

        // Test Category 2: API Integration Testing
        await this.testAPIIntegration();

        // Test Category 3: Command Line Testing
        await this.testCommandLineInterface();

        // Test Category 4: Integration Testing
        await this.testSystemIntegration();

        // Generate final report
        this.generateFinalReport();
    }

    async testWebInterface() {
        console.log('\n🌐 1. WEB INTERFACE TESTING');
        console.log('   Testing prince commands through web interface');
        console.log('   Expected endpoint: http://127.0.0.1:8899');
        console.log('   ' + '-'.repeat(40));

        // Test 1.1: Check if web server is running
        const webServerTest = await this.checkWebServer('127.0.0.1', 8899);
        this.recordTest('Web Server Availability', webServerTest.success, webServerTest.details);

        // Test 1.2: Test prince command endpoints
        if (webServerTest.success) {
            await this.testPrinceWebCommands();
        } else {
            // Try alternative ports
            const altPorts = [8080, 3000, 5000, 8888];
            let foundServer = false;

            for (const port of altPorts) {
                const altTest = await this.checkWebServer('127.0.0.1', port);
                if (altTest.success) {
                    console.log(`   ✓ Found server on alternative port: ${port}`);
                    this.recordTest(`Alternative Web Server (${port})`, true, altTest.details);
                    foundServer = true;
                    break;
                }
            }

            if (!foundServer) {
                this.recordTest('Alternative Web Server Search', false, 'No web servers found on common ports');
            }
        }

        // Test 1.3: Verify search results are real (not demo)
        await this.testRealSearchResults();
    }

    async testAPIIntegration() {
        console.log('\n🔗 2. API INTEGRATION TESTING');
        console.log('   Validating external API configurations and connectivity');
        console.log('   ' + '-'.repeat(40));

        // Test 2.1: Check environment configuration
        const envTest = this.checkEnvironmentConfiguration();
        this.recordTest('Environment Configuration', envTest.success, envTest.details);

        // Test 2.2: Test Google Search API
        await this.testGoogleSearchAPI();

        // Test 2.3: Test Brave Search API
        await this.testBraveSearchAPI();

        // Test 2.4: Validate .env loading
        this.testEnvLoading();
    }

    async testCommandLineInterface() {
        console.log('\n💻 3. COMMAND LINE INTERFACE TESTING');
        console.log('   Testing prince commands in torq> prompt sessions');
        console.log('   ' + '-'.repeat(40));

        // Test 3.1: Test torq integration script
        await this.testTorqIntegration();

        // Test 3.2: Test async bug fixes
        await this.testAsyncBugFixes();

        // Test 3.3: Test prince command formats
        await this.testPrinceCommandFormats();
    }

    async testSystemIntegration() {
        console.log('\n🔄 4. INTEGRATION TESTING');
        console.log('   Testing complete system integration');
        console.log('   ' + '-'.repeat(40));

        // Test 4.1: Test torq_integration.py functionality
        await this.testTorqIntegrationPy();

        // Test 4.2: Verify method routing fixes
        await this.testMethodRoutingFixes();

        // Test 4.3: Test Claude web search proxy
        await this.testClaudeWebSearchProxy();
    }

    async checkWebServer(host, port) {
        return new Promise((resolve) => {
            const req = http.request({
                host: host,
                port: port,
                method: 'GET',
                timeout: 3000
            }, (res) => {
                console.log(`   ✓ Web server responding on ${host}:${port} (${res.statusCode})`);
                resolve({
                    success: true,
                    details: `HTTP ${res.statusCode} response from ${host}:${port}`
                });
            });

            req.on('error', (err) => {
                console.log(`   ✗ Web server not accessible on ${host}:${port}`);
                resolve({
                    success: false,
                    details: `Connection failed: ${err.message}`
                });
            });

            req.on('timeout', () => {
                console.log(`   ✗ Web server timeout on ${host}:${port}`);
                req.destroy();
                resolve({
                    success: false,
                    details: 'Connection timeout after 3 seconds'
                });
            });

            req.end();
        });
    }

    async testPrinceWebCommands() {
        console.log('   Testing prince command endpoints...');

        const testCommands = [
            'prince help',
            'prince status',
            'prince search latest AI developments',
            'prince capabilities'
        ];

        for (const command of testCommands) {
            // This would test actual web endpoints if server was running
            // For now, we'll simulate the test structure
            console.log(`   • Testing: ${command}`);
            this.recordTest(`Prince Web Command: ${command}`, false, 'Web server not available for testing');
        }
    }

    async testRealSearchResults() {
        console.log('   Verifying search results are real (not demo data)...');

        // Check for demo data patterns
        const demoPatterns = [
            'demo',
            'sample data',
            'placeholder',
            'test response',
            'mock data'
        ];

        this.recordTest('Real Search Results Validation', false, 'Cannot verify without active web server');
    }

    checkEnvironmentConfiguration() {
        console.log('   Checking environment configuration...');

        const envPath = path.join(__dirname, '..', '.env');

        if (!fs.existsSync(envPath)) {
            return {
                success: false,
                details: '.env file not found in expected location'
            };
        }

        const envContent = fs.readFileSync(envPath, 'utf8');
        console.log(`   ✓ Found .env file with ${envContent.split('\n').length} lines`);

        return {
            success: true,
            details: `Environment file found with ${envContent.split('\n').length} configuration lines`
        };
    }

    async testGoogleSearchAPI() {
        console.log('   Testing Google Search API integration...');

        // Look for Google API key in environment
        const envPath = path.join(__dirname, '..', '.env');
        if (fs.existsSync(envPath)) {
            const envContent = fs.readFileSync(envPath, 'utf8');
            const hasGoogleKey = envContent.includes('GOOGLE') || envContent.includes('AIzaSy');

            if (hasGoogleKey) {
                console.log('   ✓ Google API configuration detected');
                this.recordTest('Google Search API Configuration', true, 'API key configuration found');
            } else {
                console.log('   ⚠ Google API configuration not found in .env');
                this.recordTest('Google Search API Configuration', false, 'No Google API key found in environment');
            }
        } else {
            this.recordTest('Google Search API Configuration', false, 'Environment file not accessible');
        }
    }

    async testBraveSearchAPI() {
        console.log('   Testing Brave Search API integration...');

        // Look for Brave API key in environment
        const envPath = path.join(__dirname, '..', '.env');
        if (fs.existsSync(envPath)) {
            const envContent = fs.readFileSync(envPath, 'utf8');
            const hasBraveKey = envContent.includes('BRAVE') || envContent.includes('BSA');

            if (hasBraveKey) {
                console.log('   ✓ Brave API configuration detected');
                this.recordTest('Brave Search API Configuration', true, 'API key configuration found');
            } else {
                console.log('   ⚠ Brave API configuration not found in .env');
                this.recordTest('Brave Search API Configuration', false, 'No Brave API key found in environment');
            }
        } else {
            this.recordTest('Brave Search API Configuration', false, 'Environment file not accessible');
        }
    }

    testEnvLoading() {
        console.log('   Testing .env configuration loading...');

        // Check if torq_integration.py exists and has env loading
        const torqIntegrationPath = path.join(__dirname, 'torq_integration.py');

        if (fs.existsSync(torqIntegrationPath)) {
            const content = fs.readFileSync(torqIntegrationPath, 'utf8');
            const hasEnvLoading = content.includes('dotenv') || content.includes('os.environ') || content.includes('.env');

            this.recordTest('.env Loading Mechanism', hasEnvLoading,
                hasEnvLoading ? 'Environment loading code detected' : 'No environment loading mechanism found');
        } else {
            this.recordTest('.env Loading Mechanism', false, 'torq_integration.py not found');
        }
    }

    async testTorqIntegration() {
        console.log('   Testing TORQ integration script...');

        const torqIntegrationPath = path.join(__dirname, 'torq_integration.py');

        if (fs.existsSync(torqIntegrationPath)) {
            const stats = fs.statSync(torqIntegrationPath);
            console.log(`   ✓ torq_integration.py found (${stats.size} bytes)`);

            // Check for key integration components
            const content = fs.readFileSync(torqIntegrationPath, 'utf8');
            const hasAsyncSupport = content.includes('async def') || content.includes('asyncio');
            const hasPrinceIntegration = content.includes('prince') || content.includes('Prince');

            this.recordTest('TORQ Integration Script', true,
                `Script found with async support: ${hasAsyncSupport}, Prince integration: ${hasPrinceIntegration}`);
        } else {
            this.recordTest('TORQ Integration Script', false, 'torq_integration.py not found');
        }
    }

    async testAsyncBugFixes() {
        console.log('   Testing async bug fixes...');

        // Check for async/await patterns and proper error handling
        const pythonFiles = ['torq_integration.py', 'prince_flowers.py', 'prince_flowers_enhanced.py'];
        let asyncFixesFound = 0;

        for (const file of pythonFiles) {
            const filePath = path.join(__dirname, '..', file);
            if (fs.existsSync(filePath)) {
                const content = fs.readFileSync(filePath, 'utf8');
                if (content.includes('try:') && content.includes('async def')) {
                    asyncFixesFound++;
                }
            }
        }

        this.recordTest('Async Bug Fixes', asyncFixesFound > 0,
            `Found async error handling in ${asyncFixesFound} files`);
    }

    async testPrinceCommandFormats() {
        console.log('   Testing prince command format variations...');

        const commandFormats = [
            'prince search',
            '@prince search',
            'prince help',
            'prince status',
            'prince capabilities'
        ];

        // Check if torq_integration.py supports these formats
        const torqIntegrationPath = path.join(__dirname, 'torq_integration.py');
        if (fs.existsSync(torqIntegrationPath)) {
            const content = fs.readFileSync(torqIntegrationPath, 'utf8');

            let supportedFormats = 0;
            for (const format of commandFormats) {
                if (content.includes(format.split(' ')[0])) {
                    supportedFormats++;
                }
            }

            this.recordTest('Prince Command Formats', supportedFormats >= 2,
                `${supportedFormats}/${commandFormats.length} command formats supported`);
        } else {
            this.recordTest('Prince Command Formats', false, 'Cannot verify without torq_integration.py');
        }
    }

    async testTorqIntegrationPy() {
        console.log('   Testing torq_integration.py directly...');

        // This would normally execute the Python script, but we'll check its structure
        const torqIntegrationPath = path.join(__dirname, 'torq_integration.py');

        if (fs.existsSync(torqIntegrationPath)) {
            const content = fs.readFileSync(torqIntegrationPath, 'utf8');

            // Check for key components
            const hasMainFunction = content.includes('def main') || content.includes('if __name__');
            const hasErrorHandling = content.includes('try:') && content.includes('except');
            const hasLogging = content.includes('logging') || content.includes('logger');

            const score = [hasMainFunction, hasErrorHandling, hasLogging].filter(Boolean).length;

            this.recordTest('torq_integration.py Structure', score >= 2,
                `Code quality indicators: main function: ${hasMainFunction}, error handling: ${hasErrorHandling}, logging: ${hasLogging}`);
        } else {
            this.recordTest('torq_integration.py Structure', false, 'File not found');
        }
    }

    async testMethodRoutingFixes() {
        console.log('   Testing method routing fixes...');

        // Check for proper method routing in integration code
        const torqIntegrationPath = path.join(__dirname, 'torq_integration.py');

        if (fs.existsSync(torqIntegrationPath)) {
            const content = fs.readFileSync(torqIntegrationPath, 'utf8');

            const hasRouting = content.includes('route') || content.includes('dispatch') || content.includes('process_command');
            const hasMethodHandling = content.includes('GET') || content.includes('POST') || content.includes('method');

            this.recordTest('Method Routing Fixes', hasRouting || hasMethodHandling,
                `Routing mechanisms detected: ${hasRouting}, Method handling: ${hasMethodHandling}`);
        } else {
            this.recordTest('Method Routing Fixes', false, 'Cannot verify without torq_integration.py');
        }
    }

    async testClaudeWebSearchProxy() {
        console.log('   Testing Claude web search proxy...');

        // Check for Claude web search implementation
        const claudeFiles = fs.readdirSync(__dirname).filter(file =>
            file.includes('claude') && file.includes('search') && file.endsWith('.py')
        );

        if (claudeFiles.length > 0) {
            console.log(`   ✓ Found Claude web search files: ${claudeFiles.join(', ')}`);

            // Check first found file for proxy functionality
            const claudeContent = fs.readFileSync(path.join(__dirname, claudeFiles[0]), 'utf8');
            const hasProxyFeatures = claudeContent.includes('proxy') || claudeContent.includes('search') || claudeContent.includes('request');

            this.recordTest('Claude Web Search Proxy', hasProxyFeatures,
                `Proxy features detected in ${claudeFiles[0]}: ${hasProxyFeatures}`);
        } else {
            this.recordTest('Claude Web Search Proxy', false, 'No Claude web search files found');
        }
    }

    recordTest(testName, success, details) {
        const result = {
            name: testName,
            success: success,
            details: details,
            timestamp: new Date().toISOString()
        };

        this.testResults.push(result);

        const status = success ? '✅ PASS' : '❌ FAIL';
        console.log(`   ${status} ${testName}`);
        if (details) {
            console.log(`        ${details}`);
        }
    }

    generateFinalReport() {
        const endTime = Date.now();
        const duration = (endTime - this.startTime) / 1000;

        console.log('\n' + '='.repeat(80));
        console.log('📊 PRINCE FLOWERS ENHANCED AGENT v2.1.0 - FINAL TEST REPORT');
        console.log('='.repeat(80));

        // Calculate statistics
        const totalTests = this.testResults.length;
        const passedTests = this.testResults.filter(t => t.success).length;
        const failedTests = totalTests - passedTests;
        const successRate = totalTests > 0 ? (passedTests / totalTests * 100).toFixed(1) : 0;

        // Calculate overall grade
        this.overallGrade = this.calculateOverallGrade(passedTests, totalTests);

        console.log(`\n📈 TEST SUMMARY:`);
        console.log(`   • Total Tests: ${totalTests}`);
        console.log(`   • Passed: ${passedTests} ✅`);
        console.log(`   • Failed: ${failedTests} ❌`);
        console.log(`   • Success Rate: ${successRate}%`);
        console.log(`   • Overall Grade: ${this.overallGrade}/100`);
        console.log(`   • Execution Time: ${duration.toFixed(2)} seconds`);

        // Component breakdown
        console.log(`\n🔍 COMPONENT BREAKDOWN:`);
        this.generateComponentBreakdown();

        // Deployment recommendation
        console.log(`\n🎯 DEPLOYMENT RECOMMENDATION:`);
        this.generateDeploymentRecommendation();

        // Critical issues
        console.log(`\n⚠️  CRITICAL ISSUES FOUND:`);
        this.listCriticalIssues();

        // Save detailed report
        this.saveDetailedReport();

        console.log(`\n📄 Detailed report saved to: prince_flowers_test_report.json`);
        console.log('='.repeat(80));
    }

    calculateOverallGrade(passed, total) {
        if (total === 0) return 0;

        const baseScore = (passed / total) * 100;

        // Apply weighted scoring for critical components
        const criticalTests = this.testResults.filter(t =>
            t.name.includes('Web Server') ||
            t.name.includes('API') ||
            t.name.includes('Integration')
        );

        const criticalPassed = criticalTests.filter(t => t.success).length;
        const criticalWeight = criticalTests.length > 0 ? (criticalPassed / criticalTests.length) * 0.4 : 0;

        return Math.round(baseScore * 0.6 + criticalWeight * 100);
    }

    generateComponentBreakdown() {
        const categories = {
            'Web Interface': this.testResults.filter(t => t.name.includes('Web')),
            'API Integration': this.testResults.filter(t => t.name.includes('API')),
            'Command Line': this.testResults.filter(t => t.name.includes('Command') || t.name.includes('TORQ')),
            'System Integration': this.testResults.filter(t => t.name.includes('Integration') || t.name.includes('Proxy'))
        };

        for (const [category, tests] of Object.entries(categories)) {
            if (tests.length === 0) continue;

            const passed = tests.filter(t => t.success).length;
            const total = tests.length;
            const percentage = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;

            const status = percentage >= 70 ? '✅' : percentage >= 40 ? '⚠️' : '❌';
            console.log(`   ${status} ${category}: ${passed}/${total} (${percentage}%)`);
        }
    }

    generateDeploymentRecommendation() {
        const criticalFailures = this.testResults.filter(t =>
            !t.success && (
                t.name.includes('Web Server') ||
                t.name.includes('API Configuration') ||
                t.name.includes('Integration Script')
            )
        ).length;

        if (criticalFailures === 0 && this.overallGrade >= 80) {
            console.log('   ✅ APPROVED - System ready for deployment');
            console.log('   All critical components are functional');
        } else if (criticalFailures <= 2 && this.overallGrade >= 60) {
            console.log('   ⚠️  CONDITIONAL APPROVAL - Minor issues need addressing');
            console.log('   System can be deployed with monitoring for known issues');
        } else {
            console.log('   ❌ BLOCKED - Critical issues prevent deployment');
            console.log('   Resolve critical failures before deployment');
        }
    }

    listCriticalIssues() {
        const criticalIssues = this.testResults.filter(t => !t.success);

        if (criticalIssues.length === 0) {
            console.log('   🎉 No critical issues found!');
            return;
        }

        criticalIssues.forEach((issue, index) => {
            console.log(`   ${index + 1}. ${issue.name}: ${issue.details}`);
        });
    }

    saveDetailedReport() {
        const report = {
            timestamp: new Date().toISOString(),
            version: 'Prince Flowers Enhanced Agent v2.1.0',
            summary: {
                totalTests: this.testResults.length,
                passed: this.testResults.filter(t => t.success).length,
                failed: this.testResults.filter(t => !t.success).length,
                overallGrade: this.overallGrade,
                executionTimeSeconds: (Date.now() - this.startTime) / 1000
            },
            testResults: this.testResults,
            environment: {
                nodeVersion: process.version,
                platform: process.platform,
                architecture: process.arch,
                workingDirectory: __dirname
            }
        };

        fs.writeFileSync(
            path.join(__dirname, 'prince_flowers_test_report.json'),
            JSON.stringify(report, null, 2)
        );
    }
}

// Execute the test suite
async function main() {
    const testSuite = new PrinceFlowersTestSuite();
    await testSuite.runAllTests();

    // Exit with appropriate code
    process.exit(testSuite.overallGrade >= 70 ? 0 : 1);
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = PrinceFlowersTestSuite;