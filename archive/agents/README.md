# Archived Prince Flowers Agents

**Status Archived:** 2025-12-14
**Reason:** Code consolidation - TORQ Console had 8+ Prince Flowers agent variants causing confusion and code duplication.
**Canonical Agent:** `torq_console/agents/torq_prince_flowers.py` (200,529 lines - primary implementation)

## Archived Files

### Core Agent Variants
1. `glm_prince_flowers.py` - GLM model integration variant
2. `marvin_prince_flowers.py` - Marvin integration variant
3. `enhanced_prince_flowers.py` - Enhanced version (12,038 lines)
4. `enhanced_prince_flowers_v2.py` - Enhanced version 2 (44,571 lines)
5. `prince_flowers_enhanced.py` - Another enhanced variant

### Integration Variants
6. `memory_enhanced_prince_flowers.py` - Memory-enhanced variant
7. `prince_flowers_evaluator.py` - Evaluator variant
8. `zep_enhanced_prince_flowers.py` - Zep memory integration

### Test Files
9. `test_enhanced_prince_flowers.py` - Tests for enhanced variants
10. `test_enhanced_prince_flowers_structure.py` - Structure tests

## Notes

- These variants represented different integration approaches and experimental features
- Functionality has been consolidated into the canonical `torq_prince_flowers.py`
- Total archived code: ~60,000+ lines of duplicate/variant code
- This reduces codebase complexity and maintenance burden

## Recovery

If needed for reference:
- All files are preserved in this archive directory
- The canonical agent contains the most complete implementation
- Specific features from variants can be ported if required