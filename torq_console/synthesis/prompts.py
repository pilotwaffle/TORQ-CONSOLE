from __future__ import annotations

from typing import Any, Dict


def build_synthesis_prompt(synthesis_type: str, grouped_entries: Dict[str, Any], detector_output: Dict[str, Any]) -> str:
    return f"""You are TORQ's Reasoning Synthesis Engine.

Generate a grounded {synthesis_type} using only the workspace contents below.

Facts:
{grouped_entries.get('facts', [])}

Hypotheses:
{grouped_entries.get('hypotheses', [])}

Questions:
{grouped_entries.get('questions', [])}

Decisions:
{grouped_entries.get('decisions', [])}

Artifacts:
{grouped_entries.get('artifacts', [])}

Heuristic detector output:
{detector_output}

Rules:
- stay grounded in workspace entries
- do not invent facts
- clearly mark uncertainty
- output concise but useful strategic synthesis
"""
