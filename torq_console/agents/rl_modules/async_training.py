"""
AReaL-inspired Asynchronous Training System for TORQ Console
Based on AReaL: A Large-Scale Asynchronous Reinforcement Learning System
"""

import asyncio
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from queue import Queue, Empty
import json
from pathlib import Path

class WorkerType(Enum):
    """Types of workers in the asynchronous system."""
    ROLLOUT = "rollout"
    TRAINING = "training"
    EVALUATION = "evaluation"

class TaskStatus(Enum):
    """Status of asynchronous tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class RolloutTask:
    """Task for generating rollout data."""
    task_id: str
    state: str
    action_space: List[str]
    context: Dict[str, Any]
    max_steps: int = 10
    temperature: float = 1.0
    created_at: float = field(default_factory=time.time)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None

@dataclass
class TrainingBatch:
    """Batch of training data."""
    batch_id: str
    experiences: List[Dict[str, Any]]
    batch_size: int
    created_at: float = field(default_factory=time.time)
    processing_time: Optional[float] = None

@dataclass
class AsyncWorker:
    """Asynchronous worker for rollouts or training."""
    worker_id: str
    worker_type: WorkerType
    status: str = "idle"
    tasks_completed: int = 0
    total_processing_time: float = 0.0
    last_activity: float = field(default_factory=time.time)
    current_task: Optional[str] = None

class AsyncTrainingSystem:
    """AReaL-inspired asynchronous training system with decoupled generation and training."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("TORQ.AsyncRL")

        # System configuration
        self.max_rollout_workers = config.get('max_rollout_workers', 4)
        self.max_training_workers = config.get('max_training_workers', 2)
        self.batch_size = config.get('batch_size', 32)
        self.max_queue_size = config.get('max_queue_size', 1000)

        # Worker management
        self.rollout_workers: Dict[str, AsyncWorker] = {}
        self.training_workers: Dict[str, AsyncWorker] = {}
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_rollout_workers + self.max_training_workers
        )

        # Task queues
        self.rollout_queue = Queue(maxsize=self.max_queue_size)
        self.training_queue = Queue(maxsize=self.max_queue_size)
        self.result_queue = Queue(maxsize=self.max_queue_size)

        # Data storage
        self.experience_buffer = []
        self.training_batches = []
        self.completed_rollouts = {}

        # Synchronization
        self.running = False
        self.lock = threading.Lock()

        # Performance tracking
        self.performance_metrics = {
            'rollouts_generated': 0,
            'training_batches_processed': 0,
            'total_experiences': 0,
            'avg_rollout_time': 0.0,
            'avg_training_time': 0.0,
            'gpu_utilization': 0.0,
            'throughput': 0.0
        }

        # Initialize workers
        self._initialize_workers()

    def _initialize_workers(self):
        """Initialize rollout and training workers."""
        # Create rollout workers
        for i in range(self.max_rollout_workers):
            worker_id = f"rollout_worker_{i}"
            self.rollout_workers[worker_id] = AsyncWorker(
                worker_id=worker_id,
                worker_type=WorkerType.ROLLOUT
            )

        # Create training workers
        for i in range(self.max_training_workers):
            worker_id = f"training_worker_{i}"
            self.training_workers[worker_id] = AsyncWorker(
                worker_id=worker_id,
                worker_type=WorkerType.TRAINING
            )

        self.logger.info(
            f"Initialized {self.max_rollout_workers} rollout workers and "
            f"{self.max_training_workers} training workers"
        )

    async def start_async_training(self):
        """Start the asynchronous training system."""
        if self.running:
            self.logger.warning("Async training system is already running")
            return

        self.running = True
        self.logger.info("Starting asynchronous training system")

        # Start worker loops
        tasks = []

        # Start rollout workers
        for worker_id in self.rollout_workers:
            task = asyncio.create_task(self._rollout_worker_loop(worker_id))
            tasks.append(task)

        # Start training workers
        for worker_id in self.training_workers:
            task = asyncio.create_task(self._training_worker_loop(worker_id))
            tasks.append(task)

        # Start batch collector
        batch_task = asyncio.create_task(self._batch_collector_loop())
        tasks.append(batch_task)

        # Start performance monitor
        monitor_task = asyncio.create_task(self._performance_monitor_loop())
        tasks.append(monitor_task)

        self.logger.info("All async training workers started")

        # Wait for completion (or run indefinitely)
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            self.logger.info("Async training system cancelled")
        except Exception as e:
            self.logger.error(f"Error in async training system: {e}")
        finally:
            await self.stop_async_training()

    async def stop_async_training(self):
        """Stop the asynchronous training system."""
        self.logger.info("Stopping asynchronous training system")
        self.running = False

        # Wait a moment for workers to finish current tasks
        await asyncio.sleep(1.0)

        # Shutdown executor
        self.executor.shutdown(wait=True)

        # Clear queues
        self._clear_queues()

        self.logger.info("Async training system stopped")

    async def submit_rollout_task(self, state: str, action_space: List[str],
                                context: Dict[str, Any]) -> str:
        """Submit a rollout task for asynchronous processing."""
        task_id = f"rollout_{int(time.time() * 1000)}_{np.random.randint(10000)}"

        task = RolloutTask(
            task_id=task_id,
            state=state,
            action_space=action_space,
            context=context
        )

        try:
            self.rollout_queue.put_nowait(task)
            self.logger.debug(f"Submitted rollout task: {task_id}")
            return task_id
        except:
            self.logger.error("Rollout queue is full, dropping task")
            raise RuntimeError("Rollout queue is full")

    async def get_rollout_result(self, task_id: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Get the result of a rollout task."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.lock:
                if task_id in self.completed_rollouts:
                    result = self.completed_rollouts.pop(task_id)
                    return result

            await asyncio.sleep(0.1)  # Check every 100ms

        self.logger.warning(f"Rollout task {task_id} timed out")
        return None

    async def _rollout_worker_loop(self, worker_id: str):
        """Main loop for rollout workers."""
        worker = self.rollout_workers[worker_id]
        self.logger.debug(f"Starting rollout worker: {worker_id}")

        while self.running:
            try:
                # Get task from queue (non-blocking)
                try:
                    task = self.rollout_queue.get_nowait()
                    worker.status = "busy"
                    worker.current_task = task.task_id
                    worker.last_activity = time.time()
                except Empty:
                    worker.status = "idle"
                    worker.current_task = None
                    await asyncio.sleep(0.1)  # Wait a bit before checking again
                    continue

                # Process rollout
                start_time = time.time()
                result = await self._process_rollout_task(task, worker_id)
                processing_time = time.time() - start_time

                # Store result
                with self.lock:
                    self.completed_rollouts[task.task_id] = result
                    worker.tasks_completed += 1
                    worker.total_processing_time += processing_time

                # Update performance metrics
                self.performance_metrics['rollouts_generated'] += 1
                self._update_avg_rollout_time(processing_time)

                self.logger.debug(f"Completed rollout {task.task_id} in {processing_time:.3f}s")

            except Exception as e:
                self.logger.error(f"Error in rollout worker {worker_id}: {e}")
                worker.status = "error"
                await asyncio.sleep(1.0)  # Wait before retrying

        worker.status = "stopped"
        self.logger.debug(f"Rollout worker {worker_id} stopped")

    async def _training_worker_loop(self, worker_id: str):
        """Main loop for training workers."""
        worker = self.training_workers[worker_id]
        self.logger.debug(f"Starting training worker: {worker_id}")

        while self.running:
            try:
                # Get training batch from queue (non-blocking)
                try:
                    batch = self.training_queue.get_nowait()
                    worker.status = "busy"
                    worker.current_task = batch.batch_id
                    worker.last_activity = time.time()
                except Empty:
                    worker.status = "idle"
                    worker.current_task = None
                    await asyncio.sleep(0.5)  # Wait longer for training
                    continue

                # Process training batch
                start_time = time.time()
                await self._process_training_batch(batch, worker_id)
                processing_time = time.time() - start_time

                # Update worker stats
                with self.lock:
                    worker.tasks_completed += 1
                    worker.total_processing_time += processing_time
                    batch.processing_time = processing_time

                # Update performance metrics
                self.performance_metrics['training_batches_processed'] += 1
                self._update_avg_training_time(processing_time)

                self.logger.debug(f"Completed training batch {batch.batch_id} in {processing_time:.3f}s")

            except Exception as e:
                self.logger.error(f"Error in training worker {worker_id}: {e}")
                worker.status = "error"
                await asyncio.sleep(1.0)  # Wait before retrying

        worker.status = "stopped"
        self.logger.debug(f"Training worker {worker_id} stopped")

    async def _batch_collector_loop(self):
        """Collect experiences into training batches."""
        self.logger.debug("Starting batch collector")

        while self.running:
            try:
                # Check if we have enough experiences for a batch
                if len(self.experience_buffer) >= self.batch_size:
                    with self.lock:
                        # Create training batch
                        batch_experiences = self.experience_buffer[:self.batch_size]
                        self.experience_buffer = self.experience_buffer[self.batch_size:]

                        batch_id = f"batch_{int(time.time() * 1000)}_{np.random.randint(10000)}"
                        batch = TrainingBatch(
                            batch_id=batch_id,
                            experiences=batch_experiences,
                            batch_size=len(batch_experiences)
                        )

                        # Queue for training
                        try:
                            self.training_queue.put_nowait(batch)
                            self.training_batches.append(batch)
                            self.logger.debug(f"Created training batch: {batch_id}")
                        except:
                            self.logger.error("Training queue is full, dropping batch")

                await asyncio.sleep(0.5)  # Check every 500ms

            except Exception as e:
                self.logger.error(f"Error in batch collector: {e}")
                await asyncio.sleep(1.0)

        self.logger.debug("Batch collector stopped")

    async def _performance_monitor_loop(self):
        """Monitor system performance."""
        self.logger.debug("Starting performance monitor")

        while self.running:
            try:
                # Calculate throughput
                current_time = time.time()
                total_rollouts = self.performance_metrics['rollouts_generated']
                total_batches = self.performance_metrics['training_batches_processed']

                # Update GPU utilization (simulated)
                active_training_workers = sum(
                    1 for w in self.training_workers.values()
                    if w.status == "busy"
                )
                self.performance_metrics['gpu_utilization'] = (
                    active_training_workers / max(1, self.max_training_workers)
                )

                # Calculate throughput (rollouts per second)
                if hasattr(self, '_last_monitor_time'):
                    time_delta = current_time - self._last_monitor_time
                    rollout_delta = total_rollouts - self._last_rollout_count
                    if time_delta > 0:
                        self.performance_metrics['throughput'] = rollout_delta / time_delta

                self._last_monitor_time = current_time
                self._last_rollout_count = total_rollouts

                # Log performance every 30 seconds
                if int(current_time) % 30 == 0:
                    self._log_performance_summary()

                await asyncio.sleep(1.0)  # Monitor every second

            except Exception as e:
                self.logger.error(f"Error in performance monitor: {e}")
                await asyncio.sleep(5.0)

        self.logger.debug("Performance monitor stopped")

    async def _process_rollout_task(self, task: RolloutTask, worker_id: str) -> Dict[str, Any]:
        """Process a single rollout task."""
        experiences = []
        current_state = task.state
        steps_taken = 0

        try:
            for step in range(task.max_steps):
                # Simulate action selection (would use actual agent here)
                if not task.action_space:
                    break

                # Simple action selection for demonstration
                action = np.random.choice(task.action_space)

                # Simulate environment step
                reward = np.random.normal(0, 1)  # Random reward for demo
                next_state = f"{current_state}_step_{step}"
                done = step >= task.max_steps - 1 or reward > 2.0

                # Create experience
                experience = {
                    'state': current_state,
                    'action': action,
                    'reward': reward,
                    'next_state': next_state,
                    'done': done,
                    'step': step,
                    'rollout_id': task.task_id,
                    'worker_id': worker_id,
                    'timestamp': time.time()
                }

                experiences.append(experience)

                # Add to experience buffer for training
                with self.lock:
                    self.experience_buffer.append(experience)
                    self.performance_metrics['total_experiences'] += 1

                if done:
                    break

                current_state = next_state
                steps_taken += 1

            return {
                'task_id': task.task_id,
                'experiences': experiences,
                'steps_taken': steps_taken,
                'total_reward': sum(exp['reward'] for exp in experiences),
                'completion_time': time.time(),
                'worker_id': worker_id
            }

        except Exception as e:
            self.logger.error(f"Error processing rollout {task.task_id}: {e}")
            return {
                'task_id': task.task_id,
                'error': str(e),
                'experiences': experiences,
                'worker_id': worker_id
            }

    async def _process_training_batch(self, batch: TrainingBatch, worker_id: str):
        """Process a training batch (simplified training simulation)."""
        try:
            # Simulate training computation
            computation_time = np.random.exponential(0.5)  # Simulate variable training time
            await asyncio.sleep(computation_time)

            # Simulate model updates (in real system, this would update neural networks)
            batch_rewards = [exp.get('reward', 0.0) for exp in batch.experiences]
            avg_reward = np.mean(batch_rewards)

            # Log training progress
            self.logger.debug(
                f"Training batch {batch.batch_id} completed by {worker_id}: "
                f"avg_reward={avg_reward:.3f}, batch_size={batch.batch_size}"
            )

            # Store training metrics
            training_result = {
                'batch_id': batch.batch_id,
                'avg_reward': avg_reward,
                'batch_size': batch.batch_size,
                'training_time': computation_time,
                'worker_id': worker_id,
                'completed_at': time.time()
            }

            # In a real system, you would save model checkpoints here
            await self._save_training_checkpoint(training_result)

        except Exception as e:
            self.logger.error(f"Error processing training batch {batch.batch_id}: {e}")

    async def _save_training_checkpoint(self, training_result: Dict[str, Any]):
        """Save training checkpoint (simplified version)."""
        # In production, this would save model weights, optimizer state, etc.
        checkpoint_dir = Path("~/.torq_console/checkpoints").expanduser()
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_file = checkpoint_dir / f"checkpoint_{training_result['batch_id']}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(training_result, f, indent=2)

    def _update_avg_rollout_time(self, processing_time: float):
        """Update average rollout time with exponential moving average."""
        alpha = 0.1
        current_avg = self.performance_metrics['avg_rollout_time']
        self.performance_metrics['avg_rollout_time'] = (
            (1 - alpha) * current_avg + alpha * processing_time
        )

    def _update_avg_training_time(self, processing_time: float):
        """Update average training time with exponential moving average."""
        alpha = 0.1
        current_avg = self.performance_metrics['avg_training_time']
        self.performance_metrics['avg_training_time'] = (
            (1 - alpha) * current_avg + alpha * processing_time
        )

    def _clear_queues(self):
        """Clear all queues."""
        while not self.rollout_queue.empty():
            try:
                self.rollout_queue.get_nowait()
            except Empty:
                break

        while not self.training_queue.empty():
            try:
                self.training_queue.get_nowait()
            except Empty:
                break

        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except Empty:
                break

    def _log_performance_summary(self):
        """Log a summary of system performance."""
        metrics = self.performance_metrics
        rollout_workers_active = sum(1 for w in self.rollout_workers.values() if w.status == "busy")
        training_workers_active = sum(1 for w in self.training_workers.values() if w.status == "busy")

        self.logger.info(
            f"Async Training Performance: "
            f"rollouts={metrics['rollouts_generated']}, "
            f"batches={metrics['training_batches_processed']}, "
            f"experiences={metrics['total_experiences']}, "
            f"throughput={metrics['throughput']:.2f}/s, "
            f"gpu_util={metrics['gpu_utilization']:.1%}, "
            f"workers_active={rollout_workers_active}/{len(self.rollout_workers)}+"
            f"{training_workers_active}/{len(self.training_workers)}"
        )

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and metrics."""
        return {
            'running': self.running,
            'performance_metrics': self.performance_metrics.copy(),
            'worker_status': {
                'rollout_workers': {
                    worker_id: {
                        'status': worker.status,
                        'tasks_completed': worker.tasks_completed,
                        'avg_processing_time': (
                            worker.total_processing_time / max(1, worker.tasks_completed)
                        ),
                        'current_task': worker.current_task
                    }
                    for worker_id, worker in self.rollout_workers.items()
                },
                'training_workers': {
                    worker_id: {
                        'status': worker.status,
                        'tasks_completed': worker.tasks_completed,
                        'avg_processing_time': (
                            worker.total_processing_time / max(1, worker.tasks_completed)
                        ),
                        'current_task': worker.current_task
                    }
                    for worker_id, worker in self.training_workers.items()
                }
            },
            'queue_sizes': {
                'rollout_queue': self.rollout_queue.qsize(),
                'training_queue': self.training_queue.qsize(),
                'result_queue': self.result_queue.qsize(),
                'experience_buffer': len(self.experience_buffer)
            },
            'system_config': {
                'max_rollout_workers': self.max_rollout_workers,
                'max_training_workers': self.max_training_workers,
                'batch_size': self.batch_size,
                'max_queue_size': self.max_queue_size
            }
        }