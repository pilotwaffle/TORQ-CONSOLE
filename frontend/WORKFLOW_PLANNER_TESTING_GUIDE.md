# Workflow Planning Copilot - Testing Guide

## Overview

This guide covers testing the complete Workflow Planning Copilot v1 implementation - from backend API to frontend UX.

## Prerequisites

1. **Anthropic API Key** set in Railway environment variables
2. **Supabase** configured and connected
3. **Local dev server** or **Vercel deployment** running

---

## Backend API Testing

### 1. Check Planner Health

```bash
curl http://localhost:5173/api/workflow-planner/health
```

Expected response:
```json
{
  "status": "healthy",
  "module": "workflow_planner",
  "anthropic_configured": "true"
}
```

### 2. Generate Simple Workflow

```bash
curl -X POST http://localhost:5173/api/workflow-planner/draft \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Research AI market and create a summary"}'
```

Expected response structure:
```json
{
  "success": true,
  "draft": {
    "name": "AI Market Research Workflow",
    "description": "Researches AI trends and produces a strategic summary",
    "rationale": "This workflow starts with research, then analyzes findings...",
    "nodes": [
      {
        "node_key": "market_research",
        "name": "Market Research",
        "node_type": "agent",
        "agent_id": "research_agent",
        "depends_on": [],
        ...
      }
    ],
    "edges": [...],
    "limits": {...}
  },
  "generation_time_ms": 1180
}
```

### 3. Test Validation Error Cases

| Test | Prompt | Expected Result |
|------|--------|-----------------|
| Too short | `"Hi"` | 400 validation error |
| Empty string | `""` | 400 validation error |
| Complex request | Long nested workflow | Simplified 2-5 nodes |

---

## Frontend UX Testing

### Test 1: Prompt Builder Flow

1. Navigate to `http://localhost:5173/workflows/new`
2. Click **"Generate with AI"** tab
3. **Verify:**
   - [ ] Tab switches correctly
   - [ ] Textarea is focused
   - [ ] Character counter shows `0 / 4000`
   - [ ] "Minimum 10 characters" warning visible
   - [ ] Example prompts clickable
   - [ ] Generate button disabled

### Test 2: Example Prompt Selection

1. Click any example prompt button
2. **Verify:**
   - [ ] Textarea fills with example text
   - [ ] Character counter updates
   - [ ] "Ready to generate" appears in green
   - [ ] Generate button becomes enabled

### Test 3: Generation Loading States

1. Enter a prompt and click "Generate Workflow"
2. **Verify:**
   - [ ] Button shows spinner + "Generating workflow..."
   - [ ] Button is disabled
   - [ ] Textarea is disabled
   - [ ] Example buttons disabled
   - [ ] Loading message visible

### Test 4: Draft Preview Display

After generation completes:
1. **Verify:**
   - [ ] Tab switches to preview
   - [ ] Workflow name shown in header
   - [ ] Description visible
   - [ ] "Draft" badge displayed
   - [ ] Graph canvas renders nodes
   - [ ] Nodes positioned correctly
   - [ ] Edges connect nodes

### Test 5: Rationale Display

1. Click **"Details & Rationale"** tab
2. **Verify:**
   - [ ] Blue info box with rationale text
   - [ ] Rationale explains agent choices
   - [ ] Node list with agent IDs
   - [ ] Workflow limits displayed

### Test 6: Edit Before Save

1. Click **"Edit"** button
2. **Verify:**
   - [ ] Opens WorkflowEditor
   - [ ] Nodes pre-populated from draft
   - [ ] Edges pre-populated
   - [ ] Can modify any node
   - [ ] Can add/remove nodes

### Test 7: Save Workflow

1. Click **"Save Workflow"** button
2. **Verify:**
   - [ ] Creates workflow in database
   - [ ] Redirects to `/workflows`
   - [ ] New workflow visible in list
   - [ ] Status shows "active"

---

## End-to-End Test Scenarios

### Scenario 1: Simple Market Research

**Prompt:**
```
Research the AI infrastructure market and create a strategic summary
```

**Expected Result:**
- 3 nodes generated
- Agent sequence: `research_agent` → `workflow_agent` → `torq_prince_flowers`
- Graph is linear (no branches)
- Rationale explains the sequence

### Scenario 2: Competitor Analysis

**Prompt:**
```
Analyze top 5 AI competitors and generate a consulting report
```

**Expected Result:**
- 3-4 nodes generated
- Research then analysis then synthesis
- May include parallel research nodes

### Scenario 3: Complex Workflow

**Prompt:**
```
Research a company, analyze their products, compare with competitors, research market trends, and create an executive summary with recommendations
```

**Expected Result:**
- Simplified to 4-5 nodes (max)
- May combine some steps
- Clear rationale for simplification

---

## Validation Rules Testing

### Backend Validation

| Rule | Test Case | Expected Behavior |
|------|-----------|-------------------|
| Max nodes | Prompt requesting 15 steps | Returns simplified 4-5 node workflow |
| Unique keys | Duplicate node names | Auto-normalizes to unique keys |
| Valid agents | Invalid agent in LLM output | Validation error + retry |
| No cycles | Circular dependencies detected | Validation error + retry |
| Dependencies exist | Node depends on non-existent node | Validation error + retry |

### Frontend Validation

| Rule | Test Case | Expected Behavior |
|------|-----------|-------------------|
| Min length | 5 character prompt | Button disabled, warning shown |
| Max length | 5000 character prompt | Truncated to 4000 |
| Empty prompt | Just spaces | Button disabled |

---

## Performance Benchmarks

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Generation time | < 2 seconds | `generation_time_ms` in response |
| UI responsiveness | < 100ms | Feel of button clicks |
| Graph rendering | < 500ms | Time to show canvas |

---

## Error Handling Tests

### Network Errors

1. **Test:** Disconnect internet and click Generate
   - **Expected:** "Failed to generate workflow" error
   - **Expected:** Can retry after reconnecting

### API Errors

1. **Test:** Use invalid Anthropic key
   - **Expected:** 503 Service Unavailable
   - **Expected:** Clear error message

### LLM Errors

1. **Test:** Prompt that causes JSON parse failure
   - **Expected:** Automatic retry (2 attempts total)
   - **Expected:** Error message if both fail

---

## Browser Testing Matrix

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest | ✅ Test |
| Firefox | Latest | ✅ Test |
| Safari | Latest | ✅ Test |
| Edge | Latest | ✅ Test |

---

## Mobile Testing

| Screen Size | Test |
|-------------|------|
| Desktop (1920x1080) | Full layout |
| Laptop (1366x768) | Stacked layout |
| Tablet (768x1024) | Single column |
| Mobile (375x667) | Responsive check |

---

## Success Criteria

The feature passes when:

- ✅ User can enter natural language prompt
- ✅ Backend generates valid graph draft
- ✅ Frontend displays draft with rationale
- ✅ User understands why workflow was designed
- ✅ User can edit draft before saving
- ✅ Workflow saves successfully to database
- ✅ Generated workflow can be executed
- ✅ Error states are clear and recoverable

---

## Known Issues (v1)

- No conversation/refinement after generation
- No parallel node detection
- No workflow optimization suggestions
- Limited to agent nodes only

---

## Next Steps After Testing

1. **Gather user feedback** on prompt quality
2. **Improve system prompt** based on edge cases
3. **Add telemetry** for generation quality
4. **Consider v2 features** (conversation, optimization)

---

**Test Status:** ⏳ Ready for Testing
**Last Updated:** 2025-03-06
