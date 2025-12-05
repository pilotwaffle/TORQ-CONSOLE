"""
Web Tools for TORQ Console - Claude Code Compatible WebFetch.

Advanced web content fetching and AI-enhanced processing for Claude Code compatibility.
Includes smart content extraction, summarization, and multi-format output.
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import hashlib

import httpx
from bs4 import BeautifulSoup


@dataclass
class WebContent:
    """Represents processed web content."""
    url: str
    title: str = ""
    content: str = ""
    markdown: str = ""
    summary: str = ""
    metadata: Dict[str, Any] = None
    processing_time: float = 0.0
    content_type: str = ""
    status_code: int = 0
    redirect_url: Optional[str] = None


class WebFetchTool:
    """
    Advanced web content fetching tool with AI-enhanced processing.

    Features:
    - Smart content extraction from HTML/PDF
    - AI-powered content summarization
    - Multi-format output (text, markdown, structured data)
    - Content caching and optimization
    - Claude Code WebFetch tool compatibility
    """

    def __init__(self, llm_provider=None):
        self.logger = logging.getLogger(__name__)
        self.llm_provider = llm_provider

        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'TORQ-Console-WebFetch/1.0 (Compatible with Claude Code)'
            }
        )

        # Content processing configuration
        self.max_content_length = 1_000_000  # 1MB max content
        self.cache_duration = timedelta(minutes=15)  # 15-minute cache
        self.content_cache = {}

        # AI processing configuration
        self.enable_ai_summarization = True
        self.summary_max_length = 500

    async def fetch_and_process(
        self,
        url: str,
        prompt: str,
        format_output: str = "markdown",
        enable_ai_processing: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch URL content and process it with AI.

        Args:
            url: URL to fetch content from
            prompt: Processing prompt for AI analysis
            format_output: Output format (text, markdown, structured)
            enable_ai_processing: Whether to use AI for content processing

        Returns:
            Dict with processed content and metadata
        """
        start_time = time.time()

        try:
            # Check cache first
            cache_key = self._get_cache_key(url, prompt)
            cached_result = self._get_cached_result(cache_key)

            if cached_result:
                cached_result['from_cache'] = True
                return cached_result

            # Fetch content
            web_content = await self._fetch_content(url)

            if not web_content:
                return {
                    'success': False,
                    'error': 'Failed to fetch content',
                    'url': url
                }

            # Process content based on format
            processed_content = await self._process_content(
                web_content,
                prompt,
                format_output,
                enable_ai_processing
            )

            # Calculate total processing time
            processing_time = time.time() - start_time

            result = {
                'success': True,
                'url': url,
                'redirect_url': web_content.redirect_url,
                'title': web_content.title,
                'content': processed_content,
                'metadata': {
                    'content_type': web_content.content_type,
                    'status_code': web_content.status_code,
                    'processing_time_ms': round(processing_time * 1000, 2),
                    'content_length': len(web_content.content),
                    'format': format_output,
                    'ai_processed': enable_ai_processing
                },
                'from_cache': False
            }

            # Cache the result
            self._cache_result(cache_key, result)

            return result

        except Exception as e:
            self.logger.error(f"WebFetch error for {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'processing_time_ms': round((time.time() - start_time) * 1000, 2)
            }

    async def _fetch_content(self, url: str) -> Optional[WebContent]:
        """Fetch raw content from URL."""
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Fetch content
            response = await self.client.get(url)
            response.raise_for_status()

            # Check content length
            content_length = len(response.content)
            if content_length > self.max_content_length:
                self.logger.warning(f"Content too large ({content_length} bytes), truncating")
                content = response.content[:self.max_content_length]
            else:
                content = response.content

            # Create WebContent object
            web_content = WebContent(
                url=str(response.url),
                content_type=response.headers.get('content-type', ''),
                status_code=response.status_code,
                redirect_url=str(response.url) if str(response.url) != url else None
            )

            # Process based on content type
            if 'text/html' in web_content.content_type:
                await self._process_html_content(web_content, content.decode('utf-8', errors='ignore'))
            elif 'application/pdf' in web_content.content_type:
                await self._process_pdf_content(web_content, content)
            else:
                # Plain text or other
                web_content.content = content.decode('utf-8', errors='ignore')
                web_content.title = urlparse(url).path.split('/')[-1] or url

            return web_content

        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    async def _process_html_content(self, web_content: WebContent, html: str):
        """Process HTML content and extract meaningful text."""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Extract title
            title_tag = soup.find('title')
            web_content.title = title_tag.get_text().strip() if title_tag else ""

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()

            # Extract main content
            # Try to find main content areas first
            main_content = None
            for selector in ['main', 'article', '.content', '#content', '.post', '.entry']:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if not main_content:
                main_content = soup.find('body') or soup

            # Extract text
            text_content = main_content.get_text()

            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)

            web_content.content = clean_text

            # Create markdown version
            web_content.markdown = await self._html_to_markdown(main_content)

        except Exception as e:
            self.logger.error(f"HTML processing error: {e}")
            web_content.content = html[:10000]  # Fallback to raw HTML (truncated)

    async def _html_to_markdown(self, soup) -> str:
        """Convert HTML soup to markdown format."""
        markdown_lines = []

        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(element.name[1])
            markdown_lines.append('#' * level + ' ' + element.get_text().strip())

        for element in soup.find_all('p'):
            text = element.get_text().strip()
            if text:
                markdown_lines.append(text)

        for element in soup.find_all(['ul', 'ol']):
            for li in element.find_all('li'):
                text = li.get_text().strip()
                if text:
                    prefix = '- ' if element.name == 'ul' else '1. '
                    markdown_lines.append(prefix + text)

        for element in soup.find_all('a'):
            text = element.get_text().strip()
            href = element.get('href', '')
            if text and href:
                markdown_lines.append(f'[{text}]({href})')

        return '\\n\\n'.join(markdown_lines)

    async def _process_pdf_content(self, web_content: WebContent, content: bytes):
        """Process PDF content (basic implementation - would need PyPDF2 for full support)."""
        try:
            # For now, just indicate PDF was detected
            web_content.content = "[PDF Content Detected - Full PDF processing requires additional dependencies]"
            web_content.title = "PDF Document"

            # In a full implementation, would use PyPDF2 or similar:
            # import PyPDF2
            # pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            # text = ""
            # for page in pdf_reader.pages:
            #     text += page.extract_text()
            # web_content.content = text

        except Exception as e:
            self.logger.error(f"PDF processing error: {e}")
            web_content.content = "[PDF processing failed]"

    async def _process_content(
        self,
        web_content: WebContent,
        prompt: str,
        format_output: str,
        enable_ai_processing: bool
    ) -> str:
        """Process content according to specified format and AI requirements."""

        if format_output == "raw":
            return web_content.content

        elif format_output == "markdown":
            content = web_content.markdown if web_content.markdown else web_content.content

        else:  # text format
            content = web_content.content

        # Apply AI processing if enabled and LLM provider available
        if enable_ai_processing and self.llm_provider and prompt:
            try:
                ai_processed = await self._ai_process_content(content, prompt)
                if ai_processed:
                    return ai_processed
            except Exception as e:
                self.logger.warning(f"AI processing failed, using raw content: {e}")

        # Fallback: apply basic processing based on prompt
        if prompt and "summarize" in prompt.lower():
            return self._basic_summarize(content)
        elif prompt and "extract" in prompt.lower():
            return self._basic_extract(content, prompt)

        return content

    async def _ai_process_content(self, content: str, prompt: str) -> Optional[str]:
        """Process content using AI/LLM."""
        if not self.llm_provider:
            return None

        try:
            # Truncate content if too long for AI processing
            max_ai_content = 8000
            if len(content) > max_ai_content:
                content = content[:max_ai_content] + "\\n\\n[Content truncated for AI processing...]"

            processing_prompt = f"""
Please process the following web content according to this request: {prompt}

Web Content:
{content}

Please provide a clear, structured response that addresses the request.
"""

            # Call LLM provider (this would depend on the specific provider interface)
            response = await self.llm_provider.generate_response(processing_prompt)

            return response.get('content', '') if response else None

        except Exception as e:
            self.logger.error(f"AI processing error: {e}")
            return None

    def _basic_summarize(self, content: str, max_sentences: int = 3) -> str:
        """Basic summarization using simple heuristics."""
        sentences = re.split(r'[.!?]+', content)

        # Remove very short sentences
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        # Take first few meaningful sentences
        if len(meaningful_sentences) <= max_sentences:
            return '. '.join(meaningful_sentences) + '.'

        return '. '.join(meaningful_sentences[:max_sentences]) + '.'

    def _basic_extract(self, content: str, prompt: str) -> str:
        """Basic extraction based on keywords in prompt."""
        extract_keywords = re.findall(r'"([^"]*)"', prompt)  # Extract quoted terms

        if not extract_keywords:
            # Look for common extraction patterns
            if 'email' in prompt.lower():
                emails = re.findall(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', content)
                return '\\n'.join(emails) if emails else "No email addresses found."

            elif 'phone' in prompt.lower():
                phones = re.findall(r'\\b(?:\\+?1[-.]?)?\\(?\\d{3}\\)?[-.]?\\d{3}[-.]?\\d{4}\\b', content)
                return '\\n'.join(phones) if phones else "No phone numbers found."

        # Return content containing keywords
        lines = content.split('\\n')
        relevant_lines = []

        for line in lines:
            if any(keyword.lower() in line.lower() for keyword in extract_keywords):
                relevant_lines.append(line.strip())

        return '\\n'.join(relevant_lines) if relevant_lines else content[:500] + "..."

    def _get_cache_key(self, url: str, prompt: str) -> str:
        """Generate cache key for URL and prompt combination."""
        """Generate unique cache key for request."""
        # Use MD5 for cache key generation only (not for security)
        content = f"{url}|{prompt}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if still valid."""
        if cache_key not in self.content_cache:
            return None

        cached_entry = self.content_cache[cache_key]
        cache_time = cached_entry.get('cached_at')

        if not cache_time or datetime.now() - cache_time > self.cache_duration:
            del self.content_cache[cache_key]
            return None

        return cached_entry['result']

    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache processing result."""
        self.content_cache[cache_key] = {
            'result': result,
            'cached_at': datetime.now()
        }

        # Clean old cache entries
        self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove expired cache entries."""
        cutoff_time = datetime.now() - self.cache_duration
        expired_keys = []

        for key, entry in self.content_cache.items():
            if entry.get('cached_at', datetime.min) < cutoff_time:
                expired_keys.append(key)

        for key in expired_keys:
            del self.content_cache[key]

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


# Export web fetch tool
web_fetch_tool = WebFetchTool()

async def web_fetch(url: str, prompt: str, **kwargs) -> Dict[str, Any]:
    """
    Claude Code compatible WebFetch function.

    Args:
        url: URL to fetch and process
        prompt: Processing instruction for the content
        **kwargs: Additional options (format, ai_processing, etc.)

    Returns:
        Processed content result
    """
    return await web_fetch_tool.fetch_and_process(url, prompt, **kwargs)