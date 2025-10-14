"""
Twitter/X Posting Tool for Prince Flowers
Integrates Twitter API v2 for posting tweets
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Try to import tweepy (Twitter API library)
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    logging.warning("Tweepy not installed. Install with: pip install tweepy")


class TwitterPostingTool:
    """
    Prince Flowers tool wrapper for Twitter/X posting.

    Provides a standardized interface for posting tweets using Twitter API v2.

    Requires Twitter API credentials:
    - API Key (Consumer Key)
    - API Secret (Consumer Secret)
    - Access Token
    - Access Token Secret
    - Bearer Token (for v2 API)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None
    ):
        """
        Initialize the Twitter posting tool.

        Args:
            api_key: Twitter API Key (Consumer Key)
            api_secret: Twitter API Secret (Consumer Secret)
            access_token: Twitter Access Token
            access_token_secret: Twitter Access Token Secret
            bearer_token: Twitter Bearer Token (for v2 API)
        """
        self.logger = logging.getLogger(__name__)

        # Tool metadata for Prince's ecosystem
        self.name = "Twitter Posting"
        self.description = "Post tweets to Twitter/X using API v2"
        self.cost = 0.3  # Time/resource cost for RL system
        self.success_rate = 0.85  # Historical success rate
        self.avg_time = 2.0  # Average execution time in seconds
        self.requires_approval = True  # Human approval needed for posting
        self.composable = True  # Can be composed with other tools

        # Get credentials from environment if not provided
        self.api_key = api_key or os.getenv('TWITTER_API_KEY')
        self.api_secret = api_secret or os.getenv('TWITTER_API_SECRET')
        self.access_token = access_token or os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = access_token_secret or os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN')

        # Initialize Twitter API client
        self.client = None
        self.api = None
        self.configured = False

        if TWEEPY_AVAILABLE and self._has_credentials():
            try:
                # Initialize Twitter API v2 client
                self.client = tweepy.Client(
                    bearer_token=self.bearer_token,
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                    wait_on_rate_limit=True
                )

                # Also initialize v1.1 API for media upload (if needed)
                auth = tweepy.OAuth1UserHandler(
                    self.api_key,
                    self.api_secret,
                    self.access_token,
                    self.access_token_secret
                )
                self.api = tweepy.API(auth, wait_on_rate_limit=True)

                self.configured = True
                self.logger.info("Twitter Posting Tool initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Twitter API: {e}")
                self.configured = False
        else:
            if not TWEEPY_AVAILABLE:
                self.logger.warning("Tweepy not available - install with: pip install tweepy")
            else:
                self.logger.warning("Twitter API credentials not configured")

    def _has_credentials(self) -> bool:
        """Check if all required credentials are present."""
        return all([
            self.api_key,
            self.api_secret,
            self.access_token,
            self.access_token_secret,
            self.bearer_token
        ])

    def is_available(self) -> bool:
        """Check if the tool is available and configured."""
        return TWEEPY_AVAILABLE and self.configured

    async def execute(
        self,
        text: str,
        reply_to_id: Optional[str] = None,
        media_urls: Optional[List[str]] = None,
        poll_options: Optional[List[str]] = None,
        poll_duration_minutes: int = 1440  # 24 hours default
    ) -> Dict[str, Any]:
        """
        Execute Twitter posting.

        Args:
            text: Tweet text (max 280 characters)
            reply_to_id: Optional tweet ID to reply to
            media_urls: Optional list of media URLs to attach
            poll_options: Optional list of poll options (2-4 options)
            poll_duration_minutes: Poll duration in minutes (5-10080)

        Returns:
            Dict containing:
                - success: bool
                - tweet_id: str (if successful)
                - tweet_url: str (if successful)
                - error: error message (if failed)
        """
        if not self.is_available():
            error_msg = "Twitter posting not available. "
            if not TWEEPY_AVAILABLE:
                error_msg += "Tweepy not installed. Run: pip install tweepy"
            elif not self.configured:
                error_msg += "Twitter API credentials not configured. Set environment variables:\n"
                error_msg += "TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, "
                error_msg += "TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN"

            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'twitter_posting'
            }

        try:
            # Validate tweet text length
            if len(text) > 280:
                return {
                    'success': False,
                    'error': f'Tweet text too long ({len(text)} characters). Maximum is 280.',
                    'tool': 'twitter_posting'
                }

            self.logger.info(f"Posting tweet: {text[:50]}...")

            # Build tweet parameters
            tweet_params = {'text': text}

            # Add reply reference if provided
            if reply_to_id:
                tweet_params['in_reply_to_tweet_id'] = reply_to_id

            # Add poll if options provided
            if poll_options:
                if len(poll_options) < 2 or len(poll_options) > 4:
                    return {
                        'success': False,
                        'error': 'Poll must have 2-4 options',
                        'tool': 'twitter_posting'
                    }
                tweet_params['poll_options'] = poll_options
                tweet_params['poll_duration_minutes'] = poll_duration_minutes

            # Post the tweet
            response = self.client.create_tweet(**tweet_params)

            # Extract tweet ID and construct URL
            tweet_id = response.data['id']

            # Get authenticated user's username
            me = self.client.get_me()
            username = me.data.username

            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"

            self.logger.info(f"Tweet posted successfully: {tweet_url}")

            return {
                'success': True,
                'tweet_id': tweet_id,
                'tweet_url': tweet_url,
                'text': text,
                'tool': 'twitter_posting',
                'timestamp': datetime.now().isoformat()
            }

        except tweepy.errors.Forbidden as e:
            error_msg = f"Twitter API access forbidden: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'twitter_posting'
            }

        except tweepy.errors.TooManyRequests as e:
            error_msg = f"Twitter API rate limit exceeded: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'twitter_posting'
            }

        except tweepy.errors.TwitterServerError as e:
            error_msg = f"Twitter server error: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'twitter_posting'
            }

        except Exception as e:
            error_msg = f"Error posting tweet: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'tool': 'twitter_posting'
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
                    'max_length': 280,
                    'description': 'Tweet text content'
                },
                'reply_to_id': {
                    'type': 'string',
                    'required': False,
                    'description': 'Tweet ID to reply to'
                },
                'media_urls': {
                    'type': 'array',
                    'required': False,
                    'description': 'List of media URLs to attach'
                },
                'poll_options': {
                    'type': 'array',
                    'required': False,
                    'min_items': 2,
                    'max_items': 4,
                    'description': 'Poll options (2-4 choices)'
                },
                'poll_duration_minutes': {
                    'type': 'integer',
                    'required': False,
                    'default': 1440,
                    'min': 5,
                    'max': 10080,
                    'description': 'Poll duration in minutes'
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
            return f"❌ Twitter posting failed: {result.get('error', 'Unknown error')}"

        tweet_url = result.get('tweet_url', '')
        tweet_id = result.get('tweet_id', '')
        text = result.get('text', '')

        response = f"✅ Tweet posted successfully!\n\n"
        response += f"**Tweet URL:** {tweet_url}\n"
        response += f"**Tweet ID:** {tweet_id}\n\n"
        response += f"**Content:**\n> {text}\n"

        return response


# Factory function for easy integration
def create_twitter_posting_tool(
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    access_token: Optional[str] = None,
    access_token_secret: Optional[str] = None,
    bearer_token: Optional[str] = None
) -> TwitterPostingTool:
    """
    Factory function to create Twitter posting tool instance.

    Args:
        api_key: Optional Twitter API Key
        api_secret: Optional Twitter API Secret
        access_token: Optional Twitter Access Token
        access_token_secret: Optional Twitter Access Token Secret
        bearer_token: Optional Twitter Bearer Token

    Returns:
        TwitterPostingTool instance
    """
    return TwitterPostingTool(
        api_key=api_key,
        api_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        bearer_token=bearer_token
    )
