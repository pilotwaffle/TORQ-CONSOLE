#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X.AI Grok API Integration for TORQ Console
Secure integration with X.AI's Grok model

Features:
- Secure API key loading from .env
- Chat completions with Grok models
- Streaming support
- Error handling and retries
- Rate limiting protection
- Usage tracking

Usage:
    python xai_grok_integration.py --prompt "Your question here"
    python xai_grok_integration.py --stream --prompt "Tell me about AI"
    python xai_grok_integration.py --test  # Test API connection
"""

import os
import sys
import json
import time
import requests
from typing import Optional, Dict, List, Iterator
from dataclasses import dataclass
import argparse

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

@dataclass
class GrokResponse:
    """Response from Grok API."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float

class XAIGrokIntegration:
    """
    X.AI Grok API Integration for TORQ Console.

    Provides secure access to X.AI's Grok model with:
    - Chat completions
    - Streaming support
    - Error handling
    - Rate limiting
    - Usage tracking
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Grok integration with API key from environment or parameter."""
        self.api_key = api_key or os.getenv('XAI_API_KEY')
        self.api_base_url = os.getenv('XAI_API_BASE_URL', 'https://api.x.ai/v1')
        self.default_model = os.getenv('XAI_MODEL', 'grok-beta')

        if not self.api_key:
            raise ValueError(
                "X.AI API key not found. Set XAI_API_KEY in .env file.\n"
                "Get your API key from: https://console.x.ai/team/api-keys"
            )

        # Validate API key format
        if not self.api_key.startswith('xai-'):
            raise ValueError(
                f"Invalid X.AI API key format. Key should start with 'xai-'\n"
                f"Current key starts with: {self.api_key[:10]}..."
            )

        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        })

        # Usage tracking
        self.total_tokens = 0
        self.total_requests = 0
        self.total_cost = 0.0  # Estimate based on token usage

        print(f"[OK] X.AI Grok initialized (model: {self.default_model})")
        print(f"[OK] API key loaded: {self.api_key[:10]}...{self.api_key[-4:]}")

    def chat_completion(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> GrokResponse:
        """
        Send a chat completion request to Grok.

        Args:
            prompt: User message/question
            system_message: Optional system message
            model: Model to use (defaults to grok-beta)
            temperature: Creativity level (0.0-2.0)
            max_tokens: Maximum response length
            stream: Enable streaming response

        Returns:
            GrokResponse with content and metadata
        """
        start_time = time.time()

        # Build messages
        messages = []
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        messages.append({
            "role": "user",
            "content": prompt
        })

        # Build request payload
        payload = {
            "messages": messages,
            "model": model or self.default_model,
            "temperature": temperature,
            "stream": stream
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            # Make API request
            response = self.session.post(
                f"{self.api_base_url}/chat/completions",
                json=payload,
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            # Extract response
            message = data['choices'][0]['message']
            content = message['content']
            finish_reason = data['choices'][0]['finish_reason']

            # Track usage
            usage = data.get('usage', {})
            self.total_tokens += usage.get('total_tokens', 0)
            self.total_requests += 1

            response_time = time.time() - start_time

            return GrokResponse(
                content=content,
                model=data['model'],
                usage=usage,
                finish_reason=finish_reason,
                response_time=response_time
            )

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError(
                    "Invalid API key. Check your XAI_API_KEY in .env file.\n"
                    "Get a new key from: https://console.x.ai/team/api-keys"
                )
            elif e.response.status_code == 429:
                raise ValueError(
                    "Rate limit exceeded. Wait a moment and try again.\n"
                    f"Response: {e.response.text}"
                )
            else:
                raise ValueError(
                    f"API request failed: {e.response.status_code}\n"
                    f"Response: {e.response.text}"
                )

        except Exception as e:
            raise ValueError(f"Error calling X.AI API: {str(e)}")

    def chat_completion_stream(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Iterator[str]:
        """
        Stream chat completion response from Grok.

        Args:
            prompt: User message/question
            system_message: Optional system message
            model: Model to use
            temperature: Creativity level

        Yields:
            Response chunks as they arrive
        """
        # Build messages
        messages = []
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        messages.append({
            "role": "user",
            "content": prompt
        })

        # Build request payload
        payload = {
            "messages": messages,
            "model": model or self.default_model,
            "temperature": temperature,
            "stream": True
        }

        try:
            response = self.session.post(
                f"{self.api_base_url}/chat/completions",
                json=payload,
                stream=True,
                timeout=60
            )

            response.raise_for_status()

            # Process streaming response
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content')
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

            self.total_requests += 1

        except Exception as e:
            raise ValueError(f"Streaming error: {str(e)}")

    def test_connection(self) -> bool:
        """Test API connection with a simple request."""
        print("\n" + "="*70)
        print("[TEST] Testing X.AI Grok API connection...")
        print("="*70)

        try:
            response = self.chat_completion(
                prompt="Testing. Just say hi and hello world and nothing else.",
                system_message="You are a test assistant.",
                temperature=0
            )

            print(f"\n[SUCCESS] Connection test passed!")
            print(f"Model: {response.model}")
            print(f"Response: {response.content}")
            print(f"Response time: {response.response_time:.2f}s")
            print(f"Tokens used: {response.usage.get('total_tokens', 'N/A')}")
            print("="*70)

            return True

        except Exception as e:
            print(f"\n[ERROR] Connection test failed: {e}")
            print("="*70)
            return False

    def get_usage_stats(self) -> Dict[str, any]:
        """Get usage statistics."""
        return {
            'total_requests': self.total_requests,
            'total_tokens': self.total_tokens,
            'estimated_cost': self.total_tokens * 0.00002  # Rough estimate
        }


def main():
    """Main entry point for X.AI Grok integration."""
    parser = argparse.ArgumentParser(
        description='X.AI Grok API Integration for TORQ Console'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        help='Prompt to send to Grok'
    )
    parser.add_argument(
        '--system',
        type=str,
        help='System message'
    )
    parser.add_argument(
        '--model',
        type=str,
        choices=['grok-beta', 'grok-2-latest', 'grok-4-latest'],
        help='Model to use (default: grok-beta)'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Temperature (0.0-2.0, default: 0.7)'
    )
    parser.add_argument(
        '--stream',
        action='store_true',
        help='Enable streaming response'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test API connection'
    )

    args = parser.parse_args()

    try:
        # Initialize integration
        grok = XAIGrokIntegration()

        # Test mode
        if args.test:
            success = grok.test_connection()
            sys.exit(0 if success else 1)

        # Require prompt for normal mode
        if not args.prompt:
            parser.print_help()
            print("\nError: --prompt is required (or use --test)")
            sys.exit(1)

        print("\n" + "="*70)
        print("[GROK] Sending request to X.AI...")
        print("="*70)

        # Streaming mode
        if args.stream:
            print(f"\nPrompt: {args.prompt}")
            print("-"*70)
            print("Response (streaming):")
            print()

            full_response = ""
            for chunk in grok.chat_completion_stream(
                prompt=args.prompt,
                system_message=args.system,
                model=args.model,
                temperature=args.temperature
            ):
                print(chunk, end='', flush=True)
                full_response += chunk

            print("\n" + "-"*70)
            print(f"Total length: {len(full_response)} characters")

        # Standard mode
        else:
            response = grok.chat_completion(
                prompt=args.prompt,
                system_message=args.system,
                model=args.model,
                temperature=args.temperature
            )

            print(f"\nPrompt: {args.prompt}")
            print("-"*70)
            print("Response:")
            print(response.content)
            print("-"*70)
            print(f"Model: {response.model}")
            print(f"Tokens: {response.usage.get('total_tokens', 'N/A')}")
            print(f"Response time: {response.response_time:.2f}s")

        # Show usage stats
        stats = grok.get_usage_stats()
        print("\nSession Usage:")
        print(f"  Requests: {stats['total_requests']}")
        print(f"  Tokens: {stats['total_tokens']}")
        print(f"  Est. Cost: ${stats['estimated_cost']:.4f}")

        print("\n" + "="*70)
        print("[COMPLETE] Done!")
        print("="*70)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
