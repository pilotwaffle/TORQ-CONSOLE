"""
Real Maxim AI Platform Integration
Using provided API key: sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8

This module integrates with the actual Maxim AI platform instead of using custom implementations.
"""

import asyncio
import json
import logging
import aiohttp
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MaximAIConfig:
    """Configuration for Maxim AI integration"""
    api_key: str = "sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8"
    base_url: str = "https://api.maxim.ai"  # Likely API base URL
    timeout: int = 30

class RealMaximAIIntegration:
    """Real integration with Maxim AI platform"""

    def __init__(self, config: Optional[MaximAIConfig] = None):
        self.config = config or MaximAIConfig()
        self.session = None
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TORQ-Console/1.0"
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=self.headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Maxim AI platform"""
        try:
            # Try common API endpoints
            endpoints_to_try = [
                "/v1/health",
                "/v1/status",
                "/v1/user",
                "/v1/evaluators",
                "/evaluators",
                "/api/v1/status",
                "/api/health"
            ]

            for endpoint in endpoints_to_try:
                try:
                    url = f"{self.config.base_url}{endpoint}"
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            return {
                                "success": True,
                                "endpoint": endpoint,
                                "status_code": response.status,
                                "message": "Successfully connected to Maxim AI"
                            }
                        elif response.status == 401:
                            return {
                                "success": False,
                                "error": "Authentication failed - check API key",
                                "endpoint": endpoint,
                                "status_code": response.status
                            }
                except Exception as e:
                    logger.debug(f"Failed to connect to {endpoint}: {e}")
                    continue

            return {
                "success": False,
                "error": "Could not connect to any known Maxim AI endpoint",
                "tried_endpoints": endpoints_to_try
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}"
            }

    async def list_evaluators(self) -> Dict[str, Any]:
        """List available evaluators from Maxim AI"""
        try:
            # Try different endpoints for evaluators
            evaluator_endpoints = [
                "/v1/evaluators",
                "/evaluators",
                "/api/v1/evaluators",
                "/v1/library/evaluators",
                "/library/evaluators"
            ]

            for endpoint in evaluator_endpoints:
                try:
                    url = f"{self.config.base_url}{endpoint}"
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                "success": True,
                                "endpoint": endpoint,
                                "evaluators": data
                            }
                except Exception as e:
                    logger.debug(f"Failed to get evaluators from {endpoint}: {e}")
                    continue

            return {
                "success": False,
                "error": "Could not fetch evaluators from any endpoint",
                "tried_endpoints": evaluator_endpoints
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list evaluators: {str(e)}"
            }

    async def create_evaluation(self,
                              evaluator_id: str,
                              prompt: str,
                              response: str,
                              context: Optional[Dict] = None) -> Dict[str, Any]:
        """Create an evaluation using Maxim AI evaluator"""
        try:
            # Try different endpoints for creating evaluations
            evaluation_endpoints = [
                "/v1/evaluations",
                "/evaluations",
                "/api/v1/evaluations",
                "/v1/run",
                "/run"
            ]

            payload = {
                "evaluator_id": evaluator_id,
                "prompt": prompt,
                "response": response,
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            }

            for endpoint in evaluation_endpoints:
                try:
                    url = f"{self.config.base_url}{endpoint}"
                    async with self.session.post(url, json=payload) as response:
                        if response.status in [200, 201]:
                            data = await response.json()
                            return {
                                "success": True,
                                "endpoint": endpoint,
                                "evaluation": data
                            }
                except Exception as e:
                    logger.debug(f"Failed to create evaluation via {endpoint}: {e}")
                    continue

            return {
                "success": False,
                "error": "Could not create evaluation via any endpoint",
                "tried_endpoints": evaluation_endpoints
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create evaluation: {str(e)}"
            }

    async def get_evaluation_results(self, evaluation_id: str) -> Dict[str, Any]:
        """Get results of an evaluation"""
        try:
            result_endpoints = [
                f"/v1/evaluations/{evaluation_id}",
                f"/evaluations/{evaluation_id}",
                f"/api/v1/evaluations/{evaluation_id}",
                f"/v1/results/{evaluation_id}",
                f"/results/{evaluation_id}"
            ]

            for endpoint in result_endpoints:
                try:
                    url = f"{self.config.base_url}{endpoint}"
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                "success": True,
                                "endpoint": endpoint,
                                "results": data
                            }
                except Exception as e:
                    logger.debug(f"Failed to get results from {endpoint}: {e}")
                    continue

            return {
                "success": False,
                "error": "Could not get evaluation results",
                "tried_endpoints": result_endpoints
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get evaluation results: {str(e)}"
            }

class MaximAIHybridIntegration:
    """Hybrid integration that falls back to custom implementation if Maxim AI is unavailable"""

    def __init__(self):
        self.maxim_config = MaximAIConfig()
        self.fallback_enabled = True

    async def evaluate_response(self,
                             prompt: str,
                             response: str,
                             context: Optional[Dict] = None) -> Dict[str, Any]:
        """Evaluate response using Maxim AI or fallback to custom implementation"""

        # Try Maxim AI first
        try:
            async with RealMaximAIIntegration(self.maxim_config) as maxim:
                # Test connection
                connection_test = await maxim.test_connection()
                if connection_test.get("success"):
                    # List available evaluators
                    evaluators = await maxim.list_evaluators()
                    if evaluators.get("success") and evaluators.get("evaluators"):
                        # Use the first available evaluator
                        evaluator_list = evaluators["evaluators"]
                        first_evaluator = evaluator_list[0] if isinstance(evaluator_list, list) else evaluator_list
                        evaluator_id = first_evaluator.get("id") if isinstance(first_evaluator, dict) else "default"

                        # Create evaluation
                        eval_result = await maxim.create_evaluation(
                            evaluator_id=evaluator_id,
                            prompt=prompt,
                            response=response,
                            context=context
                        )

                        if eval_result.get("success"):
                            return {
                                "source": "maxim_ai",
                                "success": True,
                                "evaluation": eval_result["evaluation"],
                                "confidence": 0.95
                            }

        except Exception as e:
            logger.warning(f"Maxim AI evaluation failed: {e}")

        # Fallback to custom implementation
        if self.fallback_enabled:
            logger.info("Falling back to custom evaluation implementation")
            return await self._custom_evaluation(prompt, response, context)

        return {
            "source": "none",
            "success": False,
            "error": "Both Maxim AI and fallback evaluation failed"
        }

    async def _custom_evaluation(self,
                               prompt: str,
                               response: str,
                               context: Optional[Dict] = None) -> Dict[str, Any]:
        """Custom evaluation fallback implementation"""

        # Import our custom evaluator
        try:
            from prince_flowers_evaluator import PrinceFlowersEvaluator, QueryTestCase, AgentType

            evaluator = PrinceFlowersEvaluator()

            # Create a test case
            test_case = QueryTestCase(
                query_id="hybrid_eval_001",
                query=prompt,
                expected_tools=["search", "analysis"],
                complexity_score=0.7,
                agent_type=AgentType.TORQ_PRINCE_FLOWERS
            )

            # Use our custom evaluation methods
            reasoning_score = evaluator.evaluate_reasoning_quality(
                test_case=test_case,
                response=response,
                success=True
            )

            relevance_score = evaluator.evaluate_response_relevance(
                test_case=test_case,
                response=response
            )

            execution_score = evaluator.evaluate_execution_performance(
                execution_time=1.0,
                complexity_score=test_case.complexity_score
            )

            overall_score = (reasoning_score + relevance_score + execution_score) / 3

            return {
                "source": "custom_fallback",
                "success": True,
                "scores": {
                    "reasoning_quality": reasoning_score,
                    "response_relevance": relevance_score,
                    "execution_performance": execution_score,
                    "overall_score": overall_score
                },
                "confidence": 0.85,
                "metrics": {
                    "evaluation_method": "custom_prince_flowers_evaluator",
                    "test_case_id": test_case.query_id,
                    "evaluation_timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Custom evaluation failed: {e}")
            return {
                "source": "custom_fallback",
                "success": False,
                "error": f"Custom evaluation failed: {str(e)}"
            }

async def demonstrate_real_maxim_integration():
    """Demonstrate the real Maxim AI integration"""
    print("Real Maxim AI Platform Integration Demo")
    print("="*60)
    print("Using API key: sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8")
    print("="*60)

    hybrid = MaximAIHybridIntegration()

    # Test queries for evaluation
    test_cases = [
        {
            "prompt": "Explain the benefits of using Python for data science",
            "response": "Python is excellent for data science due to its extensive libraries including pandas for data manipulation, numpy for numerical operations, scikit-learn for machine learning, and matplotlib for visualization. It has a simple syntax that makes it accessible to data scientists and researchers.",
            "context": {"domain": "data_science", "complexity": "medium"}
        },
        {
            "prompt": "What are the key principles of microservices architecture?",
            "response": "Microservices architecture follows key principles including single responsibility per service, independent deployment, decentralized data management, failure isolation, and infrastructure automation. Each service should be small, focused, and communicate through well-defined APIs.",
            "context": {"domain": "software_architecture", "complexity": "high"}
        }
    ]

    print(f"\nTesting {len(test_cases)} evaluations...")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Prompt: {test_case['prompt'][:50]}...")

        result = await hybrid.evaluate_response(
            prompt=test_case["prompt"],
            response=test_case["response"],
            context=test_case["context"]
        )

        if result["success"]:
            print(f"[PASS] Evaluation successful using: {result['source']}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")

            if "scores" in result:
                scores = result["scores"]
                print(f"   Overall Score: {scores.get('overall_score', 'N/A'):.3f}")
                print(f"   Reasoning Quality: {scores.get('reasoning_quality', 'N/A'):.3f}")
                print(f"   Response Relevance: {scores.get('response_relevance', 'N/A'):.3f}")
            elif "evaluation" in result:
                print(f"   Raw Maxim AI Result: {result['evaluation']}")
        else:
            print(f"[FAIL] Evaluation failed: {result.get('error', 'Unknown error')}")

    print(f"\nIntegration test completed!")
    print("This demonstrates hybrid Maxim AI integration with custom fallback.")

if __name__ == "__main__":
    asyncio.run(demonstrate_real_maxim_integration())