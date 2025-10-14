"""
LinkedIn Posting Tool for Prince Flowers
Integrates LinkedIn API for posting updates
"""

import logging
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Try to import requests for API calls
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("Requests not installed. Install with: pip install requests")


class LinkedInPostingTool:
    """
    Prince Flowers tool wrapper for LinkedIn posting.

    Provides a standardized interface for posting to LinkedIn using LinkedIn API.

    Requires LinkedIn API credentials:
    - Access Token (OAuth 2.0)
    - Person/Organization URN (User ID)
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        person_urn: Optional[str] = None
    ):
        """
        Initialize the LinkedIn posting tool.

        Args:
            access_token: LinkedIn OAuth 2.0 access token
            person_urn: LinkedIn person URN (e.g., urn:li:person:ABC123)
        """
        self.logger = logging.getLogger(__name__)

        # Tool metadata for Prince's ecosystem
        self.name = "LinkedIn Posting"
        self.description = "Post updates to LinkedIn using API"
        self.cost = 0.3  # Time/resource cost for RL system
        self.success_rate = 0.80  # Historical success rate
        self.avg_time = 2.5  # Average execution time in seconds
        self.requires_approval = True  # Human approval needed for posting
        self.composable = True  # Can be composed with other tools

        # Get credentials from environment if not provided
        self.access_token = access_token or os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.person_urn = person_urn or os.getenv('LINKEDIN_PERSON_URN')

        # LinkedIn API endpoints
        self.api_base = "https://api.linkedin.com/v2"
        self.shares_endpoint = f"{self.api_base}/ugcPosts"

        # Initialize
        self.configured = False

        if REQUESTS_AVAILABLE and self._has_credentials():
            self.configured = True
            self.logger.info("LinkedIn Posting Tool initialized successfully")
        else:
            if not REQUESTS_AVAILABLE:
                self.logger.warning("Requests library not available - install with: pip install requests")
            else:
                self.logger.warning("LinkedIn API credentials not configured")

    def _has_credentials(self) -> bool:
        """Check if all required credentials are present."""
        return bool(self.access_token and self.person_urn)

    def is_available(self) -> bool:
        """Check if the tool is available and configured."""
        return REQUESTS_AVAILABLE and self.configured

    async def execute(
        self,
        text: str,
        visibility: str = "PUBLIC",
        link_url: Optional[str] = None,
        link_title: Optional[str] = None,
        link_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute LinkedIn posting.

        Args:
            text: Post text content (max 3000 characters)
            visibility: Post visibility ("PUBLIC", "CONNECTIONS", or "LOGGED_IN")
            link_url: Optional URL to share
            link_title: Optional title for shared link
            link_description: Optional description for shared link

        Returns:
            Dict containing:
                - success: bool
                - post_id: str (if successful)
                - post_url: str (if successful)
                - error: error message (if failed)
        """
        if not self.is_available():
            error_msg = "LinkedIn posting not available. "
            if not REQUESTS_AVAILABLE:
                error_msg += "Requests library not installed. Run: pip install requests"
            elif not self.configured:
                error_msg += "LinkedIn API credentials not configured. Set environment variables:\n"
                error_msg += "LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN"

            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'linkedin_posting'
            }

        try:
            # Validate text length
            if len(text) > 3000:
                return {
                    'success': False,
                    'error': f'Post text too long ({len(text)} characters). Maximum is 3000.',
                    'tool': 'linkedin_posting'
                }

            # Validate visibility
            valid_visibilities = ["PUBLIC", "CONNECTIONS", "LOGGED_IN"]
            if visibility not in valid_visibilities:
                return {
                    'success': False,
                    'error': f'Invalid visibility: {visibility}. Must be one of {valid_visibilities}',
                    'tool': 'linkedin_posting'
                }

            self.logger.info(f"Posting to LinkedIn: {text[:50]}...")

            # Build post payload
            payload = {
                "author": self.person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "ARTICLE" if link_url else "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }

            # Add link/media if provided
            if link_url:
                payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {
                        "status": "READY",
                        "originalUrl": link_url,
                        "title": {
                            "text": link_title or link_url
                        },
                        "description": {
                            "text": link_description or ""
                        }
                    }
                ]

            # Make API request
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            response = requests.post(
                self.shares_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )

            # Check response
            if response.status_code == 201:
                # Extract post ID from response
                post_id = response.headers.get('X-RestLi-Id', '')

                # Construct post URL (approximate - actual URL requires activity ID)
                post_url = f"https://www.linkedin.com/feed/update/{post_id}"

                self.logger.info(f"LinkedIn post created successfully: {post_id}")

                return {
                    'success': True,
                    'post_id': post_id,
                    'post_url': post_url,
                    'text': text,
                    'visibility': visibility,
                    'tool': 'linkedin_posting',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                error_msg = f"LinkedIn API error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'tool': 'linkedin_posting'
                }

        except requests.exceptions.Timeout:
            error_msg = "LinkedIn API request timed out"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'linkedin_posting'
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"LinkedIn API request failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'linkedin_posting'
            }

        except Exception as e:
            error_msg = f"Error posting to LinkedIn: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'linkedin_posting'
            }

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
                'text': {
                    'type': 'string',
                    'required': True,
                    'max_length': 3000,
                    'description': 'Post text content'
                },
                'visibility': {
                    'type': 'string',
                    'required': False,
                    'default': 'PUBLIC',
                    'options': ['PUBLIC', 'CONNECTIONS', 'LOGGED_IN'],
                    'description': 'Post visibility level'
                },
                'link_url': {
                    'type': 'string',
                    'required': False,
                    'description': 'URL to share in the post'
                },
                'link_title': {
                    'type': 'string',
                    'required': False,
                    'description': 'Title for shared link'
                },
                'link_description': {
                    'type': 'string',
                    'required': False,
                    'description': 'Description for shared link'
                }
            }
        }

    def format_for_prince(self, result: Dict[str, Any]) -> str:
        """
        Format result for Prince Flowers output.

        Args:
            result: Posting result dict

        Returns:
            Formatted string for Prince's response
        """
        if not result.get('success'):
            return f"❌ LinkedIn posting failed: {result.get('error', 'Unknown error')}"

        post_url = result.get('post_url', '')
        post_id = result.get('post_id', '')
        text = result.get('text', '')
        visibility = result.get('visibility', 'PUBLIC')

        response = f"✅ LinkedIn post created successfully!\n\n"
        response += f"**Post URL:** {post_url}\n"
        response += f"**Post ID:** {post_id}\n"
        response += f"**Visibility:** {visibility}\n\n"
        response += f"**Content:**\n> {text[:200]}{'...' if len(text) > 200 else ''}\n"

        return response


# Factory function for easy integration
def create_linkedin_posting_tool(
    access_token: Optional[str] = None,
    person_urn: Optional[str] = None
) -> LinkedInPostingTool:
    """
    Factory function to create LinkedIn posting tool instance.

    Args:
        access_token: Optional LinkedIn access token
        person_urn: Optional LinkedIn person URN

    Returns:
        LinkedInPostingTool instance
    """
    return LinkedInPostingTool(
        access_token=access_token,
        person_urn=person_urn
    )
