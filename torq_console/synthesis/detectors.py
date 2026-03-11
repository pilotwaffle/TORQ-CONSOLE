from __future__ import annotations

from typing import Dict, List


def detect_unresolved_questions(grouped_entries: Dict[str, List[dict]]) -> List[dict]:
    questions = grouped_entries.get("questions", [])
    unresolved = []
    for q in questions:
        if q.get("status") != "resolved":
            unresolved.append({
                "memory_id": q.get("memory_id"),
                "content": q.get("content"),
                "severity": "medium",
            })
    return unresolved


def detect_contradiction_candidates(grouped_entries: Dict[str, List[dict]]) -> List[dict]:
    facts = grouped_entries.get("facts", [])
    hypotheses = grouped_entries.get("hypotheses", [])
    candidates = []

    fact_texts = [str(f.get("content", {})).lower() for f in facts]
    for h in hypotheses:
        h_text = str(h.get("content", {})).lower()
        for idx, f_text in enumerate(fact_texts):
            if ("not" in h_text and "is" in f_text) or ("increase" in h_text and "decrease" in f_text):
                candidates.append({
                    "hypothesis_id": h.get("memory_id"),
                    "fact_index": idx,
                    "reason": "Potential semantic conflict detected heuristically",
                    "severity": "low",
                })
    return candidates


def suggest_next_actions(grouped_entries: Dict[str, List[dict]]) -> List[dict]:
    actions = []
    unresolved = detect_unresolved_questions(grouped_entries)
    contradictions = detect_contradiction_candidates(grouped_entries)
    decisions = grouped_entries.get("decisions", [])
    artifacts = grouped_entries.get("artifacts", [])

    if unresolved:
        actions.append({
            "action": "Resolve the highest-priority open questions",
            "reason": f"{len(unresolved)} unresolved questions remain.",
            "priority": "high",
        })
    if contradictions:
        actions.append({
            "action": "Validate conflicting reasoning entries",
            "reason": f"{len(contradictions)} contradiction candidates detected.",
            "priority": "high",
        })
    if artifacts and not decisions:
        actions.append({
            "action": "Review artifacts and produce a decision",
            "reason": "Artifacts exist but no decisions have been recorded.",
            "priority": "medium",
        })
    if not actions:
        actions.append({
            "action": "Review workspace and generate executive brief",
            "reason": "Workspace is coherent and ready for summary.",
            "priority": "medium",
        })
    return actions
