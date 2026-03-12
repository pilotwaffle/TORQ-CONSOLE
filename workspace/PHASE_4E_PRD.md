# TORQ Console — Phase 4E PRD
# Reasoning Synthesis Engine

Version: 1.0
Status: Planning Ready
Phase: 4E
Priority: Strategic High

## Objective
Implement the Reasoning Synthesis Engine so TORQ can convert raw Shared Cognitive Workspace entries into strategic insight.

## Purpose
Phase 4D enables agents to write:
- facts
- hypotheses
- questions
- decisions
- artifacts

Phase 4E turns those entries into:
- summaries
- insights
- contradictions
- next actions
- executive briefs

## Scope
Included:
- synthesis service
- synthesis artifact schema
- workspace-level summary generation
- contradiction detection
- unresolved question prioritization
- recommended next actions
- executive brief output
- frontend synthesis panels/cards
- API endpoints for generation and retrieval

Excluded:
- autonomous action-taking
- automatic policy mutation
- cross-workspace synthesis in v1
- background scheduled synthesis in v1

## Key Use Cases
1. Workflow execution review
2. Planning Copilot explainability
3. Multi-agent investigation synthesis
4. Executive briefing output

## Functional Requirements
- generate synthesis on demand
- persist synthesis artifacts
- retrieve latest synthesis by type
- detect contradiction candidates
- prioritize unresolved questions
- suggest next actions
- support executive brief generation
- expose synthesis in UI
- avoid mutating raw entries
- support regeneration/versioning

## Synthesis Types
- summary
- insights
- risks
- contradictions
- next_actions
- executive_brief

## Testing Gates
1. summary generation
2. multi-type synthesis
3. contradiction detection
4. versioning
5. UI visibility
6. no raw entry mutation

## Acceptance Criteria
- synthesis artifacts can be generated on demand
- results are stored in workspace_syntheses
- latest synthesis can be retrieved by type
- contradictions and next actions are supported
- UI displays synthesis outputs
- versioning works
- runtime tests pass
