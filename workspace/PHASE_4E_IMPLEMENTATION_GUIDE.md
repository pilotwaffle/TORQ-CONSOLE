# TORQ Console — Phase 4E Implementation Guide
# Reasoning Synthesis Engine

## Build Order
1. create synthesis schema
2. create synthesis models
3. implement synthesis service
4. add API endpoints
5. integrate workspace retrieval
6. add contradiction detection pass
7. add frontend synthesis components
8. validate in execution/workspace UI
9. add tests

## Migration
Create:
- `migrations/005_workspace_syntheses.sql`

## Backend Files
Create:
- `torq_console/synthesis/__init__.py`
- `torq_console/synthesis/models.py`
- `torq_console/synthesis/service.py`
- `torq_console/synthesis/api.py`
- `torq_console/synthesis/detectors.py`
- `torq_console/synthesis/prompts.py`

## Frontend Files
Create:
- `frontend/src/features/synthesis/api/synthesisTypes.ts`
- `frontend/src/features/synthesis/api/synthesisApi.ts`
- `frontend/src/features/synthesis/hooks/useSynthesis.ts`
- `frontend/src/features/synthesis/components/SummaryCard.tsx`
- `frontend/src/features/synthesis/components/InsightsCard.tsx`
- `frontend/src/features/synthesis/components/RisksCard.tsx`
- `frontend/src/features/synthesis/components/NextActionsCard.tsx`
- `frontend/src/features/synthesis/components/ExecutiveBriefCard.tsx`
- `frontend/src/features/synthesis/components/SynthesisPanel.tsx`

## Validation Flow
- generate summary from populated workspace
- generate multi-type synthesis
- validate contradiction candidates
- regenerate and confirm version increment
- confirm UI rendering in execution page

## Exit Criteria
- migration applied
- synthesis endpoints operational
- latest retrieval works
- versioning works
- summary visible in UI
- contradictions and next actions supported
- no mutation of raw workspace entries
