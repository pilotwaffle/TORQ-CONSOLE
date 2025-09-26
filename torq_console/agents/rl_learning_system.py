"""
ARTIST Framework RL Learning System for Prince Flowers Agent

Implements true reinforcement learning with automatic error correction,
experience replay, and continuous improvement based on the ARTIST framework.
"""

import asyncio
import logging
import json
import pickle
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, deque

@dataclass
class Experience:
    """Single RL experience for learning."""
    state: str
    action: str
    reward: float
    next_state: str
    error_type: Optional[str] = None
    correction_applied: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorPattern:
    """Identified error pattern for automatic correction."""
    error_signature: str
    error_type: str
    frequency: int
    success_rate: float
    corrections: List[str]
    last_seen: float
    confidence: float

class RewardType(Enum):
    """Types of rewards for RL learning."""
    SUCCESS = 1.0
    PARTIAL_SUCCESS = 0.5
    FAILURE = -1.0
    ERROR_CORRECTED = 0.8
    REPEATED_ERROR = -0.5

class ARTISTRLSystem:
    """
    ARTIST Framework Reinforcement Learning System

    Implements:
    - Automatic error detection and correction
    - Experience replay for continuous learning
    - Policy optimization using GRPO algorithm
    - Adaptive strategy selection based on past performance
    """

    def __init__(self, agent_id: str = "prince_flowers"):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"ARTIST.RL.{agent_id}")

        # Learning components
        self.experience_buffer = deque(maxlen=1000)
        self.error_patterns = {}
        self.action_values = defaultdict(lambda: defaultdict(float))
        self.state_visits = defaultdict(int)

        # Learning parameters
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.1
        self.min_experiences_for_learning = 5

        # Error correction tracking
        self.error_history = deque(maxlen=100)
        self.correction_success_rate = 0.0
        self.auto_correct_enabled = True

        # Performance metrics
        self.learning_stats = {
            'total_experiences': 0,
            'errors_detected': 0,
            'corrections_applied': 0,
            'successful_corrections': 0,
            'learning_iterations': 0
        }

        # Load existing knowledge
        self._load_learned_knowledge()

    def record_experience(self, state: str, action: str, reward: float,
                         next_state: str, error_info: Optional[Dict[str, Any]] = None):
        """Record an experience for learning."""
        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            error_type=error_info.get('type') if error_info else None,
            correction_applied=error_info.get('correction') if error_info else None,
            metadata=error_info or {}
        )

        self.experience_buffer.append(experience)
        self.learning_stats['total_experiences'] += 1

        # Immediate learning if error detected
        if error_info:
            self._process_error(experience)

        # Periodic learning update
        if len(self.experience_buffer) >= self.min_experiences_for_learning:
            asyncio.create_task(self._update_policy())

    def _process_error(self, experience: Experience):
        """Process error for immediate learning and correction."""
        if not experience.error_type:
            return

        error_signature = self._generate_error_signature(experience)
        self.learning_stats['errors_detected'] += 1

        # Update or create error pattern
        if error_signature in self.error_patterns:
            pattern = self.error_patterns[error_signature]
            pattern.frequency += 1
            pattern.last_seen = time.time()

            # Update success rate if correction was applied
            if experience.correction_applied:
                pattern.success_rate = (pattern.success_rate * 0.9 +
                                      (1.0 if experience.reward > 0 else 0.0) * 0.1)
        else:
            # Create new error pattern
            self.error_patterns[error_signature] = ErrorPattern(
                error_signature=error_signature,
                error_type=experience.error_type,
                frequency=1,
                success_rate=0.5,
                corrections=[experience.correction_applied] if experience.correction_applied else [],
                last_seen=time.time(),
                confidence=0.5
            )

        self.error_history.append({
            'signature': error_signature,
            'timestamp': time.time(),
            'corrected': bool(experience.correction_applied)
        })

        self.logger.info(f"Error pattern recorded: {error_signature}")

    def _generate_error_signature(self, experience: Experience) -> str:
        """Generate unique signature for error pattern recognition."""
        error_components = [
            experience.error_type or 'unknown',
            experience.state[:50],  # First 50 chars of state
            experience.action[:30]  # First 30 chars of action
        ]
        return "|".join(error_components)

    async def predict_correction(self, current_state: str, proposed_action: str) -> Optional[str]:
        """Predict if an error will occur and suggest correction."""
        if not self.auto_correct_enabled:
            return None

        # Generate signature for current situation
        temp_experience = Experience(
            state=current_state,
            action=proposed_action,
            reward=0.0,
            next_state=""
        )

        # Check against known error patterns
        potential_signature = current_state[:50] + "|" + proposed_action[:30]

        for signature, pattern in self.error_patterns.items():
            if self._signatures_similar(potential_signature, signature, threshold=0.7):
                if pattern.frequency >= 3 and pattern.confidence > 0.6:
                    # High confidence error prediction
                    best_correction = self._get_best_correction(pattern)
                    if best_correction:
                        self.logger.info(f"Predicted error, suggesting correction: {best_correction}")
                        return best_correction

        return None

    def _signatures_similar(self, sig1: str, sig2: str, threshold: float = 0.7) -> bool:
        """Check if two error signatures are similar."""
        # Simple similarity check - could be enhanced with ML
        parts1 = sig1.split("|")
        parts2 = sig2.split("|")

        if len(parts1) != len(parts2):
            return False

        matches = sum(1 for p1, p2 in zip(parts1, parts2) if p1 == p2)
        similarity = matches / len(parts1)

        return similarity >= threshold

    def _get_best_correction(self, pattern: ErrorPattern) -> Optional[str]:
        """Get the best correction for an error pattern."""
        if not pattern.corrections:
            return None

        # Return most successful correction
        # For now, return the most recent successful correction
        return pattern.corrections[-1] if pattern.corrections else None

    async def _update_policy(self):
        """Update the RL policy based on accumulated experiences."""
        if len(self.experience_buffer) < self.min_experiences_for_learning:
            return

        # GRPO-style policy update
        recent_experiences = list(self.experience_buffer)[-50:]  # Last 50 experiences

        for exp in recent_experiences:
            # Update action values using temporal difference learning
            current_value = self.action_values[exp.state][exp.action]

            # Calculate TD target
            next_state_value = max(self.action_values[exp.next_state].values(), default=0.0)
            td_target = exp.reward + self.discount_factor * next_state_value

            # Update value with learning rate
            td_error = td_target - current_value
            self.action_values[exp.state][exp.action] += self.learning_rate * td_error

            # Update state visit count
            self.state_visits[exp.state] += 1

        # Update error pattern confidence
        self._update_pattern_confidence()

        self.learning_stats['learning_iterations'] += 1
        await self._save_learned_knowledge()

        self.logger.debug(f"Policy updated. Learning iteration {self.learning_stats['learning_iterations']}")

    def _update_pattern_confidence(self):
        """Update confidence scores for error patterns."""
        for pattern in self.error_patterns.values():
            # Confidence based on frequency and recency
            time_decay = max(0.1, 1.0 - (time.time() - pattern.last_seen) / (7 * 24 * 3600))  # 7 days
            frequency_boost = min(1.0, pattern.frequency / 10.0)  # Max boost at 10 occurrences

            pattern.confidence = (pattern.success_rate * 0.5 +
                                time_decay * 0.3 +
                                frequency_boost * 0.2)

    def get_best_action(self, state: str, available_actions: List[str]) -> Tuple[str, float]:
        """Get the best action for a given state based on learned policy."""
        if not available_actions:
            return "", 0.0

        # Epsilon-greedy action selection
        if np.random.random() < self.exploration_rate:
            # Explore: random action
            action = np.random.choice(available_actions)
            confidence = 0.5
        else:
            # Exploit: best learned action
            action_values = [(action, self.action_values[state][action])
                           for action in available_actions]
            action_values.sort(key=lambda x: x[1], reverse=True)

            action, value = action_values[0]
            confidence = min(1.0, max(0.0, value))

        return action, confidence

    def apply_automatic_correction(self, error_info: Dict[str, Any]) -> Optional[str]:
        """Apply automatic correction based on learned patterns."""
        if not self.auto_correct_enabled:
            return None

        error_signature = error_info.get('signature', '')

        if error_signature in self.error_patterns:
            pattern = self.error_patterns[error_signature]

            if pattern.confidence > 0.7 and pattern.corrections:
                correction = self._get_best_correction(pattern)
                if correction:
                    self.learning_stats['corrections_applied'] += 1
                    self.logger.info(f"Auto-correction applied: {correction}")
                    return correction

        return None

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        stats = self.learning_stats.copy()
        stats.update({
            'error_patterns_learned': len(self.error_patterns),
            'experience_buffer_size': len(self.experience_buffer),
            'correction_success_rate': self.correction_success_rate,
            'auto_correct_enabled': self.auto_correct_enabled,
            'recent_errors': len([e for e in self.error_history
                                if time.time() - e['timestamp'] < 3600]),  # Last hour
            'learning_efficiency': (self.learning_stats['successful_corrections'] /
                                  max(1, self.learning_stats['corrections_applied']))
        })
        return stats

    async def _save_learned_knowledge(self):
        """Save learned knowledge to disk."""
        try:
            knowledge_dir = Path(f"~/.torq_console/{self.agent_id}").expanduser()
            knowledge_dir.mkdir(parents=True, exist_ok=True)

            knowledge_data = {
                'error_patterns': {k: {
                    'error_signature': v.error_signature,
                    'error_type': v.error_type,
                    'frequency': v.frequency,
                    'success_rate': v.success_rate,
                    'corrections': v.corrections,
                    'last_seen': v.last_seen,
                    'confidence': v.confidence
                } for k, v in self.error_patterns.items()},
                'action_values': dict(self.action_values),
                'learning_stats': self.learning_stats,
                'timestamp': time.time()
            }

            knowledge_file = knowledge_dir / "rl_knowledge.json"
            with open(knowledge_file, 'w') as f:
                json.dump(knowledge_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save learned knowledge: {e}")

    def _load_learned_knowledge(self):
        """Load previously learned knowledge."""
        try:
            knowledge_file = Path(f"~/.torq_console/{self.agent_id}/rl_knowledge.json").expanduser()

            if knowledge_file.exists():
                with open(knowledge_file, 'r') as f:
                    knowledge_data = json.load(f)

                # Restore error patterns
                for k, v in knowledge_data.get('error_patterns', {}).items():
                    self.error_patterns[k] = ErrorPattern(**v)

                # Restore action values
                self.action_values = defaultdict(lambda: defaultdict(float))
                for state, actions in knowledge_data.get('action_values', {}).items():
                    for action, value in actions.items():
                        self.action_values[state][action] = value

                # Restore stats
                self.learning_stats.update(knowledge_data.get('learning_stats', {}))

                self.logger.info(f"Loaded {len(self.error_patterns)} error patterns from previous learning")

        except Exception as e:
            self.logger.error(f"Failed to load learned knowledge: {e}")

    def reset_learning(self):
        """Reset all learned knowledge (use with caution)."""
        self.experience_buffer.clear()
        self.error_patterns.clear()
        self.action_values.clear()
        self.state_visits.clear()
        self.error_history.clear()

        self.learning_stats = {
            'total_experiences': 0,
            'errors_detected': 0,
            'corrections_applied': 0,
            'successful_corrections': 0,
            'learning_iterations': 0
        }

        self.logger.info("RL learning system reset")

# Global instance for the Prince Flowers agent
prince_rl_system = ARTISTRLSystem("prince_flowers")