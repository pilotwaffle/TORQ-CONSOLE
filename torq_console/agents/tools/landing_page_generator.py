"""
Landing Page Generator Tool for Prince Flowers
Creates professional landing pages from text descriptions
"""
import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


class LandingPageGenerator:
    """
    Landing Page Generator using template-based approach with AI customization.
    Creates responsive, professional landing pages from text descriptions.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize Landing Page Generator.

        Args:
            output_dir: Directory to save generated pages (default: E:/generated_pages)
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir or "E:/generated_pages")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Template categories
        self.templates = {
            'startup': self._generate_startup_template,
            'saas': self._generate_saas_template,
            'portfolio': self._generate_portfolio_template,
            'product': self._generate_product_template,
            'event': self._generate_event_template,
            'minimal': self._generate_minimal_template
        }

    def is_available(self) -> bool:
        """Check if landing page generation is available."""
        try:
            # Check if output directory is writable
            test_file = self.output_dir / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            return True
        except Exception as e:
            self.logger.error(f"Landing page generation not available: {e}")
            return False

    def generate(
        self,
        description: str,
        template: str = 'minimal',
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        features: Optional[List[str]] = None,
        cta_text: str = "Get Started",
        cta_link: str = "#",
        colors: Optional[Dict[str, str]] = None,
        images: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a landing page from description.

        Args:
            description: Text description of the landing page purpose
            template: Template type (startup, saas, portfolio, product, event, minimal)
            title: Page title (auto-generated if not provided)
            subtitle: Page subtitle
            features: List of features to highlight
            cta_text: Call-to-action button text
            cta_link: Call-to-action button link
            colors: Custom color scheme {primary, secondary, accent, bg, text}
            images: Custom images {hero, logo, feature1, feature2, feature3}
            **kwargs: Additional template-specific parameters

        Returns:
            Dict with success status, file paths, and metadata
        """
        try:
            self.logger.info(f"[LANDING_PAGE] Generating {template} template")
            self.logger.info(f"[LANDING_PAGE] Description: {description[:100]}...")

            # Auto-generate title if not provided
            if not title:
                title = self._extract_title(description)

            # Auto-generate subtitle if not provided
            if not subtitle:
                subtitle = self._extract_subtitle(description)

            # Default color scheme (modern dark theme)
            default_colors = {
                'primary': '#6366f1',    # Indigo
                'secondary': '#8b5cf6',  # Purple
                'accent': '#ec4899',     # Pink
                'bg': '#0f172a',         # Dark slate
                'text': '#f1f5f9'        # Light slate
            }
            colors = {**default_colors, **(colors or {})}

            # Default placeholder images
            default_images = {
                'hero': 'https://images.unsplash.com/photo-1557821552-17105176677c?w=1200&h=600&fit=crop',
                'logo': 'https://via.placeholder.com/120x60/6366f1/ffffff?text=Logo',
                'feature1': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=300&fit=crop',
                'feature2': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&h=300&fit=crop',
                'feature3': 'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=400&h=300&fit=crop'
            }
            images = {**default_images, **(images or {})}

            # Get template generator
            template_func = self.templates.get(template, self._generate_minimal_template)

            # Generate HTML
            html_content = template_func(
                title=title,
                subtitle=subtitle,
                description=description,
                features=features or [],
                cta_text=cta_text,
                cta_link=cta_link,
                colors=colors,
                images=images,
                **kwargs
            )

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
            safe_title = safe_title.replace(' ', '_').lower()[:50]
            filename = f"{safe_title}_{timestamp}.html"
            filepath = self.output_dir / filename

            # Save HTML file
            filepath.write_text(html_content, encoding='utf-8')

            # Create metadata file
            metadata = {
                'title': title,
                'subtitle': subtitle,
                'description': description,
                'template': template,
                'generated_at': datetime.now().isoformat(),
                'filepath': str(filepath),
                'file_size': filepath.stat().st_size
            }

            metadata_path = self.output_dir / f"{safe_title}_{timestamp}_metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

            self.logger.info(f"[LANDING_PAGE] ✓ Generated: {filepath}")
            self.logger.info(f"[LANDING_PAGE] File size: {metadata['file_size']} bytes")

            return {
                'success': True,
                'filepath': str(filepath),
                'file_size': metadata['file_size'],
                'url': f"file:///{filepath}",
                'metadata': metadata,
                'template': template,
                'title': title
            }

        except Exception as e:
            error_msg = f"Landing page generation failed: {str(e)}"
            self.logger.error(f"[LANDING_PAGE] ✗ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def _extract_title(self, description: str) -> str:
        """Extract or generate title from description."""
        # Simple extraction: first sentence or first 50 characters
        sentences = description.split('.')
        title = sentences[0].strip() if sentences else description
        return title[:60] + ('...' if len(title) > 60 else '')

    def _extract_subtitle(self, description: str) -> str:
        """Extract or generate subtitle from description."""
        sentences = description.split('.')
        if len(sentences) > 1:
            return sentences[1].strip()[:100]
        return "Transform your vision into reality"

    def _generate_minimal_template(
        self,
        title: str,
        subtitle: str,
        description: str,
        features: List[str],
        cta_text: str,
        cta_link: str,
        colors: Dict[str, str],
        images: Dict[str, str],
        **kwargs
    ) -> str:
        """Generate a minimal, modern landing page."""
        features_html = "\n".join([
            f"""
            <div class="feature">
                <h3>{feature}</h3>
            </div>
            """ for feature in features
        ]) if features else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: {colors['bg']};
            color: {colors['text']};
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        header {{
            padding: 20px 0;
            background: rgba(255, 255, 255, 0.05);
        }}

        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: {colors['primary']};
        }}

        .hero {{
            padding: 100px 0;
            text-align: center;
        }}

        h1 {{
            font-size: 3rem;
            margin-bottom: 20px;
            background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .subtitle {{
            font-size: 1.5rem;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 30px;
        }}

        .description {{
            font-size: 1.1rem;
            max-width: 700px;
            margin: 0 auto 40px;
            color: rgba(255, 255, 255, 0.8);
        }}

        .cta-button {{
            display: inline-block;
            padding: 15px 40px;
            background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .cta-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
        }}

        .features {{
            padding: 80px 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
        }}

        .feature {{
            background: rgba(255, 255, 255, 0.05);
            padding: 30px;
            border-radius: 10px;
            transition: transform 0.3s ease;
        }}

        .feature:hover {{
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.08);
        }}

        .feature h3 {{
            color: {colors['primary']};
            margin-bottom: 10px;
        }}

        footer {{
            padding: 40px 0;
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.5);
        }}

        @media (max-width: 768px) {{
            h1 {{
                font-size: 2rem;
            }}
            .subtitle {{
                font-size: 1.2rem;
            }}
            .hero {{
                padding: 60px 0;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="logo">{title.split()[0] if title else 'Logo'}</div>
        </div>
    </header>

    <main>
        <section class="hero">
            <div class="container">
                <h1>{title}</h1>
                <p class="subtitle">{subtitle}</p>
                <p class="description">{description}</p>
                <a href="{cta_link}" class="cta-button">{cta_text}</a>
            </div>
        </section>

        {f'<section class="features"><div class="container">{features_html}</div></section>' if features else ''}
    </main>

    <footer>
        <div class="container">
            <p>&copy; {datetime.now().year} {title}. Generated by Prince Flowers AI.</p>
        </div>
    </footer>
</body>
</html>"""

    def _generate_startup_template(self, **kwargs) -> str:
        """Generate a startup-focused landing page."""
        # For brevity, this would implement a more elaborate startup template
        # For now, use the minimal template as base
        return self._generate_minimal_template(**kwargs)

    def _generate_saas_template(self, **kwargs) -> str:
        """Generate a SaaS product landing page."""
        return self._generate_minimal_template(**kwargs)

    def _generate_portfolio_template(self, **kwargs) -> str:
        """Generate a portfolio landing page."""
        return self._generate_minimal_template(**kwargs)

    def _generate_product_template(self, **kwargs) -> str:
        """Generate a product showcase landing page."""
        return self._generate_minimal_template(**kwargs)

    def _generate_event_template(self, **kwargs) -> str:
        """Generate an event landing page."""
        return self._generate_minimal_template(**kwargs)


def create_landing_page_generator(output_dir: Optional[str] = None) -> 'LandingPageGeneratorTool':
    """
    Factory function to create a LandingPageGeneratorTool instance.

    Args:
        output_dir: Optional custom output directory

    Returns:
        LandingPageGeneratorTool instance
    """
    return LandingPageGeneratorTool(output_dir=output_dir)


class LandingPageGeneratorTool:
    """Tool wrapper for landing page generation for Prince Flowers."""

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the landing page generator tool."""
        self.generator = LandingPageGenerator(output_dir=output_dir)
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Check if tool is available."""
        return self.generator.is_available()

    async def execute(
        self,
        description: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute landing page generation asynchronously.

        Args:
            description: Landing page description
            **kwargs: Additional generation parameters

        Returns:
            Generation result with file paths and metadata
        """
        # Run synchronously (no actual async API calls needed for local generation)
        return self.generator.generate(description=description, **kwargs)
