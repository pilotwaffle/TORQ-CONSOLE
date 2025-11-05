#!/usr/bin/env python3
"""
Simple test runner for Prince Flowers + Llama + Azure Research
Doesn't require pytest to be installed
"""

import sys
import asyncio
import os
from datetime import datetime
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 100)
print(" " * 20 + "PRINCE FLOWERS + LLAMA + AZURE RESEARCH TEST")
print("=" * 100)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)

try:
    print("\n[1/3] Importing modules...")
    from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
    from torq_console.llm.providers.ollama import OllamaProvider
    from torq_console.llm.providers.llama_cpp_provider import LlamaCppProvider
    print("✓ Imports successful")

    print("\n[2/3] Initializing LLM Provider...")

    # Try Ollama first
    try:
        print("  Trying Ollama (http://localhost:11434)...")
        llm_provider = OllamaProvider(
            base_url="http://localhost:11434",
            default_model="llama3.2"
        )
        provider_name = "Ollama (llama3.2)"
        print(f"  ✓ Connected to {provider_name}")
    except Exception as e:
        print(f"  ✗ Ollama failed: {e}")
        print("  Trying llama.cpp...")

        model_path = os.getenv('LLAMA_CPP_MODEL_PATH')
        if model_path and os.path.exists(model_path):
            llm_provider = LlamaCppProvider(
                model_path=model_path,
                n_gpu_layers=int(os.getenv('LLAMA_CPP_N_GPU_LAYERS', '28')),
                n_ctx=int(os.getenv('LLAMA_CPP_N_CTX', '2048'))
            )
            provider_name = f"llama.cpp ({os.path.basename(model_path)})"
            print(f"  ✓ Connected to {provider_name}")
        else:
            raise Exception("No Llama provider available (Ollama not running, llama.cpp not configured)")

    print(f"\n[3/3] Initializing Prince Flowers Agent...")
    agent = TORQPrinceFlowers(
        llm_provider=llm_provider,
        config={
            'enhanced_mode': True,
            'max_search_results': 10
        }
    )
    print("✓ Agent initialized")

    async def run_test():
        """Run the Azure research test"""
        print("\n" + "=" * 100)
        print("RESEARCH QUERY")
        print("=" * 100)

        query = "Research the 12 months of free services from Azure portal. What services are available at https://portal.azure.com for free tier customers?"
        print(f"Query: {query}")
        print("\nExecuting research... (this may take a few minutes)")

        start_time = datetime.now()
        result = await agent.process_query(
            query=query,
            context={}
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 100)
        print("RESULTS")
        print("=" * 100)

        print(f"\nSuccess: {result.success}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Tools used: {result.tools_used}")
        print(f"Execution time: {result.execution_time:.2f}s")
        print(f"Total duration: {duration:.2f}s")
        print(f"Reasoning mode: {result.reasoning_mode}")

        print("\n" + "=" * 100)
        print("CONTENT")
        print("=" * 100)
        print(result.content)

        print("\n" + "=" * 100)
        print("VERIFICATION")
        print("=" * 100)

        # Verify results
        checks = {
            "Success": result.success,
            "Has content": len(result.content) > 100,
            "Confidence > 0.2": result.confidence > 0.2,
            "Contains 'Azure'": 'azure' in result.content.lower(),
            "Tools used": len(result.tools_used) > 0,
        }

        passed = 0
        failed = 0

        for check_name, check_result in checks.items():
            status = "✓ PASS" if check_result else "✗ FAIL"
            print(f"{status}: {check_name}")
            if check_result:
                passed += 1
            else:
                failed += 1

        print("\n" + "=" * 100)
        print(f"SUMMARY: {passed} passed, {failed} failed")
        print("=" * 100)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)

        return failed == 0

    # Run the async test
    success = asyncio.run(run_test())

    sys.exit(0 if success else 1)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 100)
    sys.exit(1)
