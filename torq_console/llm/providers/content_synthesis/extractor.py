"""
Content Extractor

Extracts structured content from web pages including:
- Tables
- Lists (ordered and unordered)
- Images with captions
- Main text content
- Metadata
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExtractedTable:
    """Represents an extracted table."""
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedList:
    """Represents an extracted list."""
    items: List[str]
    list_type: str  # 'ordered' or 'unordered'
    nested: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedImage:
    """Represents an extracted image."""
    url: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedContent:
    """Container for all extracted content."""
    title: str
    main_content: str
    author: Optional[str] = None
    date_published: Optional[str] = None
    url: str = ""

    # Structured content
    tables: List[ExtractedTable] = field(default_factory=list)
    lists: List[ExtractedList] = field(default_factory=list)
    images: List[ExtractedImage] = field(default_factory=list)

    # Additional metadata
    keywords: List[str] = field(default_factory=list)
    description: Optional[str] = None
    language: str = "en"
    word_count: int = 0

    # Extraction metadata
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    extraction_method: str = "basic"

    metadata: Dict[str, Any] = field(default_factory=dict)


class ContentExtractor:
    """
    Extract structured content from HTML or web pages.

    Features:
    - Table extraction with headers and data
    - List extraction (ordered/unordered)
    - Image extraction with metadata
    - Main content extraction
    - Metadata extraction
    """

    def __init__(self):
        """Initialize the content extractor."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("[CONTENT_EXTRACTOR] Content extractor initialized")

    def extract_from_html(self, html: str, url: str = "") -> ExtractedContent:
        """
        Extract content from HTML string.

        Args:
            html: HTML content as string
            url: Source URL (for reference)

        Returns:
            ExtractedContent object with all extracted data
        """
        try:
            # Try importing BeautifulSoup
            from bs4 import BeautifulSoup
        except ImportError:
            self.logger.warning("[CONTENT_EXTRACTOR] BeautifulSoup not available, using basic extraction")
            return self._basic_extraction(html, url)

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Extract title
            title = self._extract_title(soup)

            # Extract metadata
            author = self._extract_author(soup)
            date_published = self._extract_date(soup)
            description = self._extract_description(soup)
            keywords = self._extract_keywords(soup)
            language = self._extract_language(soup)

            # Extract main content
            main_content = self._extract_main_content(soup)

            # Extract structured content
            tables = self._extract_tables(soup)
            lists = self._extract_lists(soup)
            images = self._extract_images(soup, url)

            # Calculate word count
            word_count = len(main_content.split())

            return ExtractedContent(
                title=title,
                main_content=main_content,
                author=author,
                date_published=date_published,
                url=url,
                tables=tables,
                lists=lists,
                images=images,
                keywords=keywords,
                description=description,
                language=language,
                word_count=word_count,
                extraction_method="beautifulsoup"
            )

        except Exception as e:
            self.logger.error(f"[CONTENT_EXTRACTOR] Error extracting content: {e}")
            return self._basic_extraction(html, url)

    async def extract_from_url(self, url: str) -> ExtractedContent:
        """
        Extract content from a URL.

        Args:
            url: URL to extract content from

        Returns:
            ExtractedContent object
        """
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self.extract_from_html(html, url)
                    else:
                        self.logger.error(f"[CONTENT_EXTRACTOR] Failed to fetch URL: {response.status}")
                        return ExtractedContent(
                            title="Failed to fetch",
                            main_content="",
                            url=url,
                            extraction_method="failed"
                        )

        except Exception as e:
            self.logger.error(f"[CONTENT_EXTRACTOR] Error fetching URL: {e}")
            return ExtractedContent(
                title="Error fetching URL",
                main_content="",
                url=url,
                extraction_method="error"
            )

    def _extract_title(self, soup) -> str:
        """Extract page title."""
        # Try <title> tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        # Try <h1>
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()

        return "Untitled"

    def _extract_author(self, soup) -> Optional[str]:
        """Extract author from metadata."""
        # Try meta author tag
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta and author_meta.get('content'):
            return author_meta['content']

        # Try schema.org author
        author_schema = soup.find(attrs={'itemprop': 'author'})
        if author_schema:
            return author_schema.get_text().strip()

        return None

    def _extract_date(self, soup) -> Optional[str]:
        """Extract publication date."""
        # Try meta published_time
        date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
        if date_meta and date_meta.get('content'):
            return date_meta['content']

        # Try schema.org datePublished
        date_schema = soup.find(attrs={'itemprop': 'datePublished'})
        if date_schema and date_schema.get('content'):
            return date_schema['content']

        return None

    def _extract_description(self, soup) -> Optional[str]:
        """Extract page description."""
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta and desc_meta.get('content'):
            return desc_meta['content']

        return None

    def _extract_keywords(self, soup) -> List[str]:
        """Extract keywords."""
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta and keywords_meta.get('content'):
            return [k.strip() for k in keywords_meta['content'].split(',')]

        return []

    def _extract_language(self, soup) -> str:
        """Extract page language."""
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            return html_tag['lang']

        return "en"

    def _extract_main_content(self, soup) -> str:
        """Extract main text content."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()

        # Try to find main content area
        main = soup.find('main') or soup.find('article') or soup.find(class_=re.compile(r'content|article|post'))

        if main:
            text = main.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)

    def _extract_tables(self, soup) -> List[ExtractedTable]:
        """Extract all tables from the page."""
        tables = []

        for table_elem in soup.find_all('table'):
            try:
                # Extract caption
                caption = None
                caption_elem = table_elem.find('caption')
                if caption_elem:
                    caption = caption_elem.get_text().strip()

                # Extract headers
                headers = []
                thead = table_elem.find('thead')
                if thead:
                    header_row = thead.find('tr')
                    if header_row:
                        headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]

                # If no thead, try first row
                if not headers:
                    first_row = table_elem.find('tr')
                    if first_row:
                        headers = [th.get_text().strip() for th in first_row.find_all('th')]

                # Extract rows
                rows = []
                tbody = table_elem.find('tbody') or table_elem
                for row_elem in tbody.find_all('tr')[1 if not thead and headers else 0:]:
                    cells = [cell.get_text().strip() for cell in row_elem.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)

                if rows:  # Only add if we have data
                    tables.append(ExtractedTable(
                        headers=headers,
                        rows=rows,
                        caption=caption
                    ))

            except Exception as e:
                self.logger.warning(f"[CONTENT_EXTRACTOR] Error extracting table: {e}")
                continue

        return tables

    def _extract_lists(self, soup) -> List[ExtractedList]:
        """Extract all lists from the page."""
        lists = []

        # Extract ordered lists
        for ol_elem in soup.find_all('ol'):
            try:
                items = [li.get_text().strip() for li in ol_elem.find_all('li', recursive=False)]
                if items:
                    lists.append(ExtractedList(
                        items=items,
                        list_type='ordered',
                        nested=bool(ol_elem.find_all(['ol', 'ul']))
                    ))
            except Exception as e:
                self.logger.warning(f"[CONTENT_EXTRACTOR] Error extracting ordered list: {e}")
                continue

        # Extract unordered lists
        for ul_elem in soup.find_all('ul'):
            try:
                items = [li.get_text().strip() for li in ul_elem.find_all('li', recursive=False)]
                if items:
                    lists.append(ExtractedList(
                        items=items,
                        list_type='unordered',
                        nested=bool(ul_elem.find_all(['ol', 'ul']))
                    ))
            except Exception as e:
                self.logger.warning(f"[CONTENT_EXTRACTOR] Error extracting unordered list: {e}")
                continue

        return lists

    def _extract_images(self, soup, base_url: str) -> List[ExtractedImage]:
        """Extract all images with metadata."""
        images = []

        for img_elem in soup.find_all('img'):
            try:
                src = img_elem.get('src', '')
                if not src:
                    continue

                # Make absolute URL if needed
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/') and base_url:
                    from urllib.parse import urljoin
                    src = urljoin(base_url, src)

                # Extract metadata
                alt_text = img_elem.get('alt', '')
                width = img_elem.get('width')
                height = img_elem.get('height')

                # Try to parse dimensions
                try:
                    width = int(width) if width else None
                    height = int(height) if height else None
                except:
                    width = None
                    height = None

                # Look for caption in parent <figure>
                caption = None
                figure_parent = img_elem.find_parent('figure')
                if figure_parent:
                    figcaption = figure_parent.find('figcaption')
                    if figcaption:
                        caption = figcaption.get_text().strip()

                images.append(ExtractedImage(
                    url=src,
                    alt_text=alt_text if alt_text else None,
                    caption=caption,
                    width=width,
                    height=height
                ))

            except Exception as e:
                self.logger.warning(f"[CONTENT_EXTRACTOR] Error extracting image: {e}")
                continue

        return images

    def _basic_extraction(self, html: str, url: str) -> ExtractedContent:
        """Basic extraction without BeautifulSoup."""
        # Extract title using regex
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "Untitled"

        # Remove HTML tags for content
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()

        return ExtractedContent(
            title=title,
            main_content=text[:5000],  # Limit to first 5000 chars
            url=url,
            word_count=len(text.split()),
            extraction_method="basic"
        )
