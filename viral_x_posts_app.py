#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viral X (Twitter) Posts Generator - TORQ Console App Builder
Created with Prince Flowers Enhanced Agent

Features:
- AI-powered viral content generation
- Multiple post formats and styles
- Hashtag optimization
- Thread generation
- Demo mode for testing without credentials
- Rate limiting and safety checks

Usage:
    python viral_x_posts_app.py --mode=generate
    python viral_x_posts_app.py --mode=post --content="Your post here"
    python viral_x_posts_app.py --mode=thread --topic="AI trends"
    python viral_x_posts_app.py --demo  # Run without Twitter credentials
"""

import os
import sys
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
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
class ViralPost:
    """Structure for viral post content."""
    content: str
    hashtags: List[str]
    style: str
    engagement_score: float
    char_count: int

class ViralContentGenerator:
    """AI-powered viral content generator for X/Twitter."""

    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode or os.getenv('TWITTER_DEMO_MODE', 'false').lower() == 'true'
        self.max_length = 280  # Twitter character limit

        # Viral content templates
        self.templates = {
            'question': [
                "What if {topic}?",
                "Why doesn't anyone talk about {topic}?",
                "Hot take: {opinion} - agree or disagree?",
                "Unpopular opinion: {opinion}. Change my mind.",
            ],
            'list': [
                "🧵 {number} things about {topic} that changed my perspective:",
                "Top {number} insights about {topic} nobody talks about:",
                "{number} lessons I learned from {topic}:",
            ],
            'story': [
                "A year ago, I {past}. Today, I {present}. Here's what changed:",
                "Nobody tells you that {insight}. But here's the truth:",
                "I spent {time} learning {topic}. Here's what I discovered:",
            ],
            'announcement': [
                "🚀 Just launched: {product}",
                "Big news: {announcement}",
                "Excited to share: {news}",
            ],
            'insight': [
                "💡 Most people don't realize that {insight}",
                "The secret to {goal} is {method}. Not many people know this.",
                "After {experience}, I learned that {lesson}",
            ]
        }

        # Viral hashtag categories
        self.hashtag_sets = {
            'tech': ['#Tech', '#AI', '#Innovation', '#StartUp', '#FutureOfWork'],
            'business': ['#Business', '#Entrepreneur', '#Growth', '#Success', '#Leadership'],
            'learning': ['#Learning', '#Growth', '#SelfImprovement', '#Knowledge', '#Wisdom'],
            'motivation': ['#Motivation', '#Inspiration', '#Success', '#Goals', '#Mindset'],
            'ai': ['#AI', '#MachineLearning', '#ChatGPT', '#ArtificialIntelligence', '#ML'],
        }

        self.viral_patterns = [
            "contrarian_take",
            "numbered_list",
            "story_arc",
            "question_hook",
            "bold_claim",
            "personal_experience",
            "how_to_guide",
            "myth_busting"
        ]

    def generate_viral_post(
        self,
        topic: str,
        style: Optional[str] = None,
        category: str = 'tech'
    ) -> ViralPost:
        """Generate a viral post about the given topic."""

        if not style:
            style = random.choice(list(self.templates.keys()))

        # Generate content based on style
        template = random.choice(self.templates.get(style, self.templates['insight']))

        # Fill in template with topic-specific content
        content = self._fill_template(template, topic, style)

        # Add relevant hashtags
        hashtags = self._select_hashtags(category, limit=3)

        # Calculate engagement score (heuristic)
        engagement_score = self._calculate_engagement_score(content, hashtags, style)

        # Ensure content fits Twitter limit
        full_content = f"{content}\n\n{' '.join(hashtags)}"
        if len(full_content) > self.max_length:
            # Truncate content to fit
            available_space = self.max_length - len(' '.join(hashtags)) - 3  # account for newlines
            content = content[:available_space] + "..."
            full_content = f"{content}\n\n{' '.join(hashtags)}"

        return ViralPost(
            content=full_content,
            hashtags=hashtags,
            style=style,
            engagement_score=engagement_score,
            char_count=len(full_content)
        )

    def generate_thread(
        self,
        topic: str,
        num_tweets: int = 5,
        category: str = 'tech'
    ) -> List[ViralPost]:
        """Generate a viral thread about the topic."""

        thread = []

        # Hook tweet (1/n)
        hook = self.generate_viral_post(topic, style='question', category=category)
        hook_content = f"🧵 Thread: {topic}\n\n{hook.content.split(chr(10))[0]}\n\n(1/{num_tweets})"
        thread.append(ViralPost(
            content=hook_content,
            hashtags=hook.hashtags,
            style='thread_hook',
            engagement_score=hook.engagement_score,
            char_count=len(hook_content)
        ))

        # Body tweets
        styles = ['insight', 'list', 'story']
        for i in range(1, num_tweets - 1):
            style = random.choice(styles)
            post = self.generate_viral_post(topic, style=style, category=category)
            tweet_content = f"{post.content.split(chr(10))[0]}\n\n({i+1}/{num_tweets})"
            thread.append(ViralPost(
                content=tweet_content,
                hashtags=[],  # No hashtags in middle tweets
                style=style,
                engagement_score=post.engagement_score,
                char_count=len(tweet_content)
            ))

        # CTA tweet (n/n)
        cta = f"If you found this thread valuable:\n\n✅ Follow for more insights on {topic}\n💬 Share your thoughts below\n🔁 Retweet to help others\n\n({num_tweets}/{num_tweets})"
        thread.append(ViralPost(
            content=cta,
            hashtags=hook.hashtags,
            style='cta',
            engagement_score=0.85,
            char_count=len(cta)
        ))

        return thread

    def _fill_template(self, template: str, topic: str, style: str) -> str:
        """Fill template with context-appropriate content."""

        # Topic-specific content generation
        if '{number}' in template:
            number = random.choice(['3', '5', '7', '10'])
            template = template.replace('{number}', number)

        if '{topic}' in template:
            template = template.replace('{topic}', topic)

        if '{opinion}' in template:
            opinions = [
                f"{topic} is overrated",
                f"{topic} will change everything in 2025",
                f"most people misunderstand {topic}",
                f"{topic} is more important than you think"
            ]
            template = template.replace('{opinion}', random.choice(opinions))

        if '{insight}' in template:
            insights = [
                f"{topic} isn't about what you think it is",
                f"the real value of {topic} is hidden in plain sight",
                f"{topic} works differently than expected",
                f"success with {topic} requires this counterintuitive approach"
            ]
            template = template.replace('{insight}', random.choice(insights))

        return template

    def _select_hashtags(self, category: str, limit: int = 3) -> List[str]:
        """Select viral hashtags for the category."""
        hashtags = self.hashtag_sets.get(category, self.hashtag_sets['tech'])
        return random.sample(hashtags, min(limit, len(hashtags)))

    def _calculate_engagement_score(
        self,
        content: str,
        hashtags: List[str],
        style: str
    ) -> float:
        """Calculate predicted engagement score (0.0 - 1.0)."""

        score = 0.5  # Base score

        # Style bonuses
        style_scores = {
            'question': 0.15,
            'list': 0.20,
            'story': 0.18,
            'announcement': 0.10,
            'insight': 0.15
        }
        score += style_scores.get(style, 0.1)

        # Content factors
        if '?' in content:
            score += 0.08  # Questions increase engagement
        if any(emoji in content for emoji in ['🚀', '💡', '🧵', '✅', '🔥']):
            score += 0.10  # Emojis increase visibility
        if len(content) > 200:
            score += 0.05  # Longer posts (but not too long)
        if len(hashtags) == 3:
            score += 0.07  # Optimal hashtag count

        return min(score, 1.0)

    def post_to_twitter(self, content: str) -> Dict[str, any]:
        """Post content to Twitter (or simulate in demo mode)."""

        if self.demo_mode:
            print("\n" + "="*70)
            print("[DEMO MODE] Post Preview (Not Actually Posted)")
            print("="*70)
            print(f"\n{content}\n")
            print("="*70)
            print(f"Characters: {len(content)}/{self.max_length}")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*70)

            return {
                'success': True,
                'mode': 'demo',
                'message': 'Post previewed successfully (demo mode)',
                'char_count': len(content)
            }

        # Real Twitter posting
        try:
            # Check for credentials
            required_vars = [
                'TWITTER_API_KEY',
                'TWITTER_API_SECRET',
                'TWITTER_ACCESS_TOKEN',
                'TWITTER_ACCESS_TOKEN_SECRET'
            ]

            missing = [var for var in required_vars if not os.getenv(var)]

            if missing:
                raise ValueError(
                    f"Missing Twitter API credentials: {', '.join(missing)}\n"
                    f"Please configure in .env file or run with --demo flag.\n"
                    f"See TWITTER_API_SETUP_GUIDE.md for instructions."
                )

            # Import Twitter library (tweepy)
            try:
                import tweepy
            except ImportError:
                raise ImportError(
                    "tweepy not installed. Install with: pip install tweepy"
                )

            # Authenticate
            auth = tweepy.OAuthHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET')
            )
            auth.set_access_token(
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )

            api = tweepy.API(auth)

            # Post tweet
            status = api.update_status(content)

            return {
                'success': True,
                'mode': 'live',
                'tweet_id': status.id_str,
                'url': f"https://twitter.com/user/status/{status.id_str}",
                'char_count': len(content),
                'created_at': status.created_at.isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to post to Twitter'
            }

    def post_thread(self, thread: List[ViralPost]) -> List[Dict[str, any]]:
        """Post a thread to Twitter."""

        results = []
        previous_tweet_id = None

        for i, post in enumerate(thread):
            print(f"\nPosting tweet {i+1}/{len(thread)}...")

            if self.demo_mode:
                result = self.post_to_twitter(post.content)
                results.append(result)
                time.sleep(0.5)  # Simulate delay
            else:
                # In real mode, reply to previous tweet
                try:
                    import tweepy

                    auth = tweepy.OAuthHandler(
                        os.getenv('TWITTER_API_KEY'),
                        os.getenv('TWITTER_API_SECRET')
                    )
                    auth.set_access_token(
                        os.getenv('TWITTER_ACCESS_TOKEN'),
                        os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
                    )

                    api = tweepy.API(auth)

                    if previous_tweet_id:
                        status = api.update_status(
                            post.content,
                            in_reply_to_status_id=previous_tweet_id,
                            auto_populate_reply_metadata=True
                        )
                    else:
                        status = api.update_status(post.content)

                    previous_tweet_id = status.id_str

                    results.append({
                        'success': True,
                        'tweet_id': status.id_str,
                        'url': f"https://twitter.com/user/status/{status.id_str}"
                    })

                    time.sleep(2)  # Rate limiting delay

                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e)
                    })
                    break

        return results


def main():
    """Main entry point for viral posts app."""

    parser = argparse.ArgumentParser(
        description='Viral X (Twitter) Posts Generator - TORQ Console App'
    )
    parser.add_argument(
        '--mode',
        choices=['generate', 'post', 'thread'],
        default='generate',
        help='Operation mode: generate, post, or thread'
    )
    parser.add_argument(
        '--topic',
        type=str,
        help='Topic for content generation'
    )
    parser.add_argument(
        '--content',
        type=str,
        help='Custom content to post (for post mode)'
    )
    parser.add_argument(
        '--category',
        choices=['tech', 'business', 'learning', 'motivation', 'ai'],
        default='tech',
        help='Content category for hashtag selection'
    )
    parser.add_argument(
        '--style',
        choices=['question', 'list', 'story', 'announcement', 'insight'],
        help='Post style (auto-selected if not specified)'
    )
    parser.add_argument(
        '--num-tweets',
        type=int,
        default=5,
        help='Number of tweets in thread (for thread mode)'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode (no actual posting)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Save generated content to file'
    )

    args = parser.parse_args()

    # Initialize generator
    generator = ViralContentGenerator(demo_mode=args.demo)

    print("\n" + "="*70)
    print("[VIRAL POSTS] X Posts Generator - TORQ Console")
    print("="*70)

    if args.demo:
        print("[DEMO MODE] Posts will not be published")
        print("="*70)

    # Execute based on mode
    if args.mode == 'generate':
        # Generate mode
        if not args.topic:
            args.topic = input("\nEnter topic for viral post: ")

        print(f"\n[GENERATE] Creating viral post about: {args.topic}")
        post = generator.generate_viral_post(
            args.topic,
            style=args.style,
            category=args.category
        )

        print("\n" + "-"*70)
        print("Generated Content:")
        print("-"*70)
        print(post.content)
        print("-"*70)
        print(f"Style: {post.style}")
        print(f"Characters: {post.char_count}/{generator.max_length}")
        print(f"Predicted Engagement: {post.engagement_score:.1%}")
        print("-"*70)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump({
                    'content': post.content,
                    'hashtags': post.hashtags,
                    'style': post.style,
                    'engagement_score': post.engagement_score,
                    'char_count': post.char_count,
                    'generated_at': datetime.now().isoformat()
                }, f, indent=2)
            print(f"\n[OK] Saved to: {args.output}")

    elif args.mode == 'post':
        # Post mode
        if args.content:
            content_to_post = args.content
        elif args.topic:
            post = generator.generate_viral_post(
                args.topic,
                style=args.style,
                category=args.category
            )
            content_to_post = post.content
        else:
            print("Error: Either --content or --topic is required for post mode")
            return

        print(f"\n[POST] Posting to X (Twitter)...")
        result = generator.post_to_twitter(content_to_post)

        if result['success']:
            print("\n[SUCCESS] Post completed!")
            if result['mode'] == 'live':
                print(f"Tweet URL: {result['url']}")
            else:
                print("(Demo mode - not actually posted)")
        else:
            print(f"\n[ERROR] {result.get('error', 'Unknown error')}")

    elif args.mode == 'thread':
        # Thread mode
        if not args.topic:
            args.topic = input("\nEnter topic for thread: ")

        print(f"\n[THREAD] Generating thread about: {args.topic}")
        print(f"Number of tweets: {args.num_tweets}")

        thread = generator.generate_thread(
            args.topic,
            num_tweets=args.num_tweets,
            category=args.category
        )

        print("\n" + "-"*70)
        print("Thread Preview:")
        print("-"*70)
        for i, post in enumerate(thread, 1):
            print(f"\nTweet {i}/{len(thread)}:")
            print(post.content)
            print(f"Characters: {post.char_count}")
        print("-"*70)

        # Ask to post
        if input("\nPost this thread? (y/n): ").lower() == 'y':
            results = generator.post_thread(thread)

            success_count = sum(1 for r in results if r['success'])
            print(f"\n[SUCCESS] Posted {success_count}/{len(thread)} tweets")

            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump({
                        'thread': [{'content': p.content, 'result': r}
                                  for p, r in zip(thread, results)],
                        'generated_at': datetime.now().isoformat()
                    }, f, indent=2)
                print(f"Saved results to: {args.output}")

    print("\n" + "="*70)
    print("[COMPLETE] Done!")
    print("="*70)


if __name__ == '__main__':
    main()
