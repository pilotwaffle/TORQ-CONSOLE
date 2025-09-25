"""
FINAL INTEGRATION: PrinceFlowers Enhanced for TORQ Console
This script demonstrates how to integrate the enhanced PrinceFlowers agent
with agentic RL capabilities into your existing TORQ Console system.
"""

import asyncio
import json
from typing import Dict, Any
from torq_integration import PrinceFlowersAgent

class TORQConsoleWithPrinceFlowers:
    """
    Enhanced TORQ Console with PrinceFlowers integration
    Demonstrates how to add the agent to your existing system
    """
    
    def __init__(self):
        self.prince_flowers = PrinceFlowersAgent()
        self.active_agent = "PrinceFlowers"
        print("🌟 TORQ Console enhanced with PrinceFlowers Agent")
        print(f"✅ Agent Status: {'Ready' if self.prince_flowers.available else 'Unavailable'}")
    
    async def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process commands through PrinceFlowers with full agentic RL
        """
        print(f"\n🔄 Processing with {self.active_agent}: {command}")
        
        # Route to PrinceFlowers for enhanced processing
        result = await self.prince_flowers.process_query(command)
        
        if result["success"]:
            print(f"✨ {result['response']}")
            
            # Show agentic RL metrics
            metadata = result.get("metadata", {})
            print(f"\n📊 Agentic RL Performance:")
            print(f"   🧠 Reasoning steps: {metadata.get('reasoning_steps', 0)}")
            print(f"   🛠️ Tool calls: {metadata.get('tool_calls', 0)}")
            print(f"   ⏱️ Execution time: {metadata.get('execution_time', 0):.2f}s")
            print(f"   🎯 Confidence: {metadata.get('confidence', 0):.2f}")
            
            # Show reasoning chain
            reasoning = metadata.get('reasoning_chain', [])
            if reasoning and len(reasoning) > 1:
                print(f"\n🔗 Agentic Reasoning Chain:")
                for i, step in enumerate(reasoning[:3], 1):
                    print(f"   {i}. [{step['type'].upper()}] {step['content'][:50]}...")
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    async def demonstrate_capabilities(self):
        """
        Demonstrate key agentic RL capabilities
        """
        print("\n" + "="*60)
        print("🚀 PRINCE FLOWERS AGENTIC RL DEMONSTRATION")
        print("="*60)
        
        demos = [
            {
                "title": "🔍 Web Search with Tool Integration",
                "query": "search for latest agentic reinforcement learning research"
            },
            {
                "title": "🧠 Multi-Step Analysis with Chain-of-Thought",
                "query": "analyze how the ARTIST framework improves LLM tool usage"
            },
            {
                "title": "🔧 Complex Research with Self-Correction",
                "query": "find and analyze information about GRPO algorithm performance"
            },
            {
                "title": "🎯 Direct Response with Adaptive Planning",
                "query": "what are your agentic RL capabilities?"
            }
        ]
        
        for demo in demos:
            print(f"\n{demo['title']}")
            print("-" * 50)
            await self.process_command(demo['query'])
            print()  # Space between demos
        
        # Show final agent status
        status = await self.prince_flowers.get_status()
        print("\n📈 FINAL AGENT STATUS:")
        print(f"   🎯 Success Rate: {status['performance'].get('success_rate', 0):.1%}")
        print(f"   🔢 Total Interactions: {status['performance'].get('total_interactions', 0)}")
        print(f"   🧠 Experience Buffer: {status['performance'].get('experience_buffer_size', 0)} experiences")
        print(f"   🛠️ Available Tools: {len(status['capabilities'])} integrated")
        
        print(f"\n✨ Agentic Features:")
        for feature in status.get('agentic_features', []):
            print(f"   • {feature}")

async def main():
    """
    Main demonstration of TORQ Console with PrinceFlowers
    """
    console = TORQConsoleWithPrinceFlowers()
    
    print("\n🎮 TORQ Console with PrinceFlowers Enhanced")
    print("Type 'demo' for full demonstration, or enter queries directly")
    print("Type 'quit' to exit")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n🌸 TORQ> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye from TORQ Console!")
                break
            
            if user_input.lower() == 'demo':
                await console.demonstrate_capabilities()
                continue
            
            if user_input.lower() == 'status':
                status = await console.prince_flowers.get_status()
                print(json.dumps(status, indent=2))
                continue
            
            if not user_input:
                continue
            
            await console.process_command(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye from TORQ Console!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")

# Quick integration test
async def integration_test():
    """
    Quick test to verify integration works
    """
    print("🧪 Running PrinceFlowers Integration Test...")
    
    console = TORQConsoleWithPrinceFlowers()
    
    # Test key capabilities
    test_queries = [
        "search for AI agent research",
        "analyze reinforcement learning benefits", 
        "what tools do you have available?"
    ]
    
    success_count = 0
    for query in test_queries:
        print(f"\n🔬 Testing: {query}")
        result = await console.process_command(query)
        if result["success"]:
            success_count += 1
    
    print(f"\n✅ Integration Test Results: {success_count}/{len(test_queries)} successful")
    print(f"🎯 Success Rate: {success_count/len(test_queries)*100:.0f}%")
    
    if success_count == len(test_queries):
        print("🌟 PrinceFlowers is fully integrated and ready for TORQ Console!")
    else:
        print("⚠️ Some tests failed - check configuration")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(integration_test())
    else:
        asyncio.run(main())
