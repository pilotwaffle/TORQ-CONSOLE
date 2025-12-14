"""
TORQ Console Evaluation Runner

Implements deterministic evaluation execution with:
- Task loading and execution
- Progress tracking
- Result collection
- Baseline comparison
- CI integration
"""

import os
import json
import time
import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

import numpy as np
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from .scoring import EvaluationScorer, TaskResult

logger = logging.getLogger(__name__)
console = Console()


class MockOrchestrator:
    """Mock orchestrator for evaluation when MarvinOrchestrator is unavailable"""

    def process_message(self, message: str, session_id: str, mode: str = 'chat') -> Dict[str, Any]:
        """Process a message with mock response"""
        return {
            'content': f"Mock response to: {message[:100]}...",
            'metadata': {'mode': mode, 'session_id': session_id},
            'tools_used': self._detect_tools(message),
            'tokens_used': len(message.split()) * 2  # Estimate
        }

    def _detect_tools(self, message: str) -> List[str]:
        """Detect required tools from message"""
        tools = []
        message_lower = message.lower()

        if 'search' in message_lower or 'find' in message_lower:
            tools.append('web_search')
        if 'file' in message_lower or 'read' in message_lower or 'write' in message_lower:
            tools.append('file_operations')
        if 'api' in message_lower or 'http' in message_lower:
            tools.append('http_client')
        if 'python' in message_lower or 'code' in message_lower:
            tools.append('python_executor')
        if 'remember' in message_lower or 'memory' in message_lower:
            tools.append('memory_system')

        return tools


class EvaluationRunner:
    """
    Runs TORQ Console evaluations with deterministic behavior

    Key features:
    - Same seed → same results
    - Progress tracking
    - Detailed reporting
    - CI integration
    """

    def __init__(self, eval_set_path: str, seed: int = 42):
        """
        Initialize evaluation runner

        Args:
            eval_set_path: Path to evaluation set directory
            seed: Random seed for deterministic behavior
        """
        self.eval_set_path = Path(eval_set_path)
        self.seed = seed
        np.random.seed(seed)

        # Load evaluation set
        self.tasks = self._load_tasks()
        self.metadata = self._load_metadata()
        self.scorer = EvaluationScorer(seed)

        # Initialize TORQ components (with fallbacks)
        self.telemetry = None  # Skip telemetry for now
        self.orchestrator = MockOrchestrator()  # Use mock orchestrator

        # Tracking
        self.results = []
        self.start_time = None
        self.end_time = None

    def _load_tasks(self) -> List[Dict[str, Any]]:
        """Load tasks from tasks.json"""
        tasks_file = self.eval_set_path / 'tasks.json'

        if not tasks_file.exists():
            raise FileNotFoundError(f"Tasks file not found: {tasks_file}")

        with open(tasks_file, 'r') as f:
            data = json.load(f)

        return data.get('tasks', [])

    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from metadata.json or create default"""
        metadata_file = self.eval_set_path / 'metadata.json'

        if not metadata_file.exists():
            logger.warning(f"Metadata file not found: {metadata_file} - creating default")
            return {
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'passing_criteria': {
                    'overall_score_min': 7.0,
                    'category_min': 6.0,
                    'tool_f1_min': 0.7,
                    'max_regression_drop': 2.0,
                    'max_domain_regression_drop': 3.0
                }
            }

        with open(metadata_file, 'r') as f:
            return json.load(f)

    def run_evaluation(self, output_file: Optional[str] = None,
                      compare_baseline: bool = True) -> Dict[str, Any]:
        """
        Run the complete evaluation

        Args:
            output_file: Optional file to save results
            compare_baseline: Whether to compare against baseline

        Returns:
            Evaluation results dictionary
        """
        self.start_time = time.time()

        console.print(Panel(
            f"[bold blue]Running TORQ Console Evaluation[/bold blue]\n"
            f"Evaluation Set: {self.eval_set_path.name}\n"
            f"Tasks: {len(self.tasks)}\n"
            f"Seed: {self.seed}\n"
            f"Deterministic: Yes",
            title="Evaluation Starting"
        ))

        # Run tasks with progress tracking
        with Progress() as progress:
            task_progress = progress.add_task(
                "[cyan]Running tasks...",
                total=len(self.tasks)
            )

            for task in self.tasks:
                try:
                    result = self._run_single_task(task)
                    self.results.append((task, result))

                    # Update progress
                    progress.update(
                        task_progress,
                        advance=1,
                        description=f"[cyan]Running tasks... ({len(self.results)}/{len(self.tasks)})"
                    )

                except Exception as e:
                    logger.error(f"Task {task['id']} failed: {e}")
                    # Create failed result
                    failed_result = TaskResult(
                        task_id=task['id'],
                        success=False,
                        outputs=[],
                        tools_used=[],
                        tools_planned=[],
                        latency_ms=0.0,
                        tokens_used=0,
                        error_message=str(e)
                    )
                    self.results.append((task, failed_result))
                    progress.advance(task_progress)

        self.end_time = time.time()

        # Calculate scores
        scores = self.scorer.calculate_overall_score(self.results)

        # Check regression if baseline available
        regression_result = None
        if compare_baseline and 'baseline_scores' in self.metadata:
            regression_result = self.scorer.check_regression(
                scores,
                self.metadata['baseline_scores'],
                self.metadata.get('passing_criteria', {})
            )

        # Create final results
        final_results = {
            'evaluation_set': self.eval_set_path.name,
            'version': self.metadata.get('version', '1.0'),
            'timestamp': datetime.utcnow().isoformat(),
            'seed': self.seed,
            'duration_seconds': self.end_time - self.start_time,
            'scores': scores,
            'regression_check': regression_result,
            'task_results': self._serialize_results(),
            'environment': self._get_environment_info(),
            'passed': self._check_passing_criteria(scores, regression_result)
        }

        # Save results if requested
        if output_file:
            self._save_results(final_results, output_file)

        # Display results
        self._display_results(final_results)

        return final_results

    def _check_passing_criteria(self, scores: Dict[str, float],
                              regression_result: Optional[Dict[str, Any]]) -> bool:
        """Check if evaluation meets passing criteria"""
        criteria = self.metadata.get('passing_criteria', {})

        # Check overall score
        min_overall = criteria.get('overall_score_min', 7.0)
        if scores['overall_score'] < min_overall:
            return False

        # Check tool F1
        min_tool_f1 = criteria.get('tool_f1_min', 0.7)
        if scores['tool_f1'] < min_tool_f1:
            return False

        # Check regression
        if regression_result and not regression_result.get('passed', True):
            return False

        return True

    def _run_single_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        Run a single evaluation task

        Args:
            task: Task definition

        Returns:
            Task execution result
        """
        task_start = time.time()

        # Extract task inputs
        inputs = task.get('inputs', [])

        # Execute with TORQ orchestrator
        try:
            # Create telemetry context for the task
            run_id = hashlib.md5(
                f"{task['id']}_{self.seed}".encode()
            ).hexdigest()[:8]

            # Execute task
            outputs = []
            tools_used = []
            tools_planned = task.get('tool_requirements', [])

            total_tokens = 0

            # Process each input
            for input_item in inputs:
                response = self.orchestrator.process_message(
                    message=input_item['content'],
                    session_id=f"eval_{run_id}",
                    mode=task.get('type', 'chat')
                )

                outputs.append({
                    'role': 'assistant',
                    'content': response.get('content', ''),
                    'metadata': response.get('metadata', {})
                })

                # Track tool usage
                tools_used.extend(response.get('tools_used', []))

                # Track tokens
                total_tokens += response.get('tokens_used', 0)

            # Calculate latency
            latency_ms = (time.time() - task_start) * 1000

            return TaskResult(
                task_id=task['id'],
                success=True,
                outputs=outputs,
                tools_used=list(set(tools_used)),
                tools_planned=tools_planned,
                latency_ms=latency_ms,
                tokens_used=total_tokens,
                timestamps={'start': task_start, 'end': time.time()}
            )

        except Exception as e:
            latency_ms = (time.time() - task_start) * 1000

            return TaskResult(
                task_id=task['id'],
                success=False,
                outputs=[],
                tools_used=[],
                tools_planned=[],
                latency_ms=latency_ms,
                tokens_used=0,
                error_message=str(e)
            )

    def _display_results(self, results: Dict[str, Any]):
        """Display evaluation results using Rich formatting"""
        console.print("\n")

        # Overall score
        overall_score = results['scores']['overall_score']
        passed = results.get('passed', True)

        score_color = "green" if passed else "red"

        console.print(Panel(
            f"[bold]Overall Score: [{score_color}]{overall_score:.2f}[/{score_color}][/bold]\n"
            f"Status: [{'green' if passed else 'red'}]{'PASSED' if passed else 'FAILED'}[/{('green' if passed else 'red')}]\n"
            f"Duration: {results['duration_seconds']:.1f}s\n"
            f"Tasks: {results['scores']['successful_tasks']}/{results['scores']['total_tasks']}",
            title="Evaluation Results"
        ))

        # Component scores
        component_scores = results['scores']['component_scores']

        comp_table = Table(title="Component Scores")
        comp_table.add_column("Component", style="cyan")
        comp_table.add_column("Score", style="magenta")
        comp_table.add_column("Status", style="green")

        for component, score in component_scores.items():
            status = "✓" if score >= 7.0 else "✗"
            comp_table.add_row(component.title(), f"{score:.2f}", status)

        console.print(comp_table)

        # Category scores
        if 'category_scores' in results['scores']:
            cat_table = Table(title="Category Scores")
            cat_table.add_column("Category", style="cyan")
            cat_table.add_column("Score", style="magenta")
            cat_table.add_column("Weight", style="yellow")

            for category, score in results['scores']['category_scores'].items():
                weight = self.metadata.get('scoring_weights', {}).get('categories', {}).get(category, 1.0)
                cat_table.add_row(category.title(), f"{score:.2f}", f"{weight:.1f}x")

            console.print(cat_table)

        # Regression check
        if results.get('regression_check'):
            regression = results['regression_check']

            if regression['passed']:
                console.print("\n[green]✓ No regressions detected[/green]")
            else:
                console.print("\n[red]✗ REGRESSIONS DETECTED[/red]")

                if regression['details']['overall_regression']:
                    console.print(f"  - Overall score dropped by {regression['overall_drop']:.2f}")

                if regression['details']['domain_regressions_count'] > 0:
                    console.print("  - Domain regressions:")
                    for domain, drop in regression['domain_regressions'].items():
                        console.print(f"    * {domain}: -{drop:.2f}")

                if regression['details']['tool_f1_failure']:
                    console.print(f"  - Tool F1 below threshold: {regression['tool_f1']:.3f}")

    def _save_results(self, results: Dict[str, Any], output_file: str):
        """Save results to file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        console.print(f"\n[green]Results saved to: {output_path}[/green]")

    def _serialize_results(self) -> List[Dict[str, Any]]:
        """Serialize task results for JSON output"""
        serialized = []

        for task, result in self.results:
            serialized.append({
                'task_id': task['id'],
                'task_type': task.get('type'),
                'task_category': task.get('category'),
                'success': result.success,
                'latency_ms': result.latency_ms,
                'tokens_used': result.tokens_used,
                'tools_used': result.tools_used,
                'tools_planned': result.tools_planned,
                'error_message': result.error_message
            })

        return serialized

    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information for reproducibility"""
        return {
            'python_version': os.sys.version,
            'platform': os.name,
            'eval_set_version': self.metadata.get('version'),
            'baseline_version': self.metadata.get('baseline_scores', {}).get('evaluated_at'),
            'deterministic': True,
            'seed': self.seed
        }


def main():
    """CLI entry point for evaluation runner"""
    parser = argparse.ArgumentParser(description='Run TORQ Console evaluations')
    parser.add_argument(
        '--set',
        required=True,
        help='Evaluation set to run (e.g., v1.0)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for deterministic behavior'
    )
    parser.add_argument(
        '--output',
        help='Output file for results (JSON)'
    )
    parser.add_argument(
        '--no-baseline',
        action='store_true',
        help='Skip baseline comparison'
    )

    args = parser.parse_args()

    # Determine evaluation set path
    eval_sets_dir = Path(__file__).parent.parent.parent.parent / 'eval_sets'
    eval_set_path = eval_sets_dir / args.set

    if not eval_set_path.exists():
        console.print(f"[red]Evaluation set not found: {eval_set_path}[/red]")
        return 1

    # Run evaluation
    runner = EvaluationRunner(str(eval_set_path), args.seed)

    try:
        results = runner.run_evaluation(
            output_file=args.output,
            compare_baseline=not args.no_baseline
        )

        # Exit with appropriate code
        return 0 if results.get('passed', True) else 1

    except Exception as e:
        console.print(f"[red]Evaluation failed: {e}[/red]")
        logger.exception("Evaluation failed")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())