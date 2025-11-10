#!/usr/bin/env python3
"""
LongMemEval Comprehensive Test
Simulates long conversations over dozens of sessions
Measures accurate retention and recall of key facts, user preferences, and conversational history

Based on LongMemEval benchmark for long-term memory evaluation
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
import os
import sys

# Add TORQ Console to path
sys.path.append('E:/TORQ-CONSOLE')

from zep_enhanced_prince_flowers import create_zep_enhanced_prince_flowers
from torq_console.llm.providers.claude import ClaudeProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LongMemEvalTest:
    """Comprehensive long-term memory evaluation test"""

    def __init__(self, agent):
        self.agent = agent
        self.test_session_id = f"longmem_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger = logging.getLogger(f"{__name__}.{self.test_session_id}")

        # Test data for comprehensive evaluation
        self.user_profile = {
            "name": "Alex Chen",
            "role": "Senior Software Engineer",
            "company": "TechCorp",
            "preferences": {
                "programming_languages": ["Python", "TypeScript", "Go"],
                "frameworks": ["React", "FastAPI", "Django"],
                "work_style": "agile with daily standups",
                "communication_preference": "concise technical updates",
                "learning_style": "hands-on coding with examples",
                "meeting_preference": "afternoon meetings only"
            },
            "project_context": {
                "current_project": "Customer Analytics Dashboard",
                "technologies": ["React", "Python", "PostgreSQL", "Docker"],
                "team_size": 5,
                "deadline": "6 weeks",
                "main_challenges": ["performance optimization", "data visualization", "real-time updates"]
            },
            "personal_details": {
                "experience_years": 8,
                "specialization": "full-stack development",
                "hobbies": ["hiking", "photography", "technical blogging"],
                "location": "San Francisco",
                "timezone": "PST",
                "recent_vacation": "Japan trip last month"
            }
        }

        self.conversation_history = []
        self.test_results = {
            "sessions": [],
            "memory_accuracy": {},
            "preference_retention": {},
            "context_continuity": {},
            "overall_performance": 0.0
        }

    async def run_comprehensive_longmem_eval(self) -> Dict[str, Any]:
        """Run comprehensive LongMemEval test"""
        self.logger.info("Starting LongMemEval Comprehensive Test")

        # Phase 1: Establish baseline profile and context (Sessions 1-5)
        await self._phase1_establish_context()

        # Phase 2: Reinforce preferences and context (Sessions 6-15)
        await self._phase2_reinforce_context()

        # Phase 3: Test long-term retention (Sessions 16-25)
        await self._phase3_test_retention()

        # Phase 4: Complex scenario testing (Sessions 26-30)
        await self._phase4_complex_scenarios()

        # Calculate comprehensive results
        return await self._calculate_comprehensive_results()

    async def _phase1_establish_context(self):
        """Phase 1: Establish baseline profile and context"""
        self.logger.info("Phase 1: Establishing Context (Sessions 1-5)")

        phase1_sessions = [
            {
                "session_id": 1,
                "topic": "Introduction and Work Context",
                "queries": [
                    f"Hi, I'm {self.user_profile['name']}, a {self.user_profile['role']} at {self.user_profile['company']}. I'm working on a {self.user_profile['project_context']['current_project']}.",
                    f"I prefer {self.user_profile['preferences']['work_style']} and my main languages are {', '.join(self.user_profile['preferences']['programming_languages'][:2])}.",
                    f"Our team has {self.user_profile['project_context']['team_size']} members and we have {self.user_profile['project_context']['deadline']} deadline."
                ]
            },
            {
                "session_id": 2,
                "topic": "Technical Preferences",
                "queries": [
                    f"For the dashboard project, I'm using {', '.join(self.user_profile['project_context']['technologies'][:3])}.",
                    f"I really prefer {self.user_profile['preferences']['communication_preference']} when discussing technical issues.",
                    f"My favorite frameworks are {', '.join(self.user_profile['preferences']['frameworks'][:2])}."
                ]
            },
            {
                "session_id": 3,
                "topic": "Personal and Work Style",
                "queries": [
                    f"I have {self.user_profile['personal_details']['experience_years']} years of experience in {self.user_profile['personal_details']['specialization']}.",
                    f"I work best with {self.user_profile['preferences']['meeting_preference']} and prefer {self.user_profile['preferences']['learning_style']}.",
                    f"Recently I went on vacation to {self.user_profile['personal_details']['recent_vacation']}."
                ]
            },
            {
                "session_id": 4,
                "topic": "Project Challenges",
                "queries": [
                    f"The main challenges I'm facing are {', '.join(self.user_profile['project_context']['main_challenges'][:2])}.",
                    f"I'm based in {self.user_profile['personal_details']['location']} in {self.user_profile['personal_details']['timezone']}.",
                    f"My hobbies include {', '.join(self.user_profile['personal_details']['hobbies'][:2])}."
                ]
            },
            {
                "session_id": 5,
                "topic": "Reinforcement and Context Building",
                "queries": [
                    f"Just to confirm, I'm {self.user_profile['name']} working on {self.user_profile['project_context']['current_project']} at {self.user_profile['company']}.",
                    f"I mentioned I like {', '.join(self.user_profile['preferences']['programming_languages'])} for development.",
                    f"Remember I prefer {self.user_profile['preferences']['work_style']} methodology."
                ]
            }
        ]

        for session in phase1_sessions:
            await self._execute_session(session)

    async def _phase2_reinforce_context(self):
        """Phase 2: Reinforce preferences and context"""
        self.logger.info("Phase 2: Reinforcing Context (Sessions 6-15)")

        phase2_sessions = []

        # Create 10 sessions that reinforce different aspects
        for i in range(10):
            session_id = 6 + i
            topic_choices = [
                "Technical Problem Solving",
                "Project Planning",
                "Code Review Discussion",
                "Team Coordination",
                "Learning New Technologies"
            ]

            session = {
                "session_id": session_id,
                "topic": random.choice(topic_choices),
                "queries": self._generate_reinforcement_queries(session_id)
            }
            phase2_sessions.append(session)

        for session in phase2_sessions:
            await self._execute_session(session)

    async def _phase3_test_retention(self):
        """Phase 3: Test long-term retention"""
        self.logger.info("Phase 3: Testing Long-Term Retention (Sessions 16-25)")

        phase3_sessions = []

        # Create 10 sessions specifically for retention testing
        retention_test_queries = [
            "Can you remind me what my name and role are?",
            "What project am I currently working on?",
            "What programming languages do I prefer?",
            "How many people are on my team?",
            "What's my work style preference?",
            "Where am I located?",
            "What are the main challenges I'm facing?",
            "What frameworks do I like to use?",
            "When did I recently go on vacation?",
            "What's my communication preference for technical discussions?"
        ]

        for i in range(10):
            session_id = 16 + i
            # Mix in retention queries with normal conversation
            queries = []

            # Add 1-2 retention test queries
            retention_count = random.randint(1, 2)
            selected_retention = random.sample(retention_test_queries, retention_count)
            queries.extend(selected_retention)

            # Add some filler conversation
            queries.extend([
                f"Let's discuss some implementation details for the {self.user_profile['project_context']['current_project']}.",
                "I need some advice on best practices."
            ])

            session = {
                "session_id": session_id,
                "topic": "Retention Testing + Normal Discussion",
                "queries": queries
            }
            phase3_sessions.append(session)

        for session in phase3_sessions:
            await self._execute_session(session)

    async def _phase4_complex_scenarios(self):
        """Phase 4: Complex scenario testing"""
        self.logger.info("Phase 4: Complex Scenario Testing (Sessions 26-30)")

        phase4_scenarios = [
            {
                "session_id": 26,
                "scenario": "Cross-Domain Problem Solving",
                "query": f"I need to optimize the {self.user_profile['project_context']['current_project']} using my preferred stack of {', '.join(self.user_profile['preferences']['programming_languages'])}. Considering my {self.user_profile['personal_details']['experience_years']} years experience, what approach would you recommend?"
            },
            {
                "session_id": 27,
                "scenario": "Preference Application",
                "query": f"Given my preference for {self.user_profile['preferences']['work_style']} and {self.user_profile['preferences']['meeting_preference']}, how should I structure a 2-week sprint for the dashboard project considering we're in {self.user_profile['personal_details']['timezone']}?"
            },
            {
                "session_id": 28,
                "scenario": "Personalized Learning",
                "query": f"I want to learn more about {self.user_profile['project_context']['technologies'][1]} using my {self.user_profile['preferences']['learning_style']}. Can you create a learning plan that fits with my background in {self.user_profile['personal_details']['specialization']}?"
            },
            {
                "session_id": 29,
                "scenario": "Comprehensive Context Integration",
                "query": f"As a {self.user_profile['role']} at {self.user_profile['company']} with {self.user_profile['personal_details']['experience_years']} years experience, how should I approach the {', '.join(self.user_profile['project_context']['main_challenges'])} in my {self.user_profile['project_context']['current_project']} using {', '.join(self.user_profile['preferences']['frameworks'])}?"
            },
            {
                "session_id": 30,
                "scenario": "Final Comprehensive Recall",
                "query": f"Can you summarize everything you know about me - my work, preferences, project, and personal details? Be specific about what you remember from our conversations."
            }
        ]

        for scenario in phase4_scenarios:
            session = {
                "session_id": scenario["session_id"],
                "topic": scenario["scenario"],
                "queries": [scenario["query"]]
            }
            await self._execute_session(session)

    def _generate_reinforcement_queries(self, session_id: int) -> List[str]:
        """Generate reinforcement queries based on session number"""

        # Rotate through different aspects of the user profile
        aspect_rotation = session_id % 4

        base_queries = {
            0: [  # Work context
                f"Working on the {self.user_profile['project_context']['current_project']} today.",
                f"Need to solve some {self.user_profile['project_context']['main_challenges'][0]} issues.",
                f"Let's discuss best practices for {self.user_profile['preferences']['programming_languages'][0]}."
            ],
            1: [  # Personal preferences
                f"I prefer {self.user_profile['preferences']['communication_preference']} when discussing technical topics.",
                f"My favorite part of development is {self.user_profile['personal_details']['specialization']}.",
                f"Considering my experience with {', '.join(self.user_profile['preferences']['frameworks'])}, what do you think?"
            ],
            2: [  # Project details
                f"Our team of {self.user_profile['project_context']['team_size']} needs to deliver in {self.user_profile['project_context']['deadline']}.",
                f"Using {', '.join(self.user_profile['project_context']['technologies'])} for our current work.",
                f"The {self.user_profile['project_context']['main_challenges'][1]} is particularly challenging."
            ],
            3: [  # Personal details
                f"Based in {self.user_profile['personal_details']['location']}, working in {self.user_profile['personal_details']['timezone']}.",
                f"With my {self.user_profile['personal_details']['experience_years']} years experience, I think...",
                f"My hobbies like {self.user_profile['personal_details']['hobbies'][0]} help me stay balanced."
            ]
        }

        return base_queries.get(aspect_rotation, base_queries[0])

    async def _execute_session(self, session: Dict[str, Any]):
        """Execute a session and track results"""
        self.logger.info(f"Executing Session {session['session_id']}: {session['topic']}")

        session_start_time = time.time()
        session_results = []

        for query in session['queries']:
            try:
                start_time = time.time()
                result = await self.agent.process_query_with_zep_memory(query)
                execution_time = time.time() - start_time

                session_result = {
                    "query": query,
                    "success": result.get("success", False),
                    "confidence": result.get("confidence", 0.0),
                    "memory_used": result.get("zep_memory", {}).get("memories_used", 0),
                    "response_preview": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                    "execution_time": execution_time
                }

                session_results.append(session_result)

                # Small delay between queries
                await asyncio.sleep(0.5)

            except Exception as e:
                self.logger.error(f"Query failed in session {session['session_id']}: {e}")
                session_results.append({
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "execution_time": 0
                })

        session_total_time = time.time() - session_start_time

        session_data = {
            "session_id": session['session_id'],
            "topic": session['topic'],
            "total_time": session_total_time,
            "query_count": len(session['queries']),
            "results": session_results,
            "avg_confidence": sum(r.get("confidence", 0) for r in session_results) / len(session_results) if session_results else 0,
            "memory_usage": sum(r.get("memory_used", 0) for r in session_results) / len(session_results) if session_results else 0,
            "success_rate": sum(1 for r in session_results if r.get("success", False)) / len(session_results) if session_results else 0
        }

        self.conversation_history.append(session_data)
        self.test_results["sessions"].append(session_data)

    async def _calculate_comprehensive_results(self) -> Dict[str, Any]:
        """Calculate comprehensive test results"""
        self.logger.info("Calculating comprehensive LongMemEval results")

        # Memory accuracy tests
        memory_accuracy = await self._test_memory_accuracy()

        # Preference retention tests
        preference_retention = await self._test_preference_retention()

        # Context continuity tests
        context_continuity = await self._test_context_continuity()

        # Overall performance score
        overall_performance = (
            memory_accuracy["score"] * 0.4 +
            preference_retention["score"] * 0.3 +
            context_continuity["score"] * 0.3
        )

        comprehensive_results = {
            "test_type": "LongMemEval Comprehensive Test",
            "test_date": datetime.now().isoformat(),
            "total_sessions": len(self.conversation_history),
            "total_queries": sum(len(s["results"]) for s in self.conversation_history),
            "memory_accuracy": memory_accuracy,
            "preference_retention": preference_retention,
            "context_continuity": context_continuity,
            "overall_performance": overall_performance,
            "performance_grade": self._calculate_performance_grade(overall_performance),
            "detailed_results": self.test_results
        }

        return comprehensive_results

    async def _test_memory_accuracy(self) -> Dict[str, Any]:
        """Test memory accuracy across sessions"""

        accuracy_tests = [
            {
                "name": "Name Recall",
                "expected": self.user_profile["name"],
                "test_query": "What is my name?",
                "sessions_tested": []
            },
            {
                "name": "Role Recall",
                "expected": self.user_profile["role"],
                "test_query": "What is my role?",
                "sessions_tested": []
            },
            {
                "name": "Company Recall",
                "expected": self.user_profile["company"],
                "test_query": "What company do I work for?",
                "sessions_tested": []
            },
            {
                "name": "Project Recall",
                "expected": self.user_profile["project_context"]["current_project"],
                "test_query": "What project am I working on?",
                "sessions_tested": []
            },
            {
                "name": "Location Recall",
                "expected": self.user_profile["personal_details"]["location"],
                "test_query": "Where am I located?",
                "sessions_tested": []
            }
        ]

        # Find sessions where these topics were discussed
        for test in accuracy_tests:
            for session in self.conversation_history:
                for result in session["results"]:
                    if any(keyword in result["query"].lower() for keyword in
                          [test["name"].lower().split()[0], "what", "who", "where"]):
                        # Check if response contains expected information
                        response_lower = result["response_preview"].lower()
                        expected_lower = test["expected"].lower()

                        is_accurate = expected_lower in response_lower
                        test["sessions_tested"].append({
                            "session_id": session["session_id"],
                            "accurate": is_accurate,
                            "confidence": result.get("confidence", 0),
                            "memory_used": result.get("memory_used", 0)
                        })

        # Calculate accuracy scores
        total_accurate = 0
        total_tests = 0

        for test in accuracy_tests:
            if test["sessions_tested"]:
                accurate_count = sum(1 for t in test["sessions_tested"] if t["accurate"])
                test["accuracy_rate"] = accurate_count / len(test["sessions_tested"])
                test["avg_confidence"] = sum(t["confidence"] for t in test["sessions_tested"]) / len(test["sessions_tested"])
                test["avg_memory_usage"] = sum(t["memory_used"] for t in test["sessions_tested"]) / len(test["sessions_tested"])

                total_accurate += accurate_count
                total_tests += len(test["sessions_tested"])
            else:
                test["accuracy_rate"] = 0.0
                test["avg_confidence"] = 0.0
                test["avg_memory_usage"] = 0.0

        overall_accuracy = total_accurate / total_tests if total_tests > 0 else 0.0

        return {
            "overall_accuracy": overall_accuracy,
            "detailed_tests": accuracy_tests,
            "total_tests": total_tests,
            "score": overall_accuracy
        }

    async def _test_preference_retention(self) -> Dict[str, Any]:
        """Test preference retention across sessions"""

        preference_tests = [
            {
                "name": "Programming Languages",
                "expected": self.user_profile["preferences"]["programming_languages"],
                "keywords": ["python", "typescript", "go", "programming", "languages"]
            },
            {
                "name": "Work Style",
                "expected": self.user_profile["preferences"]["work_style"],
                "keywords": ["agile", "standups", "work", "style"]
            },
            {
                "name": "Communication Preference",
                "expected": self.user_profile["preferences"]["communication_preference"],
                "keywords": ["communication", "technical", "updates", "concise"]
            },
            {
                "name": "Learning Style",
                "expected": self.user_profile["preferences"]["learning_style"],
                "keywords": ["learning", "hands", "coding", "examples"]
            }
        ]

        retention_scores = []

        for test in preference_tests:
            matching_sessions = []

            for session in self.conversation_history:
                for result in session["results"]:
                    if any(keyword in result["response_preview"].lower() for keyword in test["keywords"]):
                        # Check if preferences are correctly recalled
                        response_lower = result["response_preview"].lower()
                        preference_matches = sum(1 for pref in test["expected"] if pref.lower() in response_lower)
                        match_rate = preference_matches / len(test["expected"])

                        matching_sessions.append({
                            "session_id": session["session_id"],
                            "match_rate": match_rate,
                            "confidence": result.get("confidence", 0),
                            "memory_used": result.get("memory_used", 0)
                        })

            if matching_sessions:
                avg_match_rate = sum(s["match_rate"] for s in matching_sessions) / len(matching_sessions)
                avg_confidence = sum(s["confidence"] for s in matching_sessions) / len(matching_sessions)

                retention_scores.append({
                    "preference": test["name"],
                    "avg_match_rate": avg_match_rate,
                    "avg_confidence": avg_confidence,
                    "sessions_found": len(matching_sessions)
                })

        overall_retention = sum(s["avg_match_rate"] for s in retention_scores) / len(retention_scores) if retention_scores else 0.0

        return {
            "overall_retention": overall_retention,
            "detailed_results": retention_scores,
            "score": overall_retention
        }

    async def _test_context_continuity(self) -> Dict[str, Any]:
        """Test context continuity across sessions"""

        # Test if the agent maintains context about the user's situation
        continuity_tests = []

        # Check project context continuity
        project_context_sessions = []
        for session in self.conversation_history:
            for result in session["results"]:
                response_lower = result["response_preview"].lower()
                if any(term in response_lower for term in ["project", "dashboard", "analytics", "customer"]):
                    project_context_sessions.append({
                        "session_id": session["session_id"],
                        "mentions_project": True,
                        "confidence": result.get("confidence", 0),
                        "memory_used": result.get("memory_used", 0)
                    })

        # Check work context continuity
        work_context_sessions = []
        for session in self.conversation_history:
            for result in session["results"]:
                response_lower = result["response_preview"].lower()
                if any(term in response_lower for term in ["engineer", "developer", "techcorp", "software"]):
                    work_context_sessions.append({
                        "session_id": session["session_id"],
                        "mentions_work": True,
                        "confidence": result.get("confidence", 0),
                        "memory_used": result.get("memory_used", 0)
                    })

        # Calculate continuity scores
        total_sessions = len(self.conversation_history)

        project_continuity = len(project_context_sessions) / total_sessions if total_sessions > 0 else 0.0
        work_continuity = len(work_context_sessions) / total_sessions if total_sessions > 0 else 0.0

        # Test memory consistency (does the agent remember the same facts consistently?)
        memory_consistency = await self._test_memory_consistency()

        overall_continuity = (project_continuity + work_continuity + memory_consistency) / 3

        return {
            "overall_continuity": overall_continuity,
            "project_continuity": project_continuity,
            "work_continuity": work_continuity,
            "memory_consistency": memory_consistency,
            "score": overall_continuity
        }

    async def _test_memory_consistency(self) -> float:
        """Test if the agent remembers facts consistently"""

        # Find sessions where the same information should be recalled
        consistency_scores = []

        # Test name consistency
        name_mentions = []
        for session in self.conversation_history:
            for result in session["results"]:
                response_lower = result["response_preview"].lower()
                if "alex" in response_lower or "chen" in response_lower:
                    name_mentions.append({
                        "session_id": session["session_id"],
                        "mentions_name": True,
                        "confidence": result.get("confidence", 0)
                    })

        if len(name_mentions) > 1:
            # If the name is mentioned in multiple sessions, that's good consistency
            consistency_scores.append(min(len(name_mentions) / 10, 1.0))

        # Test role consistency
        role_mentions = []
        for session in self.conversation_history:
            for result in session["results"]:
                response_lower = result["response_preview"].lower()
                if "engineer" in response_lower or "developer" in response_lower or "software" in response_lower:
                    role_mentions.append({
                        "session_id": session["session_id"],
                        "mentions_role": True,
                        "confidence": result.get("confidence", 0)
                    })

        if len(role_mentions) > 1:
            consistency_scores.append(min(len(role_mentions) / 10, 1.0))

        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5

    def _calculate_performance_grade(self, score: float) -> str:
        """Calculate performance grade based on score"""
        if score >= 0.95:
            return "A+ (Exceptional)"
        elif score >= 0.90:
            return "A (Excellent)"
        elif score >= 0.85:
            return "B+ (Very Good)"
        elif score >= 0.80:
            return "B (Good)"
        elif score >= 0.75:
            return "C+ (Satisfactory)"
        elif score >= 0.70:
            return "C (Acceptable)"
        elif score >= 0.60:
            return "D (Needs Improvement)"
        else:
            return "F (Poor)"

async def run_longmemeval_test():
    """Main function to run LongMemEval test"""
    print("=" * 80)
    print("LONGMEMEVAL COMPREHENSIVE TEST")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Simulating long conversations over 30 sessions")
    print("Measuring retention and recall of key facts and preferences")
    print("=" * 80)

    # Initialize agent
    print("\n1. Initializing Enhanced Prince Flowers Agent...")
    print("-" * 50)

    try:
        # Configure LLM provider
        api_key = os.getenv('ANTHROPIC_AUTH_TOKEN')
        if not api_key:
            print("[ERROR] ANTHROPIC_AUTH_TOKEN not found")
            return False

        claude_config = {
            'api_key': api_key,
            'model': 'claude-sonnet-4-5-20250929',
            'base_url': os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com'),
            'timeout': 60
        }

        llm_provider = ClaudeProvider(claude_config)
        agent = create_zep_enhanced_prince_flowers(llm_provider=llm_provider)
        initialized = await agent.initialize()

        if not initialized:
            print("[ERROR] Agent initialization failed")
            return False

        print("[OK] Agent initialized successfully")

    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return False

    # Run LongMemEval test
    print("\n2. Running LongMemEval Test...")
    print("-" * 50)

    longmem_test = LongMemEvalTest(agent)
    results = await longmem_test.run_comprehensive_longmem_eval()

    # Display results
    print(f"\n3. LongMemEval Test Results")
    print("-" * 50)

    print(f"Total Sessions: {results['total_sessions']}")
    print(f"Total Queries: {results['total_queries']}")
    print(f"Overall Performance: {results['overall_performance']:.1%}")
    print(f"Performance Grade: {results['performance_grade']}")

    print(f"\nMemory Accuracy: {results['memory_accuracy']['overall_accuracy']:.1%}")
    print(f"Preference Retention: {results['preference_retention']['overall_retention']:.1%}")
    print(f"Context Continuity: {results['context_continuity']['overall_continuity']:.1%}")

    print(f"\nDetailed Memory Accuracy:")
    for test in results['memory_accuracy']['detailed_tests']:
        print(f"  {test['name']}: {test['accuracy_rate']:.1%} accuracy")
        print(f"    Sessions tested: {len(test['sessions_tested'])}")
        print(f"    Avg confidence: {test['avg_confidence']:.3f}")

    print(f"\nPreference Retention Details:")
    for test in results['preference_retention']['detailed_results']:
        print(f"  {test['preference']}: {test['avg_match_rate']:.1%} match rate")
        print(f"    Sessions found: {test['sessions_found']}")
        print(f"    Avg confidence: {test['avg_confidence']:.3f}")

    # Save results
    results_file = "E:/TORQ-CONSOLE/maxim_integration/longmemeval_test_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[OK] Results saved to: {results_file}")

    # Cleanup
    try:
        await agent.cleanup()
        print("[OK] Agent cleanup completed")
    except Exception as e:
        print(f"[WARNING] Cleanup failed: {e}")

    return results['overall_performance'] >= 0.75

if __name__ == "__main__":
    asyncio.run(run_longmemeval_test())