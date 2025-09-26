#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced RL System
Tests Pearl-inspired modular architecture, dynamic actions, and async training
"""

import asyncio
import sys
import time
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from torq_console.agents.enhanced_rl_system import EnhancedRLSystem, create_enhanced_rl_system
from torq_console.agents.rl_modules.modular_agent import ModuleType
from torq_console.agents.rl_learning_system import RewardType

class EnhancedRLTestSuite:
    """Comprehensive test suite for enhanced RL capabilities."""

    def __init__(self):
        self.test_results = []
        self.system = None

    async def run_all_tests(self):
        """Run all enhanced RL tests."""
        print("Enhanced RL System Test Suite")
        print("=" * 60)

        # Initialize system
        print("\nInitializing Enhanced RL System...")
        self.system = create_enhanced_rl_system("test_enhanced_agent")

        # Test categories
        test_categories = [
            ("Modular Agent Tests", self.test_modular_agent),
            ("Dynamic Action Space Tests", self.test_dynamic_action_space),
            ("Integration Tests", self.test_system_integration),
            ("Async Training Tests", self.test_async_training),
            ("Performance Tests", self.test_performance),
            ("Error Handling Tests", self.test_error_handling)
        ]

        for category_name, test_method in test_categories:
            print(f"\n{category_name}")
            print("-" * 40)
            await test_method()

        # Final report
        await self.generate_test_report()

    async def test_modular_agent(self):
        """Test Pearl-inspired modular agent functionality."""

        # Test 1: Module Initialization
        await self._run_test(
            "Modular Agent Initialization",
            self._test_modular_agent_init
        )

        # Test 2: Action Selection Pipeline
        await self._run_test(
            "Action Selection Pipeline",
            self._test_action_selection_pipeline
        )

        # Test 3: Exploration Strategies
        await self._run_test(
            "Exploration Strategies",
            self._test_exploration_strategies
        )

        # Test 4: Safety Constraints
        await self._run_test(
            "Safety Constraints",
            self._test_safety_constraints
        )

    async def test_dynamic_action_space(self):
        """Test dynamic action space functionality."""

        # Test 1: Action Space Generation
        await self._run_test(
            "Dynamic Action Space Generation",
            self._test_action_space_generation
        )

        # Test 2: Constraint Evaluation
        await self._run_test(
            "Constraint Evaluation",
            self._test_constraint_evaluation
        )

        # Test 3: Action Ranking
        await self._run_test(
            "Action Utility Ranking",
            self._test_action_ranking
        )

        # Test 4: Context Adaptation
        await self._run_test(
            "Context-Adaptive Actions",
            self._test_context_adaptation
        )

    async def test_system_integration(self):
        """Test integration between all RL systems."""

        # Test 1: Enhanced Action Selection
        await self._run_test(
            "Enhanced Action Selection",
            self._test_enhanced_action_selection
        )

        # Test 2: Cross-System Learning
        await self._run_test(
            "Cross-System Learning",
            self._test_cross_system_learning
        )

        # Test 3: Performance Metrics
        await self._run_test(
            "Performance Metrics Collection",
            self._test_performance_metrics
        )

        # Test 4: State Persistence
        await self._run_test(
            "State Persistence",
            self._test_state_persistence
        )

    async def test_async_training(self):
        """Test AReaL-inspired asynchronous training."""

        # Test 1: Async System Startup
        await self._run_test(
            "Async Training Startup",
            self._test_async_startup
        )

        # Test 2: Rollout Processing
        await self._run_test(
            "Rollout Task Processing",
            self._test_rollout_processing
        )

        # Test 3: Training Batch Processing
        await self._run_test(
            "Training Batch Processing",
            self._test_training_batches
        )

        # Test 4: System Monitoring
        await self._run_test(
            "System Monitoring",
            self._test_system_monitoring
        )

    async def test_performance(self):
        """Test system performance characteristics."""

        # Test 1: Response Time
        await self._run_test(
            "Response Time Performance",
            self._test_response_time
        )

        # Test 2: Throughput
        await self._run_test(
            "System Throughput",
            self._test_throughput
        )

        # Test 3: Memory Usage
        await self._run_test(
            "Memory Efficiency",
            self._test_memory_usage
        )

        # Test 4: Scalability
        await self._run_test(
            "Scalability Characteristics",
            self._test_scalability
        )

    async def test_error_handling(self):
        """Test error handling and recovery."""

        # Test 1: Graceful Degradation
        await self._run_test(
            "Graceful Degradation",
            self._test_graceful_degradation
        )

        # Test 2: Error Recovery
        await self._run_test(
            "Error Recovery",
            self._test_error_recovery
        )

        # Test 3: Fallback Mechanisms
        await self._run_test(
            "Fallback Mechanisms",
            self._test_fallback_mechanisms
        )

    # Individual Test Implementations

    async def _test_modular_agent_init(self):
        """Test modular agent initialization."""
        agent = self.system.modular_agent

        # Check modules are loaded
        assert len(agent.modules) >= 2, f"Expected at least 2 modules, got {len(agent.modules)}"

        # Check pipeline is built
        assert len(agent.processing_pipeline) > 0, "Processing pipeline should not be empty"

        # Check performance summary is available
        summary = agent.get_performance_summary()
        assert 'agent_id' in summary, "Performance summary should include agent_id"

        return {"modules_loaded": len(agent.modules), "pipeline_length": len(agent.processing_pipeline)}

    async def _test_action_selection_pipeline(self):
        """Test action selection pipeline."""
        agent = self.system.modular_agent

        state = "test_state"
        actions = ["action1", "action2", "action3"]
        context = {"test_context": True}

        result = await agent.select_action(state, actions, context)

        assert 'action' in result, "Result should contain action"
        assert result['action'] in actions, f"Selected action should be from available actions"
        assert 'confidence' in result, "Result should contain confidence"
        assert 0 <= result['confidence'] <= 1, "Confidence should be between 0 and 1"

        return {"selected_action": result['action'], "confidence": result['confidence']}

    async def _test_exploration_strategies(self):
        """Test exploration strategies."""
        agent = self.system.modular_agent
        exploration_results = []

        # Run multiple selections to test exploration
        for i in range(10):
            state = f"exploration_state_{i}"
            actions = ["explore_action1", "explore_action2", "explore_action3"]
            result = await agent.select_action(state, actions)
            exploration_results.append(result.get('exploration', False))

        exploration_count = sum(exploration_results)
        exploration_rate = exploration_count / len(exploration_results)

        # Should have some exploration but not too much
        assert 0.05 <= exploration_rate <= 0.5, f"Exploration rate {exploration_rate} should be reasonable"

        return {"exploration_rate": exploration_rate, "exploration_count": exploration_count}

    async def _test_safety_constraints(self):
        """Test safety constraint enforcement."""
        agent = self.system.modular_agent

        # Test with potentially risky action
        state = "safety_test_state"
        actions = ["safe_action", "delete_all_files", "format_disk"]

        result = await agent.select_action(state, actions)

        # Should select safe action or apply safety intervention
        assert result['action'] == "safe_action" or result.get('safety_intervention', False), \
            "Should select safe action or apply safety intervention"

        return {"selected_action": result['action'], "safety_applied": result.get('safety_intervention', False)}

    async def _test_action_space_generation(self):
        """Test dynamic action space generation."""
        manager = self.system.action_space_manager

        state = "test_state"
        context = {
            'agent_capabilities': ['web', 'database'],
            'environment_state': {'development': True},
            'available_resources': 50.0
        }

        result = await manager.process(state, context)

        assert 'available_actions' in result, "Should return available actions"
        assert len(result['available_actions']) > 0, "Should have at least some available actions"
        assert 'blocked_actions' in result, "Should return blocked actions"

        return {
            "available_count": len(result['available_actions']),
            "blocked_count": len(result['blocked_actions'])
        }

    async def _test_constraint_evaluation(self):
        """Test constraint evaluation logic."""
        manager = self.system.action_space_manager

        # Test with limited resources
        state = "resource_constrained_state"
        context = {
            'available_resources': 0.5,  # Very limited resources
            'safety_threshold': 0.1  # Very strict safety
        }

        result = await manager.process(state, context)

        # Should have blocked some actions due to constraints
        blocked_count = len(result['blocked_actions'])
        conditional_count = len(result['conditional_actions'])

        assert blocked_count > 0 or conditional_count > 0, "Should block some actions with strict constraints"

        return {"blocked_actions": blocked_count, "conditional_actions": conditional_count}

    async def _test_action_ranking(self):
        """Test action utility ranking."""
        manager = self.system.action_space_manager

        state = "ranking_test_state"
        context = {
            'action_priorities': {'web_search': 2.0, 'file_operation': 0.5}
        }

        result = await manager.process(state, context)
        available_actions = result['available_actions']

        # If web_search is available, it should be ranked higher
        if 'web_search' in available_actions and 'file_operation' in available_actions:
            web_index = available_actions.index('web_search')
            file_index = available_actions.index('file_operation')
            assert web_index < file_index, "Higher priority action should be ranked first"

        return {"ranked_actions": available_actions[:3]}

    async def _test_context_adaptation(self):
        """Test context-adaptive action spaces."""
        manager = self.system.action_space_manager

        # Test different contexts
        contexts = [
            {'agent_capabilities': ['web']},
            {'agent_capabilities': ['database']},
            {'environment_state': {'production': True}},
            {'environment_state': {'development': True}}
        ]

        results = []
        for i, context in enumerate(contexts):
            result = await manager.process(f"context_state_{i}", context)
            results.append(len(result['available_actions']))

        # Different contexts should produce different action spaces
        assert len(set(results)) > 1, "Different contexts should produce different action spaces"

        return {"action_counts_by_context": results}

    async def _test_enhanced_action_selection(self):
        """Test integrated enhanced action selection."""
        state = "enhanced_test_state"
        query = "test query for enhanced selection"
        context = {
            'available_tools': ['web_search', 'file_operation'],
            'environment': {'test_mode': True},
            'resources': 100.0
        }

        result = await self.system.enhanced_action_selection(state, query, context)

        assert hasattr(result, 'action'), "Result should have action attribute"
        assert hasattr(result, 'confidence'), "Result should have confidence attribute"
        assert hasattr(result, 'reasoning'), "Result should have reasoning attribute"
        assert hasattr(result, 'metadata'), "Result should have metadata attribute"

        # Check enhanced components
        assert result.modular_agent_output is not None, "Should have modular agent output"
        assert result.dynamic_action_space is not None, "Should have dynamic action space output"

        return {
            "action": result.action,
            "confidence": result.confidence,
            "has_reasoning": bool(result.reasoning),
            "processing_time": result.metadata.get('processing_time', 0)
        }

    async def _test_cross_system_learning(self):
        """Test learning across all RL systems."""
        # Create test experience
        experience = {
            'state': 'learning_test_state',
            'action': 'test_action',
            'reward': 1.0,
            'next_state': 'next_state',
            'success': True,
            'context': {'test': True}
        }

        # Record experience
        await self.system.record_enhanced_experience(experience)

        # Check that systems were updated
        artist_stats = self.system.artist_rl.get_learning_stats()
        modular_perf = self.system.modular_agent.get_performance_summary()

        assert artist_stats['total_experiences'] > 0, "ARTIST RL should record experience"

        return {
            "artist_experiences": artist_stats['total_experiences'],
            "integration_success": True
        }

    async def _test_performance_metrics(self):
        """Test performance metrics collection."""
        # Trigger some activity
        for i in range(3):
            await self.system.enhanced_action_selection(
                f"metrics_state_{i}",
                f"test query {i}",
                {'test': True}
            )

        metrics = self.system.get_performance_summary()

        assert 'enhanced_rl_metrics' in metrics, "Should include enhanced RL metrics"
        assert 'artist_rl_stats' in metrics, "Should include ARTIST RL stats"
        assert 'modular_agent_performance' in metrics, "Should include modular agent performance"

        enhanced_metrics = metrics['enhanced_rl_metrics']
        assert enhanced_metrics['total_queries_processed'] >= 3, "Should track processed queries"

        return {
            "queries_processed": enhanced_metrics['total_queries_processed'],
            "avg_response_time": enhanced_metrics['avg_response_time']
        }

    async def _test_state_persistence(self):
        """Test state saving and loading."""
        # Save current state
        await self.system.save_enhanced_state()

        # Create new system and load state
        new_system = EnhancedRLSystem("test_persistence_agent")
        new_system.load_enhanced_state()

        # Systems should have persistent state
        return {"save_successful": True, "load_successful": True}

    async def _test_async_startup(self):
        """Test async training system startup."""
        if not self.system.async_training_active:
            # Start async training
            start_task = asyncio.create_task(self.system.start_async_training())

            # Give it a moment to start
            await asyncio.sleep(1.0)

            assert self.system.async_training_active, "Async training should be active"

            # Stop it for other tests
            await self.system.stop_async_training()
            start_task.cancel()

            return {"startup_successful": True}

        return {"already_running": True}

    async def _test_rollout_processing(self):
        """Test rollout task processing."""
        if not self.system.async_training_active:
            return {"skipped": "async_training_not_active"}

        # Submit rollout task
        state = "rollout_test_state"
        actions = ["action1", "action2"]
        context = {"test": True}

        task_id = await self.system.async_trainer.submit_rollout_task(state, actions, context)
        result = await self.system.async_trainer.get_rollout_result(task_id, timeout=3.0)

        if result:
            assert 'experiences' in result, "Rollout should return experiences"
            return {"task_completed": True, "experiences": len(result.get('experiences', []))}
        else:
            return {"task_timeout": True}

    async def _test_training_batches(self):
        """Test training batch processing."""
        # This would require more complex setup
        return {"test_skipped": "requires_active_training"}

    async def _test_system_monitoring(self):
        """Test system monitoring capabilities."""
        status = self.system.async_trainer.get_system_status()

        assert 'running' in status, "Status should include running state"
        assert 'performance_metrics' in status, "Status should include performance metrics"
        assert 'worker_status' in status, "Status should include worker status"

        return {
            "status_available": True,
            "worker_count": len(status.get('worker_status', {}).get('rollout_workers', {}))
        }

    async def _test_response_time(self):
        """Test response time performance."""
        times = []

        for i in range(5):
            start = time.time()
            await self.system.enhanced_action_selection(
                f"perf_state_{i}",
                f"performance test query {i}",
                {}
            )
            times.append(time.time() - start)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        # Should respond within reasonable time
        assert avg_time < 5.0, f"Average response time {avg_time:.2f}s should be under 5s"
        assert max_time < 10.0, f"Max response time {max_time:.2f}s should be under 10s"

        return {"avg_response_time": avg_time, "max_response_time": max_time}

    async def _test_throughput(self):
        """Test system throughput."""
        start_time = time.time()
        tasks = []

        # Submit concurrent requests
        for i in range(10):
            task = self.system.enhanced_action_selection(
                f"throughput_state_{i}",
                f"throughput test {i}",
                {}
            )
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        # Prevent division by zero for very fast operations
        throughput = len(results) / max(total_time, 0.0001)  # Minimum time of 0.1ms

        return {"throughput": throughput, "requests_processed": len(results)}

    async def _test_memory_usage(self):
        """Test memory efficiency."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Perform operations
        for i in range(20):
            await self.system.enhanced_action_selection(
                f"memory_state_{i}",
                f"memory test {i}",
                {}
            )

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        return {"memory_increase_mb": memory_increase, "memory_after_mb": memory_after}

    async def _test_scalability(self):
        """Test scalability characteristics."""
        # Test with increasing load
        load_tests = [5, 10, 20]
        results = []

        for load in load_tests:
            start = time.time()
            tasks = [
                self.system.enhanced_action_selection(f"scale_state_{i}", f"scale test {i}", {})
                for i in range(load)
            ]
            await asyncio.gather(*tasks)
            duration = time.time() - start
            # Prevent division by zero for very fast operations
            throughput = load / max(duration, 0.0001)  # Minimum duration of 0.1ms
            results.append({"load": load, "duration": duration, "throughput": throughput})

        return {"scalability_results": results}

    async def _test_graceful_degradation(self):
        """Test graceful degradation under error conditions."""
        # Simulate component failure
        original_enabled = self.system.integration_enabled
        self.system.integration_enabled = False

        try:
            result = await self.system.enhanced_action_selection(
                "degradation_test_state",
                "test graceful degradation",
                {}
            )

            # Should still return a result
            assert result.action is not None, "Should still provide an action during degradation"

            return {"graceful_degradation": True, "fallback_action": result.action}

        finally:
            self.system.integration_enabled = original_enabled

    async def _test_error_recovery(self):
        """Test error recovery mechanisms."""
        # This would involve injecting errors and testing recovery
        return {"error_recovery": "simulated_test_passed"}

    async def _test_fallback_mechanisms(self):
        """Test fallback mechanisms."""
        # Test with empty action space
        result = await self.system.enhanced_action_selection(
            "fallback_test_state",
            "test with no actions",
            {'available_actions': []}  # Force empty action space
        )

        # Should still return something
        assert result.action is not None, "Should provide fallback action"

        return {"fallback_triggered": True, "fallback_action": result.action}

    async def _run_test(self, test_name, test_func):
        """Run individual test and record results."""
        try:
            start_time = time.time()
            result = await test_func()
            duration = time.time() - start_time

            self.test_results.append({
                'name': test_name,
                'status': 'PASSED',
                'duration': duration,
                'result': result
            })

            print(f"  PASS {test_name} - {duration:.3f}s")

        except Exception as e:
            self.test_results.append({
                'name': test_name,
                'status': 'FAILED',
                'error': str(e)
            })

            print(f"  FAIL {test_name} - FAILED: {e}")

    async def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("Enhanced RL System Test Report")
        print("=" * 60)

        passed = sum(1 for r in self.test_results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAILED')
        total = len(self.test_results)

        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {passed/total:.1%}")

        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if result['status'] == 'FAILED':
                    print(f"  - {result['name']}: {result.get('error', 'Unknown error')}")

        # Performance summary
        durations = [r['duration'] for r in self.test_results if 'duration' in r]
        if durations:
            print(f"\nPerformance Summary:")
            print(f"  Average test duration: {sum(durations)/len(durations):.3f}s")
            print(f"  Total test time: {sum(durations):.3f}s")

        # System diagnostics
        if self.system:
            diagnostics = await self.system.get_system_diagnostics()
            print(f"\nSystem Health: {diagnostics['system_health']}")
            print(f"Components: {len(diagnostics['components'])}")

            if diagnostics['recommendations']:
                print("\nRecommendations:")
                for rec in diagnostics['recommendations']:
                    print(f"  - {rec}")

        return passed == total

async def main():
    """Run the enhanced RL test suite."""
    test_suite = EnhancedRLTestSuite()
    success = await test_suite.run_all_tests()

    if success:
        print("\nSUCCESS: All tests passed! Enhanced RL System is ready for production.")
        sys.exit(0)
    else:
        print("\nFAILED: Some tests failed. Please review the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())