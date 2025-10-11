"""
Image Generation Integration for TORQ Console
Handles image generation via DALL-E 3 and other AI models
"""

import os
import logging
from typing import Optional, Literal
import asyncio

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not installed. Install with: pip install openai")


class ImageGenerator:
    """Handle AI image generation."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Image Generator.

        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.logger = logging.getLogger(__name__)

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI is required. Install with: pip install openai")

        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
            self.logger.info("Image Generator initialized with DALL-E 3")
        else:
            self.client = None
            self.logger.warning("Image Generator initialized without API key")

    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key and self.client)

    async def generate(
        self,
        prompt: str,
        size: Literal["1024x1024", "1792x1024", "1024x1792"] = "1024x1024",
        quality: Literal["standard", "hd"] = "standard",
        style: Literal["vivid", "natural"] = "vivid",
        n: int = 1
    ) -> dict:
        """
        Generate image from text prompt using DALL-E 3.

        Args:
            prompt: Text description of image to generate
            size: Image dimensions (1024x1024, 1792x1024, or 1024x1792)
            quality: Image quality (standard or hd)
            style: Image style (vivid or natural)
            n: Number of images to generate (1-10)

        Returns:
            dict with 'success', 'images' (list of URLs), and optional 'error' keys
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'OpenAI API key not configured. Set OPENAI_API_KEY environment variable.'
            }

        try:
            self.logger.info(f"Generating image with prompt: {prompt[:50]}...")

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    style=style,
                    n=n,
                )
            )

            images = [img.url for img in response.data]
            revised_prompt = response.data[0].revised_prompt if response.data else None

            self.logger.info(f"Successfully generated {len(images)} image(s)")

            return {
                'success': True,
                'images': images,
                'revised_prompt': revised_prompt,
                'model': 'dall-e-3',
                'size': size,
                'quality': quality,
                'style': style,
                'prompt': prompt
            }

        except openai.OpenAIError as e:
            self.logger.error(f"OpenAI API error: {e}")
            return {
                'success': False,
                'error': f'OpenAI API error: {str(e)}'
            }
        except Exception as e:
            self.logger.error(f"Error generating image: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def generate_with_stability(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024
    ) -> dict:
        """
        Generate image using Stability AI (alternative to DALL-E).

        Note: Requires separate Stability AI API key.

        Args:
            prompt: Text description
            width: Image width
            height: Image height

        Returns:
            dict with success status and image data
        """
        # Placeholder for Stability AI integration
        # Requires: pip install stability-sdk
        return {
            'success': False,
            'error': 'Stability AI integration not yet implemented. Use DALL-E 3 for now.'
        }

    def format_response_markdown(self, result: dict) -> str:
        """
        Format image generation result as markdown for TORQ Console.

        Args:
            result: Result from generate() method

        Returns:
            Formatted markdown string
        """
        if not result.get('success'):
            return f"❌ **Error**: {result.get('error', 'Unknown error')}"

        images = result.get('images', [])
        revised_prompt = result.get('revised_prompt', '')
        original_prompt = result.get('prompt', '')

        md = "# 🎨 IMAGE GENERATED\n\n"

        # Show images
        for i, url in enumerate(images, 1):
            md += f"## Image {i}\n"
            md += f"![Generated Image {i}]({url})\n\n"
            md += f"[⬇️ Download Image {i}]({url})\n\n"

        # Show prompts
        md += "## 📝 Prompt Details\n\n"
        md += f"**Your Prompt:**\n> {original_prompt}\n\n"

        if revised_prompt and revised_prompt != original_prompt:
            md += f"**DALL-E Revised Prompt:**\n> {revised_prompt}\n\n"

        # Show metadata
        md += "## ℹ️ Generation Details\n\n"
        md += f"- **Model:** {result.get('model', 'dall-e-3')}\n"
        md += f"- **Size:** {result.get('size', '1024x1024')}\n"
        md += f"- **Quality:** {result.get('quality', 'standard')}\n"
        md += f"- **Style:** {result.get('style', 'vivid')}\n\n"

        md += "---\n"
        md += "*Generated by TORQ Console using DALL-E 3*\n"

        return md
