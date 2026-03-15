"""TORQ Layer 13 - Prioritization CLI

Command-line interface for running economic prioritization.

Usage:
    python -m torq_console.layer13.economic.run_prioritization --budget 1000 --missions data/missions.json
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from . import (
    create_allocation_engine,
    create_evaluation_engine,
    create_opportunity_cost_model,
    create_prioritization_engine,
)
from ..models import (
    EconomicConfiguration,
    FederationResult,
    MissionProposal,
    ResourceConstraints,
)


async def main():
    """Main entry point for prioritization CLI."""
    parser = argparse.ArgumentParser(
        description="TORQ Layer 13 Economic Intelligence - Prioritization"
    )
    parser.add_argument(
        "--budget",
        type=float,
        required=True,
        help="Total budget available for allocation",
    )
    parser.add_argument(
        "--missions",
        type=str,
        required=True,
        help="JSON file containing mission proposals",
    )
    parser.add_argument(
        "--constraints",
        type=str,
        help="JSON file containing resource constraints",
    )
    parser.add_argument(
        "--federation",
        type=str,
        help="JSON file containing federation results",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for allocation results",
    )
    parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Load proposals
    with open(args.missions) as f:
        mission_data = json.load(f)

    proposals = [
        MissionProposal(**p) for p in mission_data.get("missions", [])
    ]

    # Load constraints
    if args.constraints:
        with open(args.constraints) as f:
            constraints_data = json.load(f)
        constraints = ResourceConstraints(**constraints_data)
        constraints.total_budget = args.budget
        constraints.budget_remaining = args.budget
    else:
        constraints = ResourceConstraints(
            total_budget=args.budget,
            budget_remaining=args.budget,
        )

    # Load federation results
    federation_results = {}
    if args.federation:
        with open(args.federation) as f:
            federation_data = json.load(f)
        for mission_id, fr_data in federation_data.items():
            federation_results[mission_id] = FederationResult(**fr_data)

    # Create engines
    evaluation_engine = create_evaluation_engine()
    prioritization_engine = create_prioritization_engine()
    allocation_engine = create_allocation_engine()
    opportunity_model = create_opportunity_cost_model()

    # Build costs dictionary
    costs = {p.mission_id: p.estimated_cost for p in proposals}

    if args.verbose:
        print("\n" + "=" * 60)
        print("Layer 13 Economic Prioritization")
        print("=" * 60)
        print(f"\nBudget: {args.budget:.2f}")
        print(f"Missions: {len(proposals)}")
        print(f"Constraints: {args.constraints if args.constraints else 'default'}")

    # Layer 1-3: Evaluate proposals
    if args.verbose:
        print("\nRunning Layers 1-3: Evaluation...")

    scores = []
    for proposal in proposals:
        federation_result = federation_results.get(proposal.mission_id)
        score = await evaluation_engine.evaluate_proposal(
            proposal,
            constraints,
            federation_result,
        )
        scores.append(score)

        if args.verbose:
            if score.eligible:
                print(f"  {score.candidate_id}: base_value={score.base_value:.2f}, "
                      f"quality_adjusted={score.quality_adjusted_value:.2f}")
            else:
                print(f"  {score.candidate_id}: REJECTED - {score.rejection_reason}")

    # Layer 4: Rank by efficiency
    if args.verbose:
        print("\nRunning Layer 4: Prioritization...")

    ranked = await prioritization_engine.rank_by_efficiency(
        scores,
        constraints,
        costs,
    )

    if args.verbose:
        print("  Ranking by efficiency:")
        for i, score in enumerate(ranked, 1):
            if score.eligible:
                print(f"    {i}. {score.candidate_id}: efficiency={score.efficiency:.4f}")

    # Layer 5: Allocate budget
    if args.verbose:
        print("\nRunning Layer 5: Allocation...")

    allocation = await allocation_engine.allocate_budget(
        ranked,
        constraints,
        costs,
    )

    # Calculate opportunity costs
    funded = [s for s in ranked if s.candidate_id in allocation.funded_mission_ids]
    rejected = [s for s in ranked if s.candidate_id not in allocation.funded_mission_ids]

    opportunity_costs = await opportunity_model.calculate_opportunity_costs(
        funded,
        rejected,
        constraints.total_budget,
        costs,
    )

    # Build result output
    result = {
        "funded_mission_ids": allocation.funded_mission_ids,
        "funded_total_cost": allocation.funded_total_cost,
        "funded_total_value": allocation.funded_total_value,
        "queued_mission_ids": allocation.queued_mission_ids,
        "queued_total_cost": allocation.queued_total_cost,
        "rejected_mission_ids": allocation.rejected_mission_ids,
        "rejected_reasons": allocation.rejected_reasons,
        "budget_utilization": allocation.budget_utilization,
        "remaining_budget": allocation.remaining_budget,
        "allocation_efficiency": allocation.allocation_efficiency,
        "regret_score": allocation.regret_score,
        "opportunity_costs": {
            mission_id: {
                "rejected_mission_id": oc.rejected_mission_id,
                "rejected_mission_value": oc.rejected_mission_value,
                "best_accepted_alternative_id": oc.best_accepted_alternative_id,
                "best_accepted_alternative_value": oc.best_accepted_alternative_value,
                "opportunity_cost": oc.opportunity_cost,
                "opportunity_cost_ratio": oc.opportunity_cost_ratio,
                "strategic_impact": oc.strategic_impact,
            }
            for mission_id, oc in opportunity_costs.items()
        },
    }

    if args.verbose:
        print("\nResults:")
        print(f"  Funded: {', '.join(allocation.funded_mission_ids)} "
              f"(cost: {allocation.funded_total_cost:.2f})")
        if allocation.queued_mission_ids:
            print(f"  Queued: {', '.join(allocation.queued_mission_ids)} "
                  f"(cost: {allocation.queued_total_cost:.2f}, doesn't fit)")
        if allocation.rejected_mission_ids:
            print(f"  Rejected: {', '.join(allocation.rejected_mission_ids)}")
        print(f"\n  Budget Utilization: {allocation.budget_utilization*100:.1f}%")
        print(f"  Remaining Budget: {allocation.remaining_budget:.2f}")
        print(f"  Allocation Efficiency: {allocation.allocation_efficiency:.2f} value/dollar")

    # Save output
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nOutput written to: {args.output}")

    elif args.format == "json":
        print("\n" + json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
