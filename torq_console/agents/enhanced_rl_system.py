"""
Enhanced RL System for Prince Flowers Agent
Integrates Pearl-inspired modular architecture with AReaL async training
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from pathlib import Path

from .rl_learning_system import ARTISTRLSystem, Experience, RewardType
from .rl_modules.modular_agent import (
    ModularRLAgent, PolicyLearnerModule, ExplorationModule, SafetyModule,
    ModuleType, create_production_agent
)
from .rl_modules.dynamic_actions import DynamicActionSpaceModule
from .rl_modules.async_training import AsyncTrainingSystem

@dataclass
class EnhancedAgentResult:
    """Enhanced result with detailed RL metadata."""
    action: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any]

    # Enhanced RL fields
    modular_agent_output: Dict[str, Any]
    dynamic_action_space: Dict[str, Any]
    rl_predictions: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class EnhancedRLSystem:
    """
    Enhanced RL System combining:
    - Original ARTIST RL Learning System
    - Pearl-inspired Modular Agent Architecture
    - Dynamic Action Spaces
    - AReaL-inspired Asynchronous Training
    """

    def __init__(self, agent_id: str = "enhanced_prince_flowers"):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"TORQ.EnhancedRL.{agent_id}")

        # Initialize core ARTIST RL system
        self.artist_rl = ARTISTRLSystem(agent_id)

        # Initialize modular agent with production configuration
        self.modular_agent = create_production_agent(agent_id)

        # Initialize dynamic action space manager
        self.action_space_manager = self._create_action_space_manager()

        # Initialize async training system
        self.async_trainer = self._create_async_trainer()

        # Integration state
        self.integration_enabled = True
        self.async_training_active = False

        # Performance tracking
        self.enhanced_metrics = {
            'total_queries_processed': 0,
            'modular_agent_usage': 0,
            'dynamic_actions_used': 0,
            'async_predictions_made': 0,
            'integration_success_rate': 0.0,
            'avg_response_time': 0.0
        }

        self.logger.info(f"Enhanced RL System initialized for agent: {agent_id}")

    def _create_action_space_manager(self) -> DynamicActionSpaceModule:
        """Create dynamic action space manager with TORQ-specific configuration."""
        config = {
            'base_actions': [
                'web_search', 'file_operation', 'code_analysis', 'data_processing',
                'api_call', 'database_query', 'text_generation', 'problem_solving'
            ],
            'conditional_actions': {
                'capability_web': ['advanced_web_scraping', 'social_media_analysis'],
                'capability_database': ['complex_queries', 'data_migration'],
                'capability_api': ['batch_processing', 'rate_limit_handling'],
                'env_development_true': ['debug_mode', 'testing_tools'],
                'env_production_true': ['monitoring', 'logging'],
                'hour_9': ['business_hours_apis'],
                'hour_17': ['end_of_day_reporting']
            },
            'actions_metadata': {
                'web_search': {
                    'description': 'Search the web for information',
                    'cost': 1.0,
                    'risk_level': 0.1,
                    'execution_time': 2.0,
                    'success_probability': 0.9,
                    'tags': ['web', 'information']
                },
                'file_operation': {
                    'description': 'Perform file system operations',
                    'cost': 0.5,
                    'risk_level': 0.3,
                    'execution_time': 1.0,
                    'success_probability': 0.95,
                    'prerequisites': ['state_file_access'],
                    'tags': ['file', 'system']
                },
                'api_call': {
                    'description': 'Make external API calls',
                    'cost': 2.0,
                    'risk_level': 0.2,
                    'execution_time': 3.0,
                    'success_probability': 0.85,
                    'constraints': ['safety'],
                    'tags': ['api', 'external']
                },
                'database_query': {
                    'description': 'Execute database queries',
                    'cost': 1.5,
                    'risk_level': 0.4,
                    'execution_time': 2.5,
                    'success_probability': 0.9,
                    'constraints': ['safety', 'resource'],
                    'tags': ['database', 'query']
                }
            }
        }

        return DynamicActionSpaceModule(config)

    def _create_async_trainer(self) -> AsyncTrainingSystem:
        """Create asynchronous training system with TORQ-optimized configuration."""
        config = {
            'max_rollout_workers': 3,  # Conservative for production
            'max_training_workers': 1,  # Single training worker to avoid conflicts
            'batch_size': 16,  # Smaller batches for responsiveness
            'max_queue_size': 500
        }

        return AsyncTrainingSystem(config)

    async def enhanced_action_selection(self, state: str, query: str,
                                      context: Dict[str, Any]) -> EnhancedAgentResult:
        """
        Enhanced action selection using all RL systems.

        Flow:
        1. Use dynamic action space to get available actions
        2. Get modular agent recommendation
        3. Check ARTIST RL for error predictions
        4. Combine insights for final decision
        """
        start_time = time.time()

        try:
            # Step 1: Generate dynamic action space
            action_space_context = {
                'agent_capabilities': context.get('available_tools', []),
                'environment_state': context.get('environment', {}),
                'available_resources': context.get('resources', 100.0),
                'safety_threshold': context.get('safety_threshold', 0.3),
                'timestamp': time.time()
            }

            action_space_result = await self.action_space_manager.process(state, action_space_context)
            available_actions = action_space_result.get('available_actions', [])

            self.enhanced_metrics['dynamic_actions_used'] += 1

            # Step 2: Get modular agent recommendation
            modular_context = action_space_context.copy()
            modular_context['available_actions'] = available_actions

            modular_result = await self.modular_agent.select_action(
                state, available_actions, modular_context
            )

            self.enhanced_metrics['modular_agent_usage'] += 1

            # Step 3: Check ARTIST RL for error predictions and corrections
            proposed_action = modular_result.get('action')
            rl_prediction = await self.artist_rl.predict_correction(state, proposed_action or "")

            if rl_prediction:
                self.enhanced_metrics['async_predictions_made'] += 1
                self.logger.info(f"RL system predicted correction: {rl_prediction}")

            # Step 4: Combine insights for final decision
            final_action = rl_prediction if rl_prediction else proposed_action
            final_confidence = self._calculate_combined_confidence(modular_result, rl_prediction)

            # Step 5: Generate reasoning
            reasoning = self._generate_enhanced_reasoning(
                modular_result, action_space_result, rl_prediction, query
            )

            # Step 6: Compile enhanced metadata
            enhanced_metadata = {
                'original_query': query,
                'processing_time': time.time() - start_time,
                'action_space_size': len(available_actions),
                'modular_agent_confidence': modular_result.get('confidence', 0.0),
                'rl_correction_applied': bool(rl_prediction),
                'safety_score': modular_result.get('risk_score', 0.0),
                'exploration_used': modular_result.get('exploration', False),
                'dynamic_constraints': len(action_space_result.get('blocked_actions', [])),
                'artist_rl_stats': self.artist_rl.get_learning_stats()
            }

            # Update performance metrics
            self.enhanced_metrics['total_queries_processed'] += 1
            self._update_avg_response_time(time.time() - start_time)

            return EnhancedAgentResult(
                action=final_action or "fallback_action",
                confidence=final_confidence,
                reasoning=reasoning,
                metadata=enhanced_metadata,
                modular_agent_output=modular_result,
                dynamic_action_space=action_space_result,
                rl_predictions={'correction': rl_prediction},
                performance_metrics=self.get_performance_summary()
            )

        except Exception as e:
            self.logger.error(f"Error in enhanced action selection: {e}")

            # Fallback to basic functionality
            fallback_result = EnhancedAgentResult(
                action="error_handling",
                confidence=0.1,
                reasoning=f"Enhanced RL system encountered an error: {str(e)}. Using fallback mode.",
                metadata={'error': str(e), 'fallback_mode': True},
                modular_agent_output={},
                dynamic_action_space={},
                rl_predictions={},
                performance_metrics={}
            )

            return fallback_result

    async def record_enhanced_experience(self, experience_data: Dict[str, Any]):
        """Record experience across all RL systems."""
        try:
            # Record in ARTIST RL system
            self.artist_rl.record_experience(
                state=experience_data.get('state', ''),
                action=experience_data.get('action', ''),
                reward=experience_data.get('reward', 0.0),
                next_state=experience_data.get('next_state', ''),
                error_info=experience_data.get('error_info')
            )

            # Update modular agent
            await self.modular_agent.update_from_feedback(experience_data)

            # Update dynamic action space manager
            self.action_space_manager.update_performance(experience_data)

            # Submit to async training if active
            if self.async_training_active:
                await self._submit_async_training_data(experience_data)

            # Update success rate
            success = experience_data.get('reward', 0.0) > 0
            current_rate = self.enhanced_metrics['integration_success_rate']
            total_queries = self.enhanced_metrics['total_queries_processed']

            if total_queries > 0:
                self.enhanced_metrics['integration_success_rate'] = (
                    (current_rate * (total_queries - 1) + (1.0 if success else 0.0)) / total_queries
                )

        except Exception as e:
            self.logger.error(f"Error recording enhanced experience: {e}")

    async def start_async_training(self):
        """Start asynchronous training system."""
        if not self.async_training_active:
            self.async_training_active = True
            asyncio.create_task(self.async_trainer.start_async_training())
            self.logger.info("Async training system started")

    async def stop_async_training(self):
        """Stop asynchronous training system."""
        if self.async_training_active:
            await self.async_trainer.stop_async_training()
            self.async_training_active = False
            self.logger.info("Async training system stopped")

    def _calculate_combined_confidence(self, modular_result: Dict[str, Any],
                                     rl_prediction: Optional[str]) -> float:
        """Calculate combined confidence from multiple RL systems."""
        base_confidence = modular_result.get('confidence', 0.5)

        # Boost confidence if RL system provided a correction
        if rl_prediction:
            rl_boost = 0.2
        else:
            rl_boost = 0.0

        # Factor in safety
        safety_factor = 1.0 - modular_result.get('risk_score', 0.0)

        combined_confidence = min(1.0, (base_confidence + rl_boost) * safety_factor)
        return combined_confidence

    def _generate_enhanced_reasoning(self, modular_result: Dict[str, Any],
                                   action_space_result: Dict[str, Any],
                                   rl_prediction: Optional[str],
                                   query: str) -> str:
        """Generate comprehensive reasoning explanation."""
        reasoning_parts = []

        reasoning_parts.append(f"Processing query: '{query}'")

        # Action space reasoning
        action_count = len(action_space_result.get('available_actions', []))
        blocked_count = len(action_space_result.get('blocked_actions', []))
        reasoning_parts.append(
            f"Dynamic action space: {action_count} available actions, {blocked_count} blocked"
        )

        # Modular agent reasoning
        if modular_result.get('exploration'):
            exploration_type = modular_result.get('exploration_type', 'unknown')
            reasoning_parts.append(f"Using exploration strategy: {exploration_type}")
        else:
            reasoning_parts.append("Using learned policy for action selection")

        # Safety reasoning
        if modular_result.get('safety_intervention'):
            reasoning_parts.append(
                f"Safety intervention: blocked '{modular_result.get('blocked_action')}' "
                f"due to {modular_result.get('safety_reason', 'safety concerns')}"
            )

        # RL prediction reasoning
        if rl_prediction:
            reasoning_parts.append(
                f"ARTIST RL system predicted error and suggested correction: '{rl_prediction}'"
            )

        return " | ".join(reasoning_parts)

    async def _submit_async_training_data(self, experience_data: Dict[str, Any]):
        """Submit experience data to async training system."""
        try:
            state = experience_data.get('state', '')
            available_actions = experience_data.get('available_actions', [])
            context = experience_data.get('context', {})

            task_id = await self.async_trainer.submit_rollout_task(
                state, available_actions, context
            )

            # Optionally wait for result (non-blocking in production)
            # result = await self.async_trainer.get_rollout_result(task_id, timeout=1.0)

        except Exception as e:
            self.logger.error(f"Error submitting async training data: {e}")

    def _update_avg_response_time(self, processing_time: float):
        """Update average response time with exponential moving average."""
        alpha = 0.1
        current_avg = self.enhanced_metrics['avg_response_time']
        self.enhanced_metrics['avg_response_time'] = (
            (1 - alpha) * current_avg + alpha * processing_time
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary from all RL systems."""
        summary = {
            'enhanced_rl_metrics': self.enhanced_metrics.copy(),
            'artist_rl_stats': self.artist_rl.get_learning_stats(),
            'modular_agent_performance': self.modular_agent.get_performance_summary(),
            'action_space_stats': self.action_space_manager.get_action_space_statistics(),
            'system_status': {
                'integration_enabled': self.integration_enabled,
                'async_training_active': self.async_training_active
            }
        }

        if self.async_training_active:
            summary['async_training_status'] = self.async_trainer.get_system_status()

        return summary

    async def get_system_diagnostics(self) -> Dict[str, Any]:
        """Get detailed system diagnostics."""
        diagnostics = {
            'timestamp': time.time(),
            'system_health': 'healthy',
            'components': {
                'artist_rl': {
                    'status': 'active',
                    'error_patterns': len(self.artist_rl.error_patterns),
                    'experiences': len(self.artist_rl.experience_buffer)
                },
                'modular_agent': {
                    'status': 'active',
                    'modules': len(self.modular_agent.modules),
                    'pipeline_length': len(self.modular_agent.processing_pipeline)
                },
                'action_space_manager': {
                    'status': 'active',
                    'registered_actions': len(self.action_space_manager.action_metadata),
                    'cache_size': len(self.action_space_manager.context_cache)
                },
                'async_trainer': {
                    'status': 'active' if self.async_training_active else 'inactive',
                    'workers': self.async_trainer.max_rollout_workers + self.async_trainer.max_training_workers
                }
            },
            'integration_metrics': self.enhanced_metrics.copy(),
            'recommendations': self._generate_optimization_recommendations()
        }

        return diagnostics

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        # Check success rate
        success_rate = self.enhanced_metrics['integration_success_rate']
        if success_rate < 0.7:
            recommendations.append(
                f"Low success rate ({success_rate:.1%}): Consider adjusting exploration parameters"
            )

        # Check response time
        avg_time = self.enhanced_metrics['avg_response_time']
        if avg_time > 2.0:
            recommendations.append(
                f"High response time ({avg_time:.2f}s): Enable async training for performance boost"
            )

        # Check RL usage
        total_queries = self.enhanced_metrics['total_queries_processed']
        predictions = self.enhanced_metrics['async_predictions_made']
        if total_queries > 0 and predictions / total_queries < 0.1:
            recommendations.append(
                "Low RL prediction usage: More diverse training data might improve error prediction"
            )

        if not recommendations:
            recommendations.append("System is performing optimally")

        return recommendations

    async def save_enhanced_state(self):
        """Save the state of all RL systems."""
        try:
            state_dir = Path(f"~/.torq_console/{self.agent_id}").expanduser()
            state_dir.mkdir(parents=True, exist_ok=True)

            # Save enhanced system state
            enhanced_state = {
                'enhanced_metrics': self.enhanced_metrics,
                'integration_enabled': self.integration_enabled,
                'async_training_active': self.async_training_active,
                'timestamp': time.time()
            }

            state_file = state_dir / "enhanced_rl_state.json"
            with open(state_file, 'w') as f:
                json.dump(enhanced_state, f, indent=2)

            # Save component states (ARTIST RL saves automatically)
            # Modular agent state could be saved here if needed
            # Action space manager state could be saved here if needed

            self.logger.info("Enhanced RL state saved successfully")

        except Exception as e:
            self.logger.error(f"Error saving enhanced state: {e}")

    def load_enhanced_state(self):
        """Load the state of all RL systems."""
        try:
            state_file = Path(f"~/.torq_console/{self.agent_id}/enhanced_rl_state.json").expanduser()

            if state_file.exists():
                with open(state_file, 'r') as f:
                    enhanced_state = json.load(f)

                self.enhanced_metrics.update(enhanced_state.get('enhanced_metrics', {}))
                self.integration_enabled = enhanced_state.get('integration_enabled', True)
                # Note: Don't restore async_training_active - let it be explicitly started

                self.logger.info("Enhanced RL state loaded successfully")

        except Exception as e:
            self.logger.error(f"Error loading enhanced state: {e}")

# Global instance factory
def create_enhanced_rl_system(agent_id: str) -> EnhancedRLSystem:
    """Create a production-ready enhanced RL system."""
    system = EnhancedRLSystem(agent_id)
    system.load_enhanced_state()  # Load any previous state
    return system