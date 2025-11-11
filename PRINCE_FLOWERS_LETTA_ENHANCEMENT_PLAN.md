# Prince Flowers Enhanced with Letta Memory - Implementation Plan

**Date:** 2025-11-11
**Branch:** `main` (merged)
**Status:** 🚧 Planning Phase 2

---

## Overview

Enhance Prince Flowers agent with Letta memory integration for persistent memory, learning, and improved user experience.

---

## Phase 1: Core Integration ✅ COMPLETE

- ✅ Letta memory manager created
- ✅ Memory operations (add, retrieve, feedback)
- ✅ Tests and documentation
- ✅ Merged to main

---

## Phase 2: Memory-Enhanced Prince Flowers (Next)

### Step 1: Create Enhanced Prince Flowers Class

**Goal:** Wrap Prince Flowers with Letta memory layer

**Implementation:**
- Create `EnhancedPrinceFlowers` class
- Integrate memory manager
- Add memory-aware response generation
- Implement conversation context tracking

**Files to Create:**
- `torq_console/agents/enhanced_prince_flowers.py`

**Key Features:**
```python
class EnhancedPrinceFlowers:
    def __init__(self, memory_enabled=True):
        self.memory = LettaMemoryManager(agent_name="prince_flowers")
        self.base_agent = PrinceFlowers()

    async def chat_with_memory(self, user_message: str):
        # 1. Store user message
        await self.memory.add_memory(user_message, metadata={"role": "user"})

        # 2. Get relevant context
        context = await self.memory.get_relevant_context(user_message)

        # 3. Generate response with context
        response = await self.base_agent.generate_response(user_message, context)

        # 4. Store response
        await self.memory.add_memory(response, metadata={"role": "assistant"})

        return response
```

**Success Criteria:**
- ✅ EnhancedPrinceFlowers class created
- ✅ Memory integration working
- ✅ Tests passing

---

### Step 2: Add Conversation History Tracking

**Goal:** Maintain full conversation history with context

**Implementation:**
- Track conversation sessions
- Link messages in sessions
- Provide session summaries
- Enable session continuation

**Features:**
```python
class ConversationSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages = []
        self.start_time = datetime.now()

    async def add_message(self, role: str, content: str):
        """Add message to session and memory."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        self.messages.append(message)

        # Store in Letta memory
        await memory.add_memory(
            content,
            metadata={
                "session_id": self.session_id,
                "role": role,
                "message_index": len(self.messages)
            }
        )

    async def get_summary(self) -> str:
        """Generate conversation summary."""
        # Use memory to create summary
        context = await memory.get_relevant_context(
            query=f"Summarize session {self.session_id}",
            max_memories=20
        )
        return self._generate_summary(context)
```

**Success Criteria:**
- ✅ Session tracking implemented
- ✅ Message linking working
- ✅ Session summaries generated
- ✅ Tests passing

---

### Step 3: Implement User Preference Learning

**Goal:** Learn and adapt to user preferences automatically

**Implementation:**
- Detect preference signals
- Extract preferences from conversations
- Apply preferences to responses
- Update preferences based on feedback

**Features:**
```python
class PreferenceLearning:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.preference_patterns = [
            # Programming language preferences
            r"I (prefer|like|use) (\w+) for",
            r"(\w+) is my (favorite|preferred)",

            # Code style preferences
            r"I (always|usually|prefer to) (\w+)",
            r"make sure to (\w+)",

            # Format preferences
            r"(don't|do not) (include|add|use) (\w+)",
            r"always (include|show|add) (\w+)"
        ]

    async def detect_and_store_preferences(self, message: str):
        """Detect preferences in user message."""
        for pattern in self.preference_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                preference = self._extract_preference(match)
                if preference:
                    await self.memory.add_memory(
                        f"User preference: {preference}",
                        metadata={"type": "preference", "importance": 0.9}
                    )

    async def apply_preferences(self, response: str) -> str:
        """Apply learned preferences to response."""
        preferences = await self.memory.get_user_preferences()

        # Modify response based on preferences
        # Example: User prefers TypeScript -> suggest TypeScript solutions
        modified_response = self._apply_preference_rules(response, preferences)

        return modified_response
```

**Success Criteria:**
- ✅ Preference detection working
- ✅ Preferences applied to responses
- ✅ Learning improves over time
- ✅ Tests passing

---

### Step 4: Add Feedback Learning Loop

**Goal:** Improve responses based on user feedback

**Implementation:**
- Capture implicit feedback (thumbs up/down)
- Capture explicit feedback (corrections)
- Learn from feedback patterns
- Adjust future responses

**Features:**
```python
class FeedbackLearning:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.feedback_patterns = []

    async def record_implicit_feedback(
        self,
        interaction_id: str,
        user_action: str  # "accepted", "rejected", "modified"
    ):
        """Record implicit feedback from user actions."""
        score = {
            "accepted": 1.0,
            "modified": 0.5,
            "rejected": 0.0
        }.get(user_action, 0.5)

        await self.memory.record_feedback(
            interaction_id=interaction_id,
            score=score,
            feedback_type="implicit"
        )

    async def record_explicit_feedback(
        self,
        interaction_id: str,
        original_response: str,
        corrected_response: str
    ):
        """Learn from user corrections."""
        # Extract what changed
        differences = self._extract_differences(
            original_response,
            corrected_response
        )

        # Store learning
        for diff in differences:
            await self.memory.add_memory(
                f"User correction: {diff['pattern']}",
                metadata={
                    "type": "correction",
                    "interaction_id": interaction_id,
                    "importance": 0.95
                }
            )

        # Record feedback
        await self.memory.record_feedback(
            interaction_id=interaction_id,
            score=0.3,  # Low score for needed correction
            feedback_type="explicit_correction"
        )

    async def improve_future_responses(self, query: str) -> Dict:
        """Get improvement suggestions based on feedback."""
        # Retrieve relevant corrections
        context = await self.memory.get_relevant_context(
            query=f"corrections for similar query: {query}",
            max_memories=10
        )

        # Extract patterns
        improvements = self._extract_improvement_patterns(context)

        return improvements
```

**Success Criteria:**
- ✅ Implicit feedback captured
- ✅ Explicit corrections learned
- ✅ Responses improve over time
- ✅ Tests passing

---

## Implementation Timeline

### Day 1 (Today)
- ✅ Plan documented
- 🚧 Step 1: Enhanced Prince Flowers class
- 🚧 Step 2: Conversation tracking

### Day 2
- 🚧 Step 3: Preference learning
- 🚧 Step 4: Feedback loop
- 🚧 Integration tests

### Day 3
- 🚧 End-to-end testing
- 🚧 Documentation
- 🚧 Deploy to production

---

## Testing Strategy

### Unit Tests
- Memory operations
- Preference detection
- Feedback recording
- Session management

### Integration Tests
- Enhanced Prince Flowers workflow
- Memory persistence
- Cross-session continuity
- Preference application

### End-to-End Tests
- Full conversation with memory
- Learning from feedback
- Preference adaptation
- Multi-session scenarios

---

## Success Metrics

### Quantitative
- **Memory Recall**: >90% relevant context retrieved
- **Response Time**: <500ms with memory
- **Learning Rate**: Preferences detected in 3 conversations
- **Improvement**: 20% fewer corrections after 10 conversations

### Qualitative
- **User Satisfaction**: Users notice memory
- **Personalization**: Responses feel tailored
- **Continuity**: Conversations flow naturally
- **Learning**: Agent adapts to user style

---

## Files to Create/Modify

### New Files
1. `torq_console/agents/enhanced_prince_flowers.py` - Main enhanced agent
2. `torq_console/agents/conversation_session.py` - Session tracking
3. `torq_console/agents/preference_learning.py` - Preference detection
4. `torq_console/agents/feedback_learning.py` - Feedback loops
5. `test_enhanced_prince_flowers.py` - Comprehensive tests

### Modified Files
1. `torq_console/agents/prince_flowers.py` - Add memory hooks
2. `torq_console/ui/web.py` - Integrate enhanced agent
3. `torq_console/core/chat_manager.py` - Session tracking

---

## Configuration

### config.yaml
```yaml
prince_flowers:
  memory:
    enabled: true
    backend: sqlite  # or postgresql for production
    db_path: ~/.torq/prince_flowers_memory.db

  learning:
    preference_detection: true
    feedback_learning: true
    auto_improve: true

  sessions:
    track_sessions: true
    session_timeout: 3600  # 1 hour
    max_session_messages: 100
```

---

## Next Steps

1. ✅ Plan complete
2. 🚧 Implement Step 1: Enhanced Prince Flowers
3. 🚧 Implement Step 2: Conversation tracking
4. 🚧 Implement Step 3: Preference learning
5. 🚧 Implement Step 4: Feedback loop
6. 🚧 Run comprehensive tests
7. 🚧 Deploy to production

---

**Status:** ✅ Plan complete, ready for implementation
**Branch:** main
**Next:** Begin Step 1 implementation
