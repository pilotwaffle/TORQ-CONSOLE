"""
Preference Learning for TORQ Console Agents.

Automatically detects and learns user preferences from conversations.
"""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Pattern
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Preference:
    """A learned user preference."""
    category: str  # e.g., "language", "code_style", "format"
    preference: str  # e.g., "Python", "concise", "markdown"
    confidence: float  # 0.0-1.0
    first_seen: datetime
    last_updated: datetime
    occurrence_count: int = 1

    @property
    def value(self) -> str:
        """Alias for preference field for compatibility."""
        return self.preference


# Alias for compatibility
UserPreference = Preference


class PreferenceLearning:
    """
    Learns and tracks user preferences from conversations.

    Features:
    - Automatic preference detection
    - Confidence scoring
    - Preference application to responses
    - Preference updating over time
    """

    def __init__(self, memory_manager=None):
        """
        Initialize preference learning.

        Args:
            memory_manager: Optional Letta memory manager for persistence
        """
        self.memory = memory_manager
        self.logger = logging.getLogger(__name__)

        # In-memory preference store
        self.preferences: Dict[str, Preference] = {}

        # Preference detection patterns
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, List[Pattern]]:
        """Initialize regex patterns for preference detection."""
        return {
            "language": [
                re.compile(r"I (?:prefer|like|use|love) (\w+) (?:for|to|when)", re.IGNORECASE),
                re.compile(r"(\w+) is my (?:favorite|preferred) (?:language|tool)", re.IGNORECASE),
                re.compile(r"(?:always|usually) (?:use|write in) (\w+)", re.IGNORECASE),
                re.compile(r"I'?m a (\w+) (?:developer|programmer)", re.IGNORECASE),
            ],

            "code_style": [
                re.compile(r"I (?:prefer|like) (?:my code )?(concise|verbose|detailed|simple)", re.IGNORECASE),
                re.compile(r"keep (?:it|code|responses) (concise|verbose|simple|detailed)", re.IGNORECASE),
                re.compile(r"(?:always|please) (?:include|add|show) (comments|docstrings|types|tests)", re.IGNORECASE),
                re.compile(r"(?:don'?t|do not) (?:include|add) (comments|explanations|docstrings)", re.IGNORECASE),
            ],

            "format": [
                re.compile(r"(?:prefer|use|want) (markdown|json|yaml|plain text) (?:format)?", re.IGNORECASE),
                re.compile(r"show (?:me )?(examples|usage|tests)", re.IGNORECASE),
                re.compile(r"(?:include|add) (examples|usage examples|test cases)", re.IGNORECASE),
            ],

            "framework": [
                re.compile(r"I'?m using (\w+)(?: framework)?", re.IGNORECASE),
                re.compile(r"(?:we|I) (?:use|work with) (\w+)", re.IGNORECASE),
                re.compile(r"for (?:my|our|the) (\w+) (?:project|app|application)", re.IGNORECASE),
            ],

            "interaction": [
                re.compile(r"(?:always|please) (?:ask|confirm) (?:before|first)", re.IGNORECASE),
                re.compile(r"(?:just|directly) (?:do it|implement|create)", re.IGNORECASE),
                re.compile(r"(?:explain|tell me) (?:why|how|what)", re.IGNORECASE),
            ]
        }

    async def detect_and_store_preferences(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Preference]:
        """
        Detect preferences in a message and store them.

        Args:
            message: User message to analyze
            context: Optional context information

        Returns:
            List of detected preferences
        """
        detected = []

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.findall(message)

                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]  # Extract from regex group

                    preference = match.strip().lower()

                    if preference:
                        pref = await self._store_preference(
                            category=category,
                            preference=preference,
                            confidence=0.7  # Initial confidence
                        )
                        detected.append(pref)

        if detected:
            self.logger.info(f"Detected {len(detected)} preferences")

        return detected

    async def _store_preference(
        self,
        category: str,
        preference: str,
        confidence: float
    ) -> Preference:
        """Store or update a preference."""
        pref_key = f"{category}:{preference}"

        if pref_key in self.preferences:
            # Update existing preference
            pref = self.preferences[pref_key]
            pref.last_updated = datetime.now()
            pref.occurrence_count += 1
            # Increase confidence with each occurrence (max 1.0)
            pref.confidence = min(pref.confidence + 0.1, 1.0)
        else:
            # Create new preference
            pref = Preference(
                category=category,
                preference=preference,
                confidence=confidence,
                first_seen=datetime.now(),
                last_updated=datetime.now()
            )
            self.preferences[pref_key] = pref

        # Store in Letta memory if available
        if self.memory:
            try:
                await self.memory.add_memory(
                    f"User preference: {category} = {preference}",
                    metadata={
                        "type": "preference",
                        "category": category,
                        "preference": preference,
                        "confidence": pref.confidence
                    },
                    importance=0.9
                )
            except Exception as e:
                self.logger.error(f"Error storing preference in memory: {e}")

        return pref

    def get_preferences(
        self,
        category: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> Dict[str, Preference]:
        """
        Get stored preferences.

        Args:
            category: Filter by category (None for all)
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary of preferences
        """
        filtered = {}

        for key, pref in self.preferences.items():
            if pref.confidence >= min_confidence:
                if category is None or pref.category == category:
                    filtered[key] = pref

        return filtered

    def get_all_preferences(self, min_confidence: float = 0.5) -> Dict[str, Preference]:
        """
        Get all stored preferences (alias for get_preferences).

        Args:
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary of all preferences
        """
        return self.get_preferences(category=None, min_confidence=min_confidence)

    def get_preferences_by_category(
        self,
        category: str,
        min_confidence: float = 0.5
    ) -> Dict[str, Preference]:
        """
        Get preferences filtered by category (alias for get_preferences with category).

        Args:
            category: Category to filter by
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary of preferences in the specified category
        """
        return self.get_preferences(category=category, min_confidence=min_confidence)

    async def apply_preferences_to_response(
        self,
        response: str,
        response_type: str = "code"
    ) -> str:
        """
        Apply learned preferences to modify a response.

        Args:
            response: Original response
            response_type: Type of response (code, explanation, etc.)

        Returns:
            Modified response with preferences applied
        """
        modified_response = response

        # Get high-confidence preferences
        prefs = self.get_preferences(min_confidence=0.7)

        # Apply code style preferences
        if response_type == "code":
            # Check for "concise" preference
            if any(p.preference == "concise" for p in prefs.values()):
                # Remove excessive comments (placeholder)
                self.logger.debug("Applying 'concise' preference")

            # Check for "comments" preference
            if any(p.preference == "comments" for p in prefs.values()):
                # Ensure comments are included (placeholder)
                self.logger.debug("Applying 'comments' preference")

        # Apply format preferences
        format_prefs = [p for p in prefs.values() if p.category == "format"]
        if format_prefs:
            preferred_format = format_prefs[0].preference
            self.logger.debug(f"Preferred format: {preferred_format}")

        # Apply language preferences
        language_prefs = [p for p in prefs.values() if p.category == "language"]
        if language_prefs and response_type == "code":
            preferred_lang = language_prefs[0].preference
            self.logger.debug(f"Preferred language: {preferred_lang}")

        return modified_response

    def get_preference_summary(self) -> Dict[str, Any]:
        """Get summary of all learned preferences."""
        summary = {
            "total_preferences": len(self.preferences),
            "by_category": {},
            "high_confidence": [],
            "recent": []
        }

        # Group by category
        for pref in self.preferences.values():
            if pref.category not in summary["by_category"]:
                summary["by_category"][pref.category] = []
            summary["by_category"][pref.category].append({
                "preference": pref.preference,
                "confidence": pref.confidence,
                "occurrences": pref.occurrence_count
            })

        # High confidence preferences
        high_conf = [
            {
                "category": p.category,
                "preference": p.preference,
                "confidence": p.confidence
            }
            for p in self.preferences.values()
            if p.confidence >= 0.8
        ]
        summary["high_confidence"] = sorted(
            high_conf,
            key=lambda x: x["confidence"],
            reverse=True
        )

        # Recently updated
        recent = sorted(
            self.preferences.values(),
            key=lambda x: x.last_updated,
            reverse=True
        )[:5]
        summary["recent"] = [
            {
                "category": p.category,
                "preference": p.preference,
                "last_updated": p.last_updated.isoformat()
            }
            for p in recent
        ]

        return summary

    def clear_preferences(self, category: Optional[str] = None):
        """
        Clear stored preferences.

        Args:
            category: Clear only this category (None for all)
        """
        if category is None:
            self.preferences.clear()
            self.logger.info("Cleared all preferences")
        else:
            keys_to_remove = [
                key for key, pref in self.preferences.items()
                if pref.category == category
            ]
            for key in keys_to_remove:
                del self.preferences[key]
            self.logger.info(f"Cleared preferences in category: {category}")


# Global preference learning instance
_preference_learning: Optional[PreferenceLearning] = None


def get_preference_learning(memory_manager=None) -> PreferenceLearning:
    """Get or create global preference learning instance."""
    global _preference_learning

    if _preference_learning is None:
        _preference_learning = PreferenceLearning(memory_manager=memory_manager)

    return _preference_learning
