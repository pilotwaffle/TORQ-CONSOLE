"""
Dynamic Action Spaces Module - Pearl-inspired capability for TORQ Console
Handles adaptive action spaces that change based on context and environment state
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from .modular_agent import RLModule, ModuleType

class ActionConstraint(Enum):
    """Types of constraints that can be applied to action spaces."""
    TEMPORAL = "temporal"  # Time-based constraints
    CONTEXTUAL = "contextual"  # Context-dependent constraints
    SAFETY = "safety"  # Safety-based constraints
    RESOURCE = "resource"  # Resource availability constraints
    CAPABILITY = "capability"  # Agent capability constraints

@dataclass
class ActionMetadata:
    """Metadata associated with each action."""
    action_id: str
    description: str
    prerequisites: List[str] = field(default_factory=list)
    cost: float = 1.0
    risk_level: float = 0.0
    execution_time: float = 1.0
    success_probability: float = 1.0
    constraints: List[ActionConstraint] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)

@dataclass
class ActionSpaceState:
    """Current state of the dynamic action space."""
    available_actions: Set[str]
    blocked_actions: Set[str]
    conditional_actions: Dict[str, List[str]]  # Action -> conditions needed
    action_metadata: Dict[str, ActionMetadata]
    last_updated: float
    context_hash: str

class DynamicActionSpaceModule(RLModule):
    """Manages dynamic action spaces that adapt to environment and context."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(ModuleType.ACTION_SPACE_MANAGER, config)
        self.base_actions = set(config.get('base_actions', []))
        self.conditional_actions = config.get('conditional_actions', {})
        self.action_metadata = {}
        self.context_cache = {}
        self.action_history = []
        self.current_state = None

        # Initialize action metadata
        self._initialize_action_metadata(config)

    def _initialize_action_metadata(self, config: Dict[str, Any]):
        """Initialize metadata for all possible actions."""
        actions_config = config.get('actions_metadata', {})

        # Create metadata for base actions
        for action in self.base_actions:
            metadata_config = actions_config.get(action, {})
            self.action_metadata[action] = ActionMetadata(
                action_id=action,
                description=metadata_config.get('description', f'Action: {action}'),
                prerequisites=metadata_config.get('prerequisites', []),
                cost=metadata_config.get('cost', 1.0),
                risk_level=metadata_config.get('risk_level', 0.1),
                execution_time=metadata_config.get('execution_time', 1.0),
                success_probability=metadata_config.get('success_probability', 0.9),
                constraints=[ActionConstraint(c) for c in metadata_config.get('constraints', [])],
                tags=set(metadata_config.get('tags', []))
            )

    async def process(self, state: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dynamic action space based on current context."""
        context_signature = self._generate_context_signature(state, context)

        # Check if we can use cached result
        if (context_signature in self.context_cache and
            time.time() - self.context_cache[context_signature]['timestamp'] < 30):
            cached_result = self.context_cache[context_signature]
            return cached_result['action_space']

        # Generate new action space
        action_space = await self._compute_dynamic_action_space(state, context)

        # Cache result
        self.context_cache[context_signature] = {
            'action_space': action_space,
            'timestamp': time.time()
        }

        # Update current state
        self.current_state = ActionSpaceState(
            available_actions=set(action_space['available_actions']),
            blocked_actions=set(action_space['blocked_actions']),
            conditional_actions=action_space['conditional_actions'],
            action_metadata=action_space['action_metadata'],
            last_updated=time.time(),
            context_hash=context_signature
        )

        return action_space

    async def _compute_dynamic_action_space(self, state: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Compute the dynamic action space for the current context."""
        available_actions = set()
        blocked_actions = set()
        conditional_actions = {}
        relevant_metadata = {}

        # Start with base actions
        candidate_actions = self.base_actions.copy()

        # Add context-specific actions
        candidate_actions.update(await self._get_contextual_actions(state, context))

        # Evaluate each candidate action
        for action in candidate_actions:
            metadata = self.action_metadata.get(action)
            if not metadata:
                continue

            # Check constraints
            constraint_results = await self._evaluate_constraints(action, metadata, state, context)

            if constraint_results['allowed']:
                available_actions.add(action)
                relevant_metadata[action] = metadata
            else:
                blocked_actions.add(action)
                if constraint_results['conditions']:
                    conditional_actions[action] = constraint_results['conditions']

        # Rank actions by utility
        ranked_actions = await self._rank_actions_by_utility(
            list(available_actions), state, context
        )

        return {
            'available_actions': ranked_actions,
            'blocked_actions': list(blocked_actions),
            'conditional_actions': conditional_actions,
            'action_metadata': {k: self._serialize_metadata(v)
                              for k, v in relevant_metadata.items()},
            'space_size': len(available_actions),
            'generation_time': time.time()
        }

    async def _get_contextual_actions(self, state: str, context: Dict[str, Any]) -> Set[str]:
        """Get actions that are available only in specific contexts with enhanced sensitivity."""
        contextual_actions = set()

        # Enhanced agent capabilities - more granular capability-based actions
        agent_capabilities = context.get('agent_capabilities', [])
        for capability in agent_capabilities:
            capability_actions = self.conditional_actions.get(f'capability_{capability}', [])
            contextual_actions.update(capability_actions)

            # Add capability combinations for more varied action spaces
            for other_cap in agent_capabilities:
                if other_cap != capability:
                    combo_key = f'combo_{min(capability, other_cap)}_{max(capability, other_cap)}'
                    combo_actions = self.conditional_actions.get(combo_key, [])
                    contextual_actions.update(combo_actions)

        # Enhanced environment state with nested context awareness
        environment_state = context.get('environment_state', {})
        for env_key, env_value in environment_state.items():
            env_actions = self.conditional_actions.get(f'env_{env_key}_{env_value}', [])
            contextual_actions.update(env_actions)

            # Add context-sensitive state combinations
            for other_key, other_value in environment_state.items():
                if other_key != env_key:
                    state_combo_key = f'state_combo_{env_key}_{env_value}_{other_key}_{other_value}'
                    state_combo_actions = self.conditional_actions.get(state_combo_key, [])
                    contextual_actions.update(state_combo_actions)

        # Enhanced temporal context with multiple time scales
        current_time = context.get('timestamp', time.time())
        hour_of_day = int((current_time % 86400) / 3600)  # Hour of day (0-23)
        day_of_week = int((current_time // 86400) % 7)  # Day of week (0-6)

        # Hour-based actions
        time_actions = self.conditional_actions.get(f'hour_{hour_of_day}', [])
        contextual_actions.update(time_actions)

        # Day-based actions
        day_actions = self.conditional_actions.get(f'day_{day_of_week}', [])
        contextual_actions.update(day_actions)

        # Time period combinations
        time_period = 'morning' if 6 <= hour_of_day < 12 else 'afternoon' if 12 <= hour_of_day < 18 else 'evening' if 18 <= hour_of_day < 22 else 'night'
        period_actions = self.conditional_actions.get(f'period_{time_period}', [])
        contextual_actions.update(period_actions)

        # Context priority-based actions (weighted by importance)
        context_priority = context.get('priority', 'normal')
        priority_actions = self.conditional_actions.get(f'priority_{context_priority}', [])
        contextual_actions.update(priority_actions)

        # User/task-specific context
        user_context = context.get('user_context', {})
        for ctx_key, ctx_value in user_context.items():
            user_actions = self.conditional_actions.get(f'user_{ctx_key}_{ctx_value}', [])
            contextual_actions.update(user_actions)

        # Dynamic action generation based on state complexity
        state_complexity = len(state.split()) if isinstance(state, str) else 0
        if state_complexity > 5:  # Complex states get additional actions
            complex_actions = self.conditional_actions.get('complex_state', [])
            contextual_actions.update(complex_actions)

        return contextual_actions

    async def _evaluate_constraints(self, action: str, metadata: ActionMetadata,
                                   state: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate whether an action satisfies all constraints."""
        allowed = True
        conditions_needed = []

        # Check prerequisites
        for prereq in metadata.prerequisites:
            if not await self._check_prerequisite(prereq, state, context):
                allowed = False
                conditions_needed.append(f"prerequisite_{prereq}")

        # Check specific constraints
        for constraint in metadata.constraints:
            constraint_result = await self._check_constraint(constraint, action, state, context)
            if not constraint_result['satisfied']:
                allowed = False
                if constraint_result['condition']:
                    conditions_needed.append(constraint_result['condition'])

        # Check resource availability
        if metadata.cost > 0:
            available_resources = context.get('available_resources', float('inf'))
            if available_resources < metadata.cost:
                allowed = False
                conditions_needed.append(f"resources_needed_{metadata.cost}")

        # Check agent state
        agent_state = context.get('agent_state', {})
        if agent_state.get('busy', False) and metadata.execution_time > 0:
            allowed = False
            conditions_needed.append("agent_available")

        return {
            'allowed': allowed,
            'conditions': conditions_needed
        }

    async def _check_prerequisite(self, prerequisite: str, state: str, context: Dict[str, Any]) -> bool:
        """Check if a prerequisite is satisfied."""
        # Simple prerequisite checking - can be extended
        if prerequisite.startswith('state_'):
            required_state = prerequisite[6:]  # Remove 'state_' prefix
            return required_state in state

        if prerequisite.startswith('context_'):
            context_key = prerequisite[8:]  # Remove 'context_' prefix
            return context.get(context_key, False)

        if prerequisite.startswith('action_'):
            required_action = prerequisite[7:]  # Remove 'action_' prefix
            # Check if action was recently performed
            recent_actions = [h['action'] for h in self.action_history[-5:]]
            return required_action in recent_actions

        return True  # Unknown prerequisites are assumed satisfied

    async def _check_constraint(self, constraint: ActionConstraint, action: str,
                               state: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a specific constraint is satisfied."""
        if constraint == ActionConstraint.TEMPORAL:
            # Example: Some actions only available during business hours
            current_time = context.get('timestamp', time.time())
            hour_of_day = int((current_time % 86400) / 3600)
            if 9 <= hour_of_day <= 17:  # Business hours
                return {'satisfied': True}
            else:
                return {'satisfied': False, 'condition': 'business_hours'}

        elif constraint == ActionConstraint.SAFETY:
            # Safety constraint - check risk level
            metadata = self.action_metadata.get(action)
            safety_threshold = context.get('safety_threshold', 0.5)
            if metadata and metadata.risk_level <= safety_threshold:
                return {'satisfied': True}
            else:
                return {'satisfied': False, 'condition': 'safety_clearance'}

        elif constraint == ActionConstraint.RESOURCE:
            # Resource constraint - check if sufficient resources
            metadata = self.action_metadata.get(action)
            available_resources = context.get('available_resources', float('inf'))
            if metadata and available_resources >= metadata.cost:
                return {'satisfied': True}
            else:
                return {'satisfied': False, 'condition': 'sufficient_resources'}

        elif constraint == ActionConstraint.CAPABILITY:
            # Capability constraint - check agent capabilities
            agent_capabilities = set(context.get('agent_capabilities', []))
            metadata = self.action_metadata.get(action)
            if metadata:
                required_capabilities = metadata.tags.intersection({'web', 'database', 'file', 'api'})
                if required_capabilities.issubset(agent_capabilities):
                    return {'satisfied': True}
                else:
                    missing = required_capabilities - agent_capabilities
                    return {'satisfied': False, 'condition': f'capabilities_{",".join(missing)}'}

        return {'satisfied': True}  # Unknown constraints are assumed satisfied

    async def _rank_actions_by_utility(self, actions: List[str], state: str,
                                      context: Dict[str, Any]) -> List[str]:
        """Rank actions by their expected utility."""
        if not actions:
            return []

        action_utilities = []

        for action in actions:
            metadata = self.action_metadata.get(action)
            if not metadata:
                continue

            # Calculate utility based on multiple factors
            utility = await self._calculate_action_utility(action, metadata, state, context)
            action_utilities.append((action, utility))

        # Sort by utility (descending)
        action_utilities.sort(key=lambda x: x[1], reverse=True)

        return [action for action, utility in action_utilities]

    async def _calculate_action_utility(self, action: str, metadata: ActionMetadata,
                                       state: str, context: Dict[str, Any]) -> float:
        """Calculate the utility score for an action."""
        # Base utility from success probability
        utility = metadata.success_probability

        # Penalize by cost
        if metadata.cost > 0:
            utility -= metadata.cost * 0.1

        # Penalize by risk
        utility -= metadata.risk_level * 0.2

        # Bonus for speed (inverse of execution time)
        if metadata.execution_time > 0:
            utility += 1.0 / metadata.execution_time * 0.1

        # Context-specific bonuses
        context_priority = context.get('action_priorities', {})
        if action in context_priority:
            utility += context_priority[action]

        # Historical performance bonus/penalty
        action_performance = self._get_historical_performance(action)
        utility += action_performance * 0.15

        return max(0.0, utility)

    def _get_historical_performance(self, action: str) -> float:
        """Get historical performance score for an action."""
        action_history = [h for h in self.action_history if h.get('action') == action]

        if not action_history:
            return 0.0

        # Calculate average reward for this action
        rewards = [h.get('reward', 0.0) for h in action_history]
        return np.mean(rewards)

    def _generate_context_signature(self, state: str, context: Dict[str, Any]) -> str:
        """Generate a signature for the current context for caching."""
        # Create a simplified hash of the context
        context_keys = ['agent_capabilities', 'environment_state', 'available_resources']
        context_subset = {k: context.get(k) for k in context_keys}
        context_str = f"{state}|{str(sorted(context_subset.items()))}"
        return str(hash(context_str))

    def _serialize_metadata(self, metadata: ActionMetadata) -> Dict[str, Any]:
        """Serialize action metadata for JSON compatibility."""
        return {
            'action_id': metadata.action_id,
            'description': metadata.description,
            'prerequisites': metadata.prerequisites,
            'cost': metadata.cost,
            'risk_level': metadata.risk_level,
            'execution_time': metadata.execution_time,
            'success_probability': metadata.success_probability,
            'constraints': [c.value for c in metadata.constraints],
            'tags': list(metadata.tags)
        }

    def update_performance(self, feedback: Dict[str, Any]):
        """Update action space manager based on feedback."""
        action = feedback.get('action')
        reward = feedback.get('reward', 0.0)
        execution_time = feedback.get('execution_time', 0.0)
        success = feedback.get('success', reward > 0)

        if action:
            # Update action history
            history_entry = {
                'action': action,
                'reward': reward,
                'execution_time': execution_time,
                'success': success,
                'timestamp': time.time(),
                'state': feedback.get('state', ''),
                'context_hash': feedback.get('context_hash', '')
            }

            self.action_history.append(history_entry)

            # Keep only recent history
            if len(self.action_history) > 1000:
                self.action_history = self.action_history[-1000:]

            # Update action metadata based on performance
            if action in self.action_metadata:
                metadata = self.action_metadata[action]

                # Update success probability with exponential moving average
                alpha = 0.1
                metadata.success_probability = (
                    (1 - alpha) * metadata.success_probability +
                    alpha * (1.0 if success else 0.0)
                )

                # Update execution time estimate
                if execution_time > 0:
                    metadata.execution_time = (
                        (1 - alpha) * metadata.execution_time +
                        alpha * execution_time
                    )

            # Update performance metrics
            self.performance_metrics['actions_executed'] = (
                self.performance_metrics.get('actions_executed', 0) + 1
            )

            if success:
                self.performance_metrics['successful_actions'] = (
                    self.performance_metrics.get('successful_actions', 0) + 1
                )

            # Update success rate
            total_actions = self.performance_metrics['actions_executed']
            successful_actions = self.performance_metrics.get('successful_actions', 0)
            self.performance_metrics['success_rate'] = successful_actions / max(1, total_actions)

    def get_action_space_statistics(self) -> Dict[str, Any]:
        """Get statistics about the dynamic action space."""
        if not self.current_state:
            return {'status': 'not_initialized'}

        return {
            'current_space_size': len(self.current_state.available_actions),
            'blocked_actions_count': len(self.current_state.blocked_actions),
            'conditional_actions_count': len(self.current_state.conditional_actions),
            'total_registered_actions': len(self.action_metadata),
            'last_updated': self.current_state.last_updated,
            'cache_hit_rate': len(self.context_cache) / max(1, len(self.action_history[-100:])),
            'most_used_actions': self._get_most_used_actions(),
            'action_success_rates': self._get_action_success_rates()
        }

    def _get_most_used_actions(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get the most frequently used actions."""
        action_counts = {}
        for entry in self.action_history[-100:]:  # Last 100 actions
            action = entry.get('action')
            if action:
                action_counts[action] = action_counts.get(action, 0) + 1

        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'action': action, 'count': count} for action, count in sorted_actions[:top_n]]

    def _get_action_success_rates(self) -> Dict[str, float]:
        """Get success rates for each action."""
        action_stats = {}

        for entry in self.action_history:
            action = entry.get('action')
            success = entry.get('success', False)

            if action not in action_stats:
                action_stats[action] = {'total': 0, 'successful': 0}

            action_stats[action]['total'] += 1
            if success:
                action_stats[action]['successful'] += 1

        return {
            action: stats['successful'] / max(1, stats['total'])
            for action, stats in action_stats.items()
        }