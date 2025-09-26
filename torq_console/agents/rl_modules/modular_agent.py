"""
Pearl-inspired Modular Agent Architecture for TORQ Console
Based on Facebook's Pearl RL framework research
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

@dataclass
class AgentCapability:
    """Represents a specific capability of the agent."""
    name: str
    description: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

class ModuleType(Enum):
    """Types of RL modules that can be combined."""
    POLICY_LEARNER = "policy_learner"
    EXPLORATION = "exploration"
    SAFETY = "safety"
    HISTORY_SUMMARIZATION = "history_summarization"
    RISK_SENSITIVITY = "risk_sensitivity"
    ACTION_SPACE_MANAGER = "action_space_manager"

class RLModule(ABC):
    """Base class for all modular RL components."""

    def __init__(self, module_type: ModuleType, config: Dict[str, Any]):
        self.module_type = module_type
        self.config = config
        self.enabled = True
        self.performance_metrics = {}
        self.logger = logging.getLogger(f"TORQ.RL.{module_type.value}")

    @abstractmethod
    async def process(self, state: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return module output."""
        pass

    @abstractmethod
    def update_performance(self, feedback: Dict[str, Any]):
        """Update performance metrics based on feedback."""
        pass

    def get_metrics(self) -> Dict[str, float]:
        """Get current performance metrics."""
        return self.performance_metrics.copy()

class PolicyLearnerModule(RLModule):
    """Policy learning module - core decision making."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(ModuleType.POLICY_LEARNER, config)
        self.algorithm = config.get('algorithm', 'td_learning')
        self.learning_rate = config.get('learning_rate', 0.1)
        self.policy_values = {}

    async def process(self, state: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate action based on learned policy."""
        available_actions = context.get('available_actions', [])

        if not available_actions:
            return {'action': None, 'confidence': 0.0}

        # Simple policy lookup with exploration
        best_action = None
        best_value = float('-inf')

        for action in available_actions:
            state_action = f"{state}|{action}"
            value = self.policy_values.get(state_action, 0.0)

            if value > best_value:
                best_value = value
                best_action = action

        confidence = min(1.0, max(0.0, best_value))

        return {
            'action': best_action or available_actions[0],
            'confidence': confidence,
            'value': best_value
        }

    def update_performance(self, feedback: Dict[str, Any]):
        """Update policy based on reward feedback."""
        state = feedback.get('state')
        action = feedback.get('action')
        reward = feedback.get('reward', 0.0)
        next_state = feedback.get('next_state')

        if state and action:
            state_action = f"{state}|{action}"
            current_value = self.policy_values.get(state_action, 0.0)

            # Simple TD learning update
            td_target = reward
            if next_state:
                # Look for best next state value
                next_values = [v for k, v in self.policy_values.items()
                              if k.startswith(f"{next_state}|")]
                if next_values:
                    td_target += 0.9 * max(next_values)  # gamma = 0.9

            td_error = td_target - current_value
            self.policy_values[state_action] = current_value + self.learning_rate * td_error

            self.performance_metrics['policy_updates'] = self.performance_metrics.get('policy_updates', 0) + 1
            self.performance_metrics['avg_td_error'] = (
                (self.performance_metrics.get('avg_td_error', 0.0) * 0.9) +
                (abs(td_error) * 0.1)
            )

class ExplorationModule(RLModule):
    """Intelligent exploration module."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(ModuleType.EXPLORATION, config)
        self.strategy = config.get('strategy', 'epsilon_greedy')
        self.initial_epsilon = config.get('initial_epsilon', 0.3)  # Start with higher exploration
        self.min_epsilon = config.get('min_epsilon', 0.05)  # Minimum exploration rate
        self.epsilon_decay_rate = config.get('epsilon_decay_rate', 0.995)  # Decay factor
        self.epsilon = self.initial_epsilon
        self.exploration_bonus = config.get('exploration_bonus', 0.1)
        self.state_visit_counts = {}
        self.total_steps = 0

    async def process(self, state: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance action selection with exploration."""
        policy_output = context.get('policy_output', {})
        available_actions = context.get('available_actions', [])

        if not available_actions:
            return policy_output

        # Track state visits
        self.state_visit_counts[state] = self.state_visit_counts.get(state, 0) + 1

        # Exploration strategies
        if self.strategy == 'epsilon_greedy':
            if np.random.random() < self.epsilon:
                # Explore: choose random action
                explore_action = np.random.choice(available_actions)
                return {
                    'action': explore_action,
                    'confidence': 0.5,
                    'exploration': True,
                    'exploration_type': 'random'
                }

        elif self.strategy == 'curiosity_driven':
            # Curiosity-driven exploration - prefer less visited states
            action_curiosity_scores = {}
            for action in available_actions:
                # Simulate next state for curiosity calculation
                next_state_key = f"{state}_{action}"
                visit_count = self.state_visit_counts.get(next_state_key, 0)
                curiosity_score = self.exploration_bonus / max(1, visit_count)
                action_curiosity_scores[action] = curiosity_score

            # Choose action with highest curiosity if it exceeds threshold
            max_curiosity_action = max(action_curiosity_scores, key=action_curiosity_scores.get)
            max_curiosity_score = action_curiosity_scores[max_curiosity_action]

            if max_curiosity_score > 0.05:  # Curiosity threshold
                return {
                    'action': max_curiosity_action,
                    'confidence': min(1.0, max_curiosity_score * 5),
                    'exploration': True,
                    'exploration_type': 'curiosity',
                    'curiosity_score': max_curiosity_score
                }

        # Default: return policy output with exploration metadata
        enhanced_output = policy_output.copy()
        enhanced_output['exploration'] = False
        return enhanced_output

    def update_performance(self, feedback: Dict[str, Any]):
        """Update exploration strategy based on performance."""
        reward = feedback.get('reward', 0.0)
        was_exploration = feedback.get('was_exploration', False)

        if was_exploration:
            self.performance_metrics['exploration_attempts'] = (
                self.performance_metrics.get('exploration_attempts', 0) + 1
            )

            if reward > 0:
                self.performance_metrics['successful_explorations'] = (
                    self.performance_metrics.get('successful_explorations', 0) + 1
                )

        # Production-ready adaptive epsilon with decay schedule
        self.total_steps += 1

        # Apply epsilon decay (following 2024 research recommendations)
        if self.total_steps % 100 == 0:  # Decay every 100 steps
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay_rate)

        # Additional adaptive adjustment based on success rate
        exploration_success_rate = (
            self.performance_metrics.get('successful_explorations', 0) /
            max(1, self.performance_metrics.get('exploration_attempts', 1))
        )

        # Fine-tune epsilon based on performance (secondary adjustment)
        if exploration_success_rate > 0.8:
            # High success rate - can afford slightly more exploration
            self.epsilon = min(self.initial_epsilon * 0.5, self.epsilon * 1.02)
        elif exploration_success_rate < 0.2:
            # Low success rate - reduce exploration more aggressively
            self.epsilon = max(self.min_epsilon, self.epsilon * 0.98)

class SafetyModule(RLModule):
    """Safety constraints and risk management."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(ModuleType.SAFETY, config)
        self.risk_threshold = config.get('risk_threshold', 0.3)
        self.safety_constraints = config.get('constraints', [])
        self.risk_history = []

    async def process(self, state: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply safety constraints to action selection."""
        action_output = context.get('action_output', {})
        proposed_action = action_output.get('action')

        if not proposed_action:
            return action_output

        # Assess risk of proposed action
        risk_score = await self._assess_risk(state, proposed_action, context)

        # Apply safety constraints
        safe_actions = await self._filter_safe_actions(
            context.get('available_actions', []), state, context
        )

        # If proposed action is too risky, suggest safer alternative
        if risk_score > self.risk_threshold:
            if safe_actions:
                safer_action = safe_actions[0]  # Choose first safe action
                self.logger.warning(
                    f"Blocked risky action '{proposed_action}' (risk: {risk_score:.3f}), "
                    f"suggesting safer alternative: '{safer_action}'"
                )
                return {
                    'action': safer_action,
                    'confidence': action_output.get('confidence', 0.5) * 0.8,
                    'safety_intervention': True,
                    'blocked_action': proposed_action,
                    'risk_score': risk_score,
                    'safety_reason': 'risk_threshold_exceeded'
                }

        # Action is safe, add safety metadata
        safe_output = action_output.copy()
        safe_output.update({
            'safety_intervention': False,
            'risk_score': risk_score,
            'safety_approved': True
        })

        return safe_output

    async def _assess_risk(self, state: str, action: str, context: Dict[str, Any]) -> float:
        """Assess risk score for state-action pair."""
        # Simple heuristic-based risk assessment
        risk_factors = []

        # Check for known risky patterns
        risky_keywords = ['delete', 'remove', 'destroy', 'format', 'kill']
        if any(keyword in action.lower() for keyword in risky_keywords):
            risk_factors.append(0.8)

        # Check historical risk
        historical_risk = np.mean([
            r['risk'] for r in self.risk_history
            if r['action'] == action
        ]) if self.risk_history else 0.0

        if historical_risk > 0:
            risk_factors.append(historical_risk)

        # Combine risk factors
        if not risk_factors:
            return 0.1  # Baseline low risk

        return min(1.0, np.mean(risk_factors))

    async def _filter_safe_actions(self, actions: List[str], state: str,
                                  context: Dict[str, Any]) -> List[str]:
        """Filter actions to only include safe ones."""
        safe_actions = []

        for action in actions:
            risk_score = await self._assess_risk(state, action, context)
            if risk_score <= self.risk_threshold:
                safe_actions.append(action)

        return safe_actions

    def update_performance(self, feedback: Dict[str, Any]):
        """Update safety metrics and risk models."""
        action = feedback.get('action')
        reward = feedback.get('reward', 0.0)
        error_occurred = feedback.get('error_occurred', False)

        if action:
            # Record risk outcome
            risk_outcome = {
                'action': action,
                'risk': 1.0 if error_occurred else max(0.0, -reward),
                'timestamp': time.time()
            }

            self.risk_history.append(risk_outcome)

            # Keep only recent history
            if len(self.risk_history) > 100:
                self.risk_history = self.risk_history[-100:]

            # Update safety metrics
            self.performance_metrics['safety_assessments'] = (
                self.performance_metrics.get('safety_assessments', 0) + 1
            )

            if error_occurred:
                self.performance_metrics['safety_violations'] = (
                    self.performance_metrics.get('safety_violations', 0) + 1
                )

class ModularRLAgent:
    """Pearl-inspired modular RL agent with pluggable capabilities."""

    def __init__(self, agent_id: str = "modular_rl"):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"TORQ.ModularRL.{agent_id}")
        self.modules: Dict[ModuleType, RLModule] = {}
        self.capabilities: List[AgentCapability] = []
        self.processing_pipeline = []

    def add_module(self, module: RLModule):
        """Add a module to the agent."""
        self.modules[module.module_type] = module
        self._rebuild_pipeline()
        self.logger.info(f"Added module: {module.module_type.value}")

    def remove_module(self, module_type: ModuleType):
        """Remove a module from the agent."""
        if module_type in self.modules:
            del self.modules[module_type]
            self._rebuild_pipeline()
            self.logger.info(f"Removed module: {module_type.value}")

    def _rebuild_pipeline(self):
        """Rebuild processing pipeline based on available modules."""
        # Define optimal processing order
        pipeline_order = [
            ModuleType.HISTORY_SUMMARIZATION,
            ModuleType.ACTION_SPACE_MANAGER,
            ModuleType.POLICY_LEARNER,
            ModuleType.EXPLORATION,
            ModuleType.RISK_SENSITIVITY,
            ModuleType.SAFETY
        ]

        self.processing_pipeline = [
            module_type for module_type in pipeline_order
            if module_type in self.modules and self.modules[module_type].enabled
        ]

    async def select_action(self, state: str, available_actions: List[str],
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Select action using modular pipeline."""
        if context is None:
            context = {}

        # Initialize context
        context.update({
            'state': state,
            'available_actions': available_actions,
            'timestamp': time.time()
        })

        # Process through pipeline
        for module_type in self.processing_pipeline:
            module = self.modules[module_type]

            try:
                result = await module.process(state, context)

                # Update context with module output
                if module_type == ModuleType.POLICY_LEARNER:
                    context['policy_output'] = result
                elif module_type == ModuleType.EXPLORATION:
                    context['action_output'] = result
                elif module_type == ModuleType.SAFETY:
                    context['final_output'] = result
                else:
                    context[f'{module_type.value}_output'] = result

                self.logger.debug(f"Module {module_type.value} processed: {result}")

            except Exception as e:
                self.logger.error(f"Error in module {module_type.value}: {e}")
                continue

        # Return final action decision
        final_output = context.get('final_output', context.get('action_output', {}))

        # Ensure we have a valid action
        if not final_output.get('action') and available_actions:
            final_output = {
                'action': available_actions[0],
                'confidence': 0.1,
                'fallback': True
            }

        return final_output

    async def update_from_feedback(self, experience: Dict[str, Any]):
        """Update all modules based on experience feedback."""
        for module in self.modules.values():
            try:
                module.update_performance(experience)
            except Exception as e:
                self.logger.error(f"Error updating module {module.module_type.value}: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from all modules."""
        summary = {
            'agent_id': self.agent_id,
            'active_modules': list(self.modules.keys()),
            'pipeline_order': self.processing_pipeline,
            'module_performance': {}
        }

        for module_type, module in self.modules.items():
            summary['module_performance'][module_type.value] = module.get_metrics()

        return summary

    def configure_capabilities(self, capabilities_config: Dict[str, Any]):
        """Configure agent capabilities based on Pearl-style configuration."""
        # Parse configuration and instantiate modules
        if capabilities_config.get('intelligent_exploration', False):
            exploration_config = capabilities_config.get('exploration_config', {})
            self.add_module(ExplorationModule(exploration_config))

        if capabilities_config.get('safety_constraints', False):
            safety_config = capabilities_config.get('safety_config', {})
            self.add_module(SafetyModule(safety_config))

        # Always include policy learner
        policy_config = capabilities_config.get('policy_config', {})
        self.add_module(PolicyLearnerModule(policy_config))

        self.logger.info(f"Configured modular agent with {len(self.modules)} modules")

# Factory function for creating pre-configured agents
def create_production_agent(agent_id: str) -> ModularRLAgent:
    """Create a production-ready modular agent with Pearl-inspired capabilities."""
    agent = ModularRLAgent(agent_id)

    # Production configuration similar to Pearl's defaults
    config = {
        'intelligent_exploration': True,
        'safety_constraints': True,
        'exploration_config': {
            'strategy': 'curiosity_driven',
            'initial_epsilon': 0.3,  # Start with 30% exploration
            'min_epsilon': 0.05,     # Minimum 5% exploration
            'epsilon_decay_rate': 0.995,  # Gradual decay
            'exploration_bonus': 0.1
        },
        'safety_config': {
            'risk_threshold': 0.3,
            'constraints': ['no_destructive_actions']
        },
        'policy_config': {
            'algorithm': 'td_learning',
            'learning_rate': 0.1
        }
    }

    agent.configure_capabilities(config)
    return agent