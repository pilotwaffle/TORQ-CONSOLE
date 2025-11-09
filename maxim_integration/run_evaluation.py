"""
Prince Flowers Evaluation Runner
Execute the comprehensive evaluation system to establish baseline metrics
"""

import asyncio
import sys
import os
import logging

# Add TORQ Console to path
sys.path.insert(0, 'E:/TORQ-CONSOLE')

from prince_flowers_evaluator import PrinceFlowersEvaluator, EvaluationMetric

async def run_baseline_evaluation():
    """Run baseline evaluation of Prince Flowers agents"""

    print("🎯 PHASE 1: MAXIM AI INTEGRATION - BASELINE EVALUATION")
    print("=" * 80)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Initialize evaluator
        print("\n📋 Initializing Prince Flowers Evaluator...")
        evaluator = PrinceFlowersEvaluator()

        # Check available agents
        print(f"\n🤖 Available Agents: {list(evaluator.agents.keys())}")

        # Run comprehensive evaluation
        print("\n🚀 Running comprehensive evaluation...")
        print("   This will test all agents with various query types")
        print("   and establish baseline metrics using Maxim AI methodology")

        summary = await evaluator.run_comprehensive_evaluation()

        if summary:
            # Print detailed results
            evaluator.print_evaluation_summary(summary)

            # Save baseline for future comparisons
            await save_baseline_metrics(summary)

            print(f"\n✅ BASELINE EVALUATION COMPLETED SUCCESSFULLY")
            print(f"   📊 Overall Quality Score: {summary.overall_quality_score:.1%}")
            print(f"   📈 Results saved for future comparison")

            return summary
        else:
            print("❌ Evaluation failed - no summary returned")
            return None

    except Exception as e:
        logging.error(f"Evaluation execution failed: {e}")
        print(f"❌ Evaluation failed: {e}")
        return None

async def save_baseline_metrics(summary):
    """Save baseline metrics for future comparison"""
    baseline_data = {
        "evaluation_type": "baseline",
        "timestamp": summary.evaluation_timestamp.isoformat(),
        "overall_quality_score": summary.overall_quality_score,
        "success_rate": summary.success_rate,
        "average_execution_time": summary.average_execution_time,
        "average_confidence": summary.average_confidence,
        "metric_scores": {metric.value: score for metric, score in summary.metric_scores.items()},
        "agent_performance": {agent.value: performance for agent, performance in summary.agent_performance.items()},
        "total_queries_tested": summary.total_queries,
        "recommendations": summary.recommendations
    }

    # Save baseline file
    baseline_file = "E:/TORQ-CONSOLE/maxim_integration/baseline_metrics.json"
    os.makedirs(os.path.dirname(baseline_file), exist_ok=True)

    import json
    with open(baseline_file, 'w') as f:
        json.dump(baseline_data, f, indent=2)

    print(f"📁 Baseline metrics saved to: {baseline_file}")

def print_evaluation_introduction():
    """Print evaluation introduction"""
    print("""
🤖 PRINCE FLOWERS AGENT EVALUATION
Maxim AI Integration - Phase 1

This evaluation will assess the performance of TORQ Console's Prince Flowers agents
using Maxim AI's comprehensive evaluation methodology.

📊 EVALUATION METRICS:
• Reasoning Quality - Quality of logical reasoning and analysis
• Response Relevance - How well responses address user queries
• Tool Selection Efficiency - Appropriateness of tool usage
• Multi-step Accuracy - Accuracy of complex reasoning processes
• Execution Performance - Speed and efficiency
• Error Handling - Graceful error management
• Confidence Calibration - Accuracy of confidence scores

🎯 AGENTS BEING EVALUATED:
• TorqPrinceFlowers - Tool-enhanced agent for search/research
• MarvinPrinceFlowers - Conversational agent for analysis
• MarvinAgentOrchestrator - Intelligent routing system

📝 TEST CATEGORIES:
• Search queries (GitHub repos, news, research)
• Analysis queries (concepts, comparisons, explanations)
• Code generation (API creation, implementation)
• General queries (capabilities, help)
• Complex multi-tool workflows

The evaluation will establish baseline metrics that can be used to
track improvements and optimize agent performance over time.
""")

if __name__ == "__main__":
    print_evaluation_introduction()

    # Run the evaluation
    result = asyncio.run(run_baseline_evaluation())

    if result:
        print(f"\n🎉 BASELINE ESTABLISHED SUCCESSFULLY!")
        print(f"   Quality Score: {result.overall_quality_score:.1%}")
        print(f"   Success Rate: {result.success_rate:.1%}")
        print(f"   Total Tests: {result.total_queries}")
    else:
        print(f"\n❌ BASELINE EVALUATION FAILED")
        print(f"   Check logs for detailed error information")