"""
Core Marvin Integration for TORQ Console

Provides the main integration point for Marvin functionality.
"""

import os
import logging
from typing import Type, TypeVar, List, Any, Optional
from enum import Enum

import marvin
from pydantic import BaseModel, Field

T = TypeVar('T')

logger = logging.getLogger(__name__)


class TorqMarvinIntegration:
    """
    Main integration point for Marvin in TORQ Console.

    Provides structured outputs, data extraction, classification,
    and agentic workflow capabilities.
    """

    def __init__(
        self,
        model: str = "anthropic/claude-sonnet-4-20250514",
        api_key: Optional[str] = None
    ):
        """
        Initialize Marvin integration for TORQ Console.

        Args:
            model: Default LLM model to use
            api_key: API key for LLM provider (uses env var if not provided)
        """
        self.model = model
        self.api_key = api_key or self._get_api_key()

        # Configure Marvin
        if self.api_key and self.model:
            if "anthropic" in self.model.lower():
                os.environ.setdefault("ANTHROPIC_API_KEY", self.api_key)
            elif "openai" in self.model.lower() or "gpt" in self.model.lower():
                os.environ.setdefault("OPENAI_API_KEY", self.api_key)

        # Performance metrics
        self.metrics = {
            'extractions': 0,
            'casts': 0,
            'classifications': 0,
            'generations': 0,
            'task_runs': 0,
        }

        logger.info(f"Marvin integration initialized with model: {model}")

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment."""
        return (
            os.getenv("ANTHROPIC_API_KEY") or
            os.getenv("OPENAI_API_KEY") or
            os.getenv("OPENROUTER_API_KEY")
        )

    def extract(
        self,
        text: str,
        target_type: Type[T],
        instructions: Optional[str] = None
    ) -> List[T]:
        """
        Extract structured data from unstructured text.

        Args:
            text: Input text to extract from
            target_type: Type to extract (e.g., int, str, custom model)
            instructions: Optional instructions for extraction

        Returns:
            List of extracted items of target_type

        Example:
            >>> integration = TorqMarvinIntegration()
            >>> prices = integration.extract(
            ...     "Laptop costs $1299, mouse is $29",
            ...     int,
            ...     instructions="extract USD amounts"
            ... )
            >>> print(prices)  # [1299, 29]
        """
        self.metrics['extractions'] += 1
        logger.debug(f"Extracting {target_type.__name__} from text: {text[:50]}...")

        result = marvin.extract(
            text,
            target_type,
            instructions=instructions
        )

        logger.info(f"Extracted {len(result)} items of type {target_type.__name__}")
        return result

    def cast(
        self,
        text: str,
        target_type: Type[T],
        instructions: Optional[str] = None
    ) -> T:
        """
        Cast unstructured text into a structured type.

        Args:
            text: Input text to cast
            target_type: Target type (must be a Pydantic model or basic type)
            instructions: Optional instructions for casting

        Returns:
            Instance of target_type

        Example:
            >>> from pydantic import BaseModel
            >>> class Person(BaseModel):
            ...     name: str
            ...     age: int
            >>> integration = TorqMarvinIntegration()
            >>> person = integration.cast("John is 30", Person)
            >>> print(person)  # Person(name='John', age=30)
        """
        self.metrics['casts'] += 1
        logger.debug(f"Casting text to {target_type.__name__}: {text[:50]}...")

        result = marvin.cast(
            text,
            target_type,
            instructions=instructions
        )

        logger.info(f"Cast to {target_type.__name__}: {result}")
        return result

    def classify(
        self,
        text: str,
        labels: Type[Enum],
        instructions: Optional[str] = None
    ) -> Enum:
        """
        Classify text into one of predefined labels.

        Args:
            text: Text to classify
            labels: Enum of possible labels
            instructions: Optional instructions for classification

        Returns:
            One of the enum labels

        Example:
            >>> from enum import Enum
            >>> class Priority(Enum):
            ...     LOW = "low"
            ...     HIGH = "high"
            >>> integration = TorqMarvinIntegration()
            >>> priority = integration.classify("Server is down!", Priority)
            >>> print(priority)  # Priority.HIGH
        """
        self.metrics['classifications'] += 1
        logger.debug(f"Classifying text into {labels.__name__}: {text[:50]}...")

        result = marvin.classify(
            text,
            labels,
            instructions=instructions
        )

        logger.info(f"Classified as: {result}")
        return result

    def generate(
        self,
        target_type: Type[T],
        n: int,
        instructions: str
    ) -> List[T]:
        """
        Generate structured data from a description.

        Args:
            target_type: Type to generate
            n: Number of items to generate
            instructions: Description of what to generate

        Returns:
            List of n generated items

        Example:
            >>> integration = TorqMarvinIntegration()
            >>> cities = integration.generate(str, 5, "major CA cities")
            >>> print(cities)  # ['Los Angeles', 'San Francisco', ...]
        """
        self.metrics['generations'] += 1
        logger.debug(f"Generating {n} {target_type.__name__} items: {instructions[:50]}...")

        result = marvin.generate(
            target_type,
            n,
            instructions
        )

        logger.info(f"Generated {len(result)} items")
        return result

    def run(
        self,
        task: str,
        result_type: Optional[Type[T]] = None,
        context: Optional[dict] = None,
        agents: Optional[List] = None
    ) -> T:
        """
        Run a simple task with Marvin.

        Args:
            task: Task description
            result_type: Expected result type (optional, defaults to str)
            context: Additional context for the task
            agents: Specific agents to use (optional)

        Returns:
            Task result of result_type

        Example:
            >>> integration = TorqMarvinIntegration()
            >>> answer = integration.run(
            ...     "What is 2+2?",
            ...     result_type=int
            ... )
            >>> print(answer)  # 4
        """
        self.metrics['task_runs'] += 1
        logger.debug(f"Running task: {task[:50]}...")

        result = marvin.run(
            task,
            result_type=result_type,
            context=context,
            agents=agents
        )

        logger.info(f"Task completed: {task[:50]}...")
        return result

    def create_agent(
        self,
        name: str,
        instructions: str,
        tools: Optional[List] = None,
        model: Optional[str] = None
    ) -> marvin.Agent:
        """
        Create a specialized Marvin agent.

        Args:
            name: Agent name
            instructions: Agent instructions/personality
            tools: Optional list of tools for the agent
            model: Optional model override

        Returns:
            Marvin Agent instance

        Example:
            >>> integration = TorqMarvinIntegration()
            >>> poet = integration.create_agent(
            ...     name="Poet",
            ...     instructions="Write creative poetry"
            ... )
        """
        agent = marvin.Agent(
            name=name,
            instructions=instructions,
            tools=tools or [],
            model=model or self.model
        )

        logger.info(f"Created agent: {name}")
        return agent

    def get_metrics(self) -> dict:
        """Get usage metrics."""
        return self.metrics.copy()

    def reset_metrics(self):
        """Reset usage metrics."""
        self.metrics = {key: 0 for key in self.metrics}
        logger.info("Metrics reset")
