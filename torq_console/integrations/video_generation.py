"""
Video Generation Integration for TORQ Console
Handles video generation via RunwayML Gen-3 and other AI video models
"""

import os
import logging
from typing import Optional, Literal
import asyncio
import aiohttp


class VideoGenerator:
    """Handle AI video generation using RunwayML."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Video Generator.

        Args:
            api_key: RunwayML API key
        """
        self.api_key = api_key or os.getenv('RUNWAYML_API_KEY')
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.runwayml.com/v1"

        if self.api_key:
            self.logger.info("Video Generator initialized with RunwayML Gen-3")
        else:
            self.logger.warning("Video Generator initialized without API key")

    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        ratio: Literal["16:9", "9:16", "1:1"] = "16:9",
        model: str = "gen3a_turbo"
    ) -> dict:
        """
        Generate video from text prompt using RunwayML Gen-3.

        Args:
            prompt: Text description of video to generate
            duration: Video duration in seconds (5-10)
            ratio: Aspect ratio (16:9, 9:16, or 1:1)
            model: Model to use (gen3a_turbo recommended)

        Returns:
            dict with 'success', 'video_url', 'task_id', and optional 'error' keys
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'RunwayML API key not configured. Set RUNWAYML_API_KEY environment variable.'
            }

        try:
            self.logger.info(f"Generating video with prompt: {prompt[:50]}...")

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'promptText': prompt,
                'model': model,
                'duration': duration,
                'ratio': ratio,
                'watermark': False  # Remove watermark if plan allows
            }

            async with aiohttp.ClientSession() as session:
                # Initiate video generation
                async with session.post(
                    f'{self.base_url}/generate',
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f'RunwayML API error ({response.status}): {error_text}'
                        }

                    result = await response.json()
                    task_id = result.get('id')

                    if not task_id:
                        return {
                            'success': False,
                            'error': 'No task ID returned from RunwayML'
                        }

                    self.logger.info(f"Video generation started. Task ID: {task_id}")

                    # Poll for completion
                    video_url = await self._poll_for_completion(task_id, headers, session)

                    if video_url:
                        return {
                            'success': True,
                            'video_url': video_url,
                            'task_id': task_id,
                            'model': model,
                            'duration': duration,
                            'ratio': ratio,
                            'prompt': prompt
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Video generation timed out or failed',
                            'task_id': task_id
                        }

        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP error generating video: {e}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def generate_image_to_video(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        duration: int = 5,
        ratio: Literal["16:9", "9:16", "1:1"] = "16:9"
    ) -> dict:
        """
        Generate video from image using RunwayML.

        Args:
            image_url: URL of source image
            prompt: Optional text prompt for motion
            duration: Video duration in seconds
            ratio: Aspect ratio

        Returns:
            dict with success status and video data
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'RunwayML API key not configured'
            }

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'promptImage': image_url,
                'model': 'gen3a_turbo',
                'duration': duration,
                'ratio': ratio,
                'watermark': False
            }

            if prompt:
                payload['promptText'] = prompt

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/generate',
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f'RunwayML API error: {error_text}'
                        }

                    result = await response.json()
                    task_id = result.get('id')

                    video_url = await self._poll_for_completion(task_id, headers, session)

                    if video_url:
                        return {
                            'success': True,
                            'video_url': video_url,
                            'task_id': task_id,
                            'source_image': image_url
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Video generation failed or timed out'
                        }

        except Exception as e:
            self.logger.error(f"Error in image-to-video: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _poll_for_completion(
        self,
        task_id: str,
        headers: dict,
        session: aiohttp.ClientSession,
        max_attempts: int = 60,
        poll_interval: int = 5
    ) -> Optional[str]:
        """
        Poll RunwayML API for video generation completion.

        Args:
            task_id: Generation task ID
            headers: Request headers
            session: aiohttp session
            max_attempts: Maximum polling attempts
            poll_interval: Seconds between polls

        Returns:
            Video URL if successful, None otherwise
        """
        for attempt in range(max_attempts):
            await asyncio.sleep(poll_interval)

            try:
                async with session.get(
                    f'{self.base_url}/tasks/{task_id}',
                    headers=headers
                ) as response:
                    if response.status != 200:
                        self.logger.warning(f"Poll attempt {attempt + 1} failed")
                        continue

                    data = await response.json()
                    status = data.get('status')

                    if status == 'SUCCEEDED':
                        video_url = data.get('output', [None])[0]
                        self.logger.info(f"Video generation completed! URL: {video_url}")
                        return video_url
                    elif status in ['FAILED', 'CANCELLED']:
                        self.logger.error(f"Video generation {status.lower()}")
                        return None
                    else:
                        # Still processing
                        progress = data.get('progress', 0)
                        self.logger.info(f"Video generation in progress: {progress}%")

            except Exception as e:
                self.logger.error(f"Error polling task status: {e}")
                continue

        self.logger.error("Video generation timed out after maximum attempts")
        return None

    async def get_task_status(self, task_id: str) -> dict:
        """
        Get status of a video generation task.

        Args:
            task_id: Task ID to check

        Returns:
            dict with task status information
        """
        if not self.is_configured():
            return {'error': 'Not configured'}

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.base_url}/tasks/{task_id}',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            'error': f'Status check failed: {response.status}'
                        }

        except Exception as e:
            self.logger.error(f"Error checking task status: {e}")
            return {'error': str(e)}

    def format_response_markdown(self, result: dict) -> str:
        """
        Format video generation result as markdown for TORQ Console.

        Args:
            result: Result from generate methods

        Returns:
            Formatted markdown string
        """
        if not result.get('success'):
            return f"❌ **Error**: {result.get('error', 'Unknown error')}"

        video_url = result.get('video_url')
        prompt = result.get('prompt', 'N/A')
        task_id = result.get('task_id', 'N/A')

        md = "# 🎬 VIDEO GENERATED\n\n"

        # Embed video player
        md += "## Video Preview\n\n"
        md += f'<video controls width="100%" style="max-width: 800px;">\n'
        md += f'  <source src="{video_url}" type="video/mp4">\n'
        md += f'  Your browser does not support video playback.\n'
        md += f'</video>\n\n'

        md += f"[⬇️ Download Video]({video_url})\n\n"

        # Show prompt
        md += "## 📝 Generation Details\n\n"
        md += f"**Prompt:**\n> {prompt}\n\n"

        # Show metadata
        md += "## ℹ️ Technical Information\n\n"
        md += f"- **Model:** {result.get('model', 'gen3a_turbo')}\n"
        md += f"- **Duration:** {result.get('duration', 5)} seconds\n"
        md += f"- **Aspect Ratio:** {result.get('ratio', '16:9')}\n"
        md += f"- **Task ID:** `{task_id}`\n\n"

        md += "---\n"
        md += "*Generated by TORQ Console using RunwayML Gen-3*\n"

        return md
