"""
Image Generation Tool for Prince Flowers
Integrates ImageGenerator into Prince's tool ecosystem
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

# Import the existing ImageGenerator
try:
    from torq_console.integrations.image_generation import ImageGenerator
    IMAGE_GEN_AVAILABLE = True
except ImportError:
    IMAGE_GEN_AVAILABLE = False
    logging.warning("ImageGenerator not available")


class ImageGenerationTool:
    """
    Prince Flowers tool wrapper for image generation.

    Provides a standardized interface for Prince to generate images using DALL-E 3.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the image generation tool.

        Args:
            api_key: OpenAI API key (optional, will use env var if not provided)
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key

        # Tool metadata for Prince's ecosystem
        self.name = "Image Generation"
        self.description = "Generate images from text descriptions using DALL-E 3"
        self.cost = 0.4  # Time/resource cost for RL system
        self.success_rate = 0.90  # Historical success rate
        self.avg_time = 3.0  # Average execution time in seconds
        self.requires_approval = False  # No human approval needed
        self.composable = True  # Can be composed with other tools

        # Initialize the underlying generator
        if IMAGE_GEN_AVAILABLE:
            try:
                self.generator = ImageGenerator(api_key=api_key)
                self.configured = self.generator.is_configured()
                if self.configured:
                    self.logger.info("Image Generation Tool initialized successfully")
                else:
                    self.logger.warning("Image Generation Tool initialized but API key not configured")
            except Exception as e:
                self.logger.error(f"Failed to initialize ImageGenerator: {e}")
                self.generator = None
                self.configured = False
        else:
            self.generator = None
            self.configured = False
            self.logger.error("ImageGenerator not available - install openai package")

    def is_available(self) -> bool:
        """Check if the tool is available and configured."""
        return IMAGE_GEN_AVAILABLE and self.configured

    async def execute(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        n: int = 1,
        save_to_file: bool = False,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute image generation.

        Args:
            prompt: Text description of the image to generate
            size: Image size (1024x1024, 1792x1024, or 1024x1792)
            quality: Image quality (standard or hd)
            style: Image style (vivid or natural)
            n: Number of images to generate (1-10)
            save_to_file: Whether to save image URLs to a file
            output_dir: Directory to save the file (defaults to E:\TORQ-CONSOLE\outputs)

        Returns:
            Dict containing:
                - success: bool
                - images: list of image URLs
                - revised_prompt: DALL-E's revised prompt
                - error: error message (if failed)
                - output_file: path to saved file (if save_to_file=True)
        """
        if not self.is_available():
            error_msg = "Image generation not available. "
            if not IMAGE_GEN_AVAILABLE:
                error_msg += "OpenAI package not installed. Run: pip install openai"
            elif not self.configured:
                error_msg += "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."

            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'image_generation'
            }

        try:
            self.logger.info(f"Generating image with prompt: {prompt[:100]}...")

            # Generate the image
            result = await self.generator.generate(
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=n
            )

            # Add tool metadata
            result['tool'] = 'image_generation'
            result['execution_time'] = self.avg_time  # Placeholder for actual timing

            # Save to file if requested
            if result.get('success') and save_to_file:
                output_path = self._save_result_to_file(result, output_dir)
                result['output_file'] = output_path
                self.logger.info(f"Image generation result saved to: {output_path}")

            if result.get('success'):
                self.logger.info(f"Successfully generated {len(result.get('images', []))} image(s)")
            else:
                self.logger.error(f"Image generation failed: {result.get('error')}")

            return result

        except Exception as e:
            error_msg = f"Error executing image generation: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'image_generation'
            }

    def _save_result_to_file(self, result: Dict[str, Any], output_dir: Optional[str] = None) -> str:
        """
        Save image generation result to a file.

        Args:
            result: Generation result dict
            output_dir: Output directory (defaults to E:\TORQ-CONSOLE\outputs)

        Returns:
            Path to saved file
        """
        # Determine output directory
        if output_dir is None:
            output_dir = Path("E:\\TORQ-CONSOLE\\outputs")
        else:
            output_dir = Path(output_dir)

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"image_gen_{timestamp}.md"

        # Format as markdown
        content = self.generator.format_response_markdown(result)

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_file)

    def get_tool_info(self) -> Dict[str, Any]:
        """
        Get tool information for Prince's tool registry.

        Returns:
            Dict containing tool metadata
        """
        return {
            'name': self.name,
            'description': self.description,
            'cost': self.cost,
            'success_rate': self.success_rate,
            'avg_time': self.avg_time,
            'requires_approval': self.requires_approval,
            'composable': self.composable,
            'available': self.is_available(),
            'dependencies': [],
            'parameters': {
                'prompt': {
                    'type': 'string',
                    'required': True,
                    'description': 'Text description of the image'
                },
                'size': {
                    'type': 'string',
                    'required': False,
                    'default': '1024x1024',
                    'options': ['1024x1024', '1792x1024', '1024x1792'],
                    'description': 'Image dimensions'
                },
                'quality': {
                    'type': 'string',
                    'required': False,
                    'default': 'standard',
                    'options': ['standard', 'hd'],
                    'description': 'Image quality level'
                },
                'style': {
                    'type': 'string',
                    'required': False,
                    'default': 'vivid',
                    'options': ['vivid', 'natural'],
                    'description': 'Image style preference'
                },
                'n': {
                    'type': 'integer',
                    'required': False,
                    'default': 1,
                    'min': 1,
                    'max': 10,
                    'description': 'Number of images to generate'
                }
            }
        }

    def format_for_prince(self, result: Dict[str, Any]) -> str:
        """
        Format result for Prince Flowers output.

        Args:
            result: Generation result dict

        Returns:
            Formatted string for Prince's response
        """
        if not result.get('success'):
            return f"❌ Image generation failed: {result.get('error', 'Unknown error')}"

        images = result.get('images', [])
        revised_prompt = result.get('revised_prompt', '')
        output_file = result.get('output_file', '')

        response = f"✅ Generated {len(images)} image(s)\n\n"

        # Add image URLs
        for i, url in enumerate(images, 1):
            response += f"Image {i}: {url}\n"

        # Add revised prompt if different
        if revised_prompt:
            response += f"\n📝 Revised Prompt: {revised_prompt}\n"

        # Add output file if saved
        if output_file:
            response += f"\n💾 Saved to: {output_file}\n"

        return response


# Factory function for easy integration
def create_image_generation_tool(api_key: Optional[str] = None) -> ImageGenerationTool:
    """
    Factory function to create image generation tool instance.

    Args:
        api_key: Optional OpenAI API key

    Returns:
        ImageGenerationTool instance
    """
    return ImageGenerationTool(api_key=api_key)
