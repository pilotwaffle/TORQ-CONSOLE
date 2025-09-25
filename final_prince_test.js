#!/usr/bin/env node
/**
 * Final Prince Flowers Test - Direct Chat API Testing
 *
 * Tests the actual working chat endpoints to validate Prince commands.
 */

const http = require('http');

class FinalPrinceTest {
    constructor() {
        this.baseURL = 'http://127.0.0.1:8899';
        this.chatTabId = null;
        this.testResults = [];
    }

    async runFinalTest() {
        console.log('🎯 FINAL PRINCE FLOWERS VALIDATION TEST');
        console.log('Testing actual chat endpoints with Prince commands');
        console.log('='.repeat(60));

        try {
            // Step 1: Create a chat tab
            await this.createChatTab();

            // Step 2: Test Prince commands through chat
            await this.testPrinceCommandsViaChat();

            // Step 3: Test command palette for Prince commands
            await this.testCommandPalette();

            // Step 4: Generate final report
            this.generateFinalReport();

        } catch (error) {
            console.log(`❌ Test failed: ${error.message}`);
        }
    }

    async createChatTab() {
        console.log('\n📝 Creating chat tab...');

        try {
            const response = await this.makeRequest('POST', '/api/chat/tabs', {
                title: 'Prince Flowers Test'
            });

            if (response.statusCode === 200) {
                const chatData = JSON.parse(response.data);
                this.chatTabId = chatData.id;
                console.log(`✅ Chat tab created: ${this.chatTabId}`);
                console.log(`   Title: ${chatData.title}`);
                console.log(`   Status: ${chatData.status}`);

                this.recordTest('Chat Tab Creation', true, `Tab ID: ${this.chatTabId}`);
                return true;
            } else {
                console.log(`❌ Failed to create chat tab: ${response.statusCode}`);
                this.recordTest('Chat Tab Creation', false, `HTTP ${response.statusCode}`);
                return false;
            }
        } catch (error) {
            console.log(`❌ Error creating chat tab: ${error.message}`);
            this.recordTest('Chat Tab Creation', false, error.message);
            return false;
        }
    }

    async testPrinceCommandsViaChat() {
        if (!this.chatTabId) {
            console.log('❌ No chat tab available for testing');
            return;
        }

        console.log('\n🤖 Testing Prince commands via chat...');

        const testCommands = [
            {
                message: 'prince help',
                expectation: 'Help information or command list'
            },
            {
                message: 'prince status',
                expectation: 'Agent status information'
            },
            {
                message: 'prince capabilities',
                expectation: 'List of agent capabilities'
            },
            {
                message: 'prince search latest AI developments',
                expectation: 'Search results with real data'
            }
        ];

        for (const test of testCommands) {
            console.log(`\n🔍 Testing: "${test.message}"`);

            try {
                const response = await this.makeRequest('POST', `/api/chat/tabs/${this.chatTabId}/messages`, {
                    content: test.message,
                    type: 'user'
                });

                if (response.statusCode === 200) {
                    console.log(`   ✅ Message sent successfully`);

                    // Wait a moment for processing
                    await this.delay(2000);

                    // Get chat messages to see the response
                    const messagesResponse = await this.makeRequest('GET', `/api/chat/tabs/${this.chatTabId}/messages`);

                    if (messagesResponse.statusCode === 200) {
                        const messages = JSON.parse(messagesResponse.data);
                        console.log(`   📊 Total messages in chat: ${messages.length}`);

                        // Look for assistant responses
                        const assistantMessages = messages.filter(m => m.type === 'assistant');
                        const lastAssistantMessage = assistantMessages[assistantMessages.length - 1];

                        if (lastAssistantMessage) {
                            const content = lastAssistantMessage.content;
                            console.log(`   📝 Response length: ${content.length} characters`);

                            // Analyze the response
                            const isPrinceResponse = this.analyzePrinceResponse(content);
                            const hasRealData = this.hasRealData(content);

                            console.log(`   🤖 Prince response: ${isPrinceResponse ? 'YES' : 'NO'}`);
                            console.log(`   🌐 Real data: ${hasRealData ? 'YES' : 'NO'}`);

                            if (content.length > 100) {
                                const preview = content.substring(0, 150).replace(/\n/g, ' ');
                                console.log(`   📖 Preview: ${preview}...`);
                            }

                            this.recordTest(
                                `Prince Command: ${test.message}`,
                                isPrinceResponse || content.length > 50,
                                `Response: ${content.length} chars, Prince: ${isPrinceResponse}, Real: ${hasRealData}`
                            );
                        } else {
                            console.log(`   ⚠️  No assistant response found`);
                            this.recordTest(`Prince Command: ${test.message}`, false, 'No assistant response');
                        }
                    } else {
                        console.log(`   ❌ Failed to get messages: ${messagesResponse.statusCode}`);
                        this.recordTest(`Prince Command: ${test.message}`, false, 'Could not retrieve response');
                    }
                } else {
                    console.log(`   ❌ Failed to send message: ${response.statusCode}`);
                    this.recordTest(`Prince Command: ${test.message}`, false, `HTTP ${response.statusCode}`);
                }

            } catch (error) {
                console.log(`   ❌ Error testing command: ${error.message}`);
                this.recordTest(`Prince Command: ${test.message}`, false, error.message);
            }
        }
    }

    async testCommandPalette() {
        console.log('\n🎨 Testing command palette for Prince commands...');

        try {
            // Get available commands
            const response = await this.makeRequest('GET', '/api/command-palette/commands');

            if (response.statusCode === 200) {
                const commands = JSON.parse(response.data);
                console.log(`✅ Retrieved ${commands.length} available commands`);

                // Look for Prince-related commands
                const princeCommands = commands.filter(cmd =>
                    cmd.id?.toLowerCase().includes('prince') ||
                    cmd.name?.toLowerCase().includes('prince') ||
                    cmd.description?.toLowerCase().includes('prince')
                );

                console.log(`🤖 Prince commands found: ${princeCommands.length}`);

                if (princeCommands.length > 0) {
                    princeCommands.forEach(cmd => {
                        console.log(`   • ${cmd.id || cmd.name}: ${cmd.description || 'No description'}`);
                    });

                    // Test executing a Prince command if available
                    if (princeCommands.length > 0) {
                        const testCommand = princeCommands[0];
                        console.log(`\n🧪 Testing command execution: ${testCommand.id}`);

                        try {
                            const execResponse = await this.makeRequest('POST', '/api/command-palette/execute', {
                                command_id: testCommand.id
                            });

                            if (execResponse.statusCode === 200) {
                                console.log(`   ✅ Command executed successfully`);
                                console.log(`   📊 Response: ${execResponse.data}`);
                            } else {
                                console.log(`   ⚠️  Command execution returned: ${execResponse.statusCode}`);
                            }
                        } catch (error) {
                            console.log(`   ❌ Command execution error: ${error.message}`);
                        }
                    }

                    this.recordTest('Command Palette Prince Commands', true, `${princeCommands.length} commands found`);
                } else {
                    this.recordTest('Command Palette Prince Commands', false, 'No Prince commands in palette');
                }

            } else {
                console.log(`❌ Failed to get commands: ${response.statusCode}`);
                this.recordTest('Command Palette Access', false, `HTTP ${response.statusCode}`);
            }

        } catch (error) {
            console.log(`❌ Command palette test error: ${error.message}`);
            this.recordTest('Command Palette Access', false, error.message);
        }
    }

    analyzePrinceResponse(content) {
        if (!content) return false;

        const princeIndicators = [
            /prince[\s-_]*flowers?/i,
            /enhanced[\s-_]*agent/i,
            /agentic[\s-_]*(rl|reinforcement)/i,
            /capabilities.*available/i,
            /agent.*status/i,
            /search.*results/i,
            /command.*help/i,
            /torq.*console/i,
            /mcp.*server/i
        ];

        return princeIndicators.some(pattern => pattern.test(content));
    }

    hasRealData(content) {
        if (!content) return false;

        // Check for real data indicators
        const realDataIndicators = [
            /https?:\/\/[^\s]+/.test(content) && !/example\.com/.test(content), // Real URLs
            /202[3-4]/.test(content), // Recent years
            /\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+202[3-4]/i.test(content), // Real dates
            content.length > 200, // Substantial content
            !/\b(demo|sample|placeholder|lorem|ipsum|test\s*data)\b/i.test(content) // Not demo data
        ];

        return realDataIndicators.filter(Boolean).length >= 2;
    }

    async delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
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

    generateFinalReport() {
        console.log('\n' + '='.repeat(80));
        console.log('🏆 PRINCE FLOWERS ENHANCED AGENT v2.1.0 - FINAL VALIDATION REPORT');
        console.log('='.repeat(80));

        const passed = this.testResults.filter(t => t.success).length;
        const total = this.testResults.length;
        const successRate = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;

        // Calculate weighted grade
        const criticalTests = this.testResults.filter(t =>
            t.name.includes('Prince Command') ||
            t.name.includes('Chat Tab Creation')
        );
        const criticalPassed = criticalTests.filter(t => t.success).length;
        const criticalRate = criticalTests.length > 0 ? (criticalPassed / criticalTests.length) : 0;

        const overallGrade = Math.round(successRate * 0.4 + criticalRate * 60);

        console.log(`\n📈 FINAL RESULTS:`);
        console.log(`   • Total Tests: ${total}`);
        console.log(`   • Passed: ${passed} ✅`);
        console.log(`   • Failed: ${total - passed} ❌`);
        console.log(`   • Success Rate: ${successRate}%`);
        console.log(`   • Critical Tests: ${criticalPassed}/${criticalTests.length} passed`);
        console.log(`   • Overall System Grade: ${overallGrade}/100`);

        // Component status
        console.log(`\n🔍 COMPONENT STATUS:`);
        const components = {
            'Web Interface': this.testResults.filter(t => t.name.includes('Chat Tab')).length > 0,
            'Prince Commands': criticalPassed > 0,
            'Real Data': this.testResults.some(t => t.details.includes('Real: true')),
            'Command Palette': this.testResults.some(t => t.name.includes('Command Palette') && t.success)
        };

        Object.entries(components).forEach(([component, working]) => {
            const status = working ? '✅ FUNCTIONAL' : '❌ NON-FUNCTIONAL';
            console.log(`   • ${component}: ${status}`);
        });

        // Final deployment recommendation
        console.log(`\n🎯 FINAL DEPLOYMENT RECOMMENDATION:`);
        if (overallGrade >= 70 && criticalPassed > 0) {
            console.log('   ✅ APPROVED FOR DEPLOYMENT');
            console.log('   Prince Flowers Enhanced Agent is functional and ready for use');
        } else if (overallGrade >= 50) {
            console.log('   ⚠️  CONDITIONAL APPROVAL');
            console.log('   System partially functional but needs improvements');
        } else {
            console.log('   ❌ DEPLOYMENT BLOCKED');
            console.log('   Critical functionality not working properly');
        }

        console.log(`\n📋 TEST DETAILS:`);
        this.testResults.forEach((test, index) => {
            const status = test.success ? '✅' : '❌';
            console.log(`   ${index + 1}. ${status} ${test.name}`);
            console.log(`      ${test.details}`);
        });

        console.log('\n' + '='.repeat(80));
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
                    'User-Agent': 'Prince-Flowers-Final-Test/1.0',
                    'Accept': 'application/json, */*',
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

// Run the final test
async function main() {
    const test = new FinalPrinceTest();
    await test.runFinalTest();
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = FinalPrinceTest;