#!/usr/bin/env python3
"""
Phase 5.1 Validation Helper Script

Automates validation execution and telemetry capture for Phase 5.1.
Usage: python scripts/run_validation.py --mission-id <uuid>
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from supabase import create_client, Client
    from torq_console.dependencies import get_supabase_client
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Ensure torq_console environment is activated.")
    sys.exit(1)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationRunner:
    """Runs validation checks and captures telemetry."""

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """Initialize validation runner."""
        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
        else:
            self.supabase = get_supabase_client()

    def reset_validation_environment(self) -> Dict[str, Any]:
        """Reset validation tables for clean baseline."""
        logger.info("Resetting validation environment...")

        # Note: This uses direct SQL via RPC if available, otherwise manual
        result = {
            "missions_cleared": 0,
            "validation_reset": False,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Clear mission-related tables
            self.supabase.table("mission_handoffs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.supabase.table("workstream_states").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.supabase.table("mission_events").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.supabase.table("mission_edges").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.supabase.table("mission_nodes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.supabase.table("mission_graphs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.supabase.table("missions").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.supabase.table("validation_telemetry").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.supabase.table("validation_results").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

            result["validation_reset"] = True
            logger.info("✓ Validation environment reset complete")

        except Exception as e:
            logger.error(f"Failed to reset environment: {e}")
            result["error"] = str(e)

        return result

    def get_baseline_state(self) -> Dict[str, int]:
        """Capture baseline state before validation."""
        logger.info("Capturing baseline state...")

        tables = [
            "missions", "mission_nodes", "mission_edges",
            "mission_events", "mission_handoffs", "workstream_states",
            "validation_telemetry", "validation_results"
        ]

        baseline = {}
        for table in tables:
            try:
                result = self.supabase.table(table).select("*", count="exact").limit(0).execute()
                baseline[table] = result.count if hasattr(result, 'count') else 0
            except Exception as e:
                logger.warning(f"Could not count {table}: {e}")
                baseline[table] = -1

        logger.info(f"Baseline: {json.dumps(baseline, indent=2)}")
        return baseline

    def create_mission(self, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a validation mission."""
        logger.info(f"Creating mission: {mission_data.get('title')}")

        result = self.supabase.table("missions").insert({
            "title": mission_data["title"],
            "mission_type": mission_data["mission_type"],
            "objective": mission_data["objective"],
            "context": mission_data.get("context", {}),
            "constraints": mission_data.get("constraints"),
            "reasoning_strategy": mission_data.get("reasoning_strategy"),
            "status": "draft"
        }).execute()

        if result.data:
            mission_id = result.data[0]["id"]
            logger.info(f"✓ Mission created: {mission_id}")
            return {"mission_id": mission_id, "status": "created"}
        else:
            logger.error("Failed to create mission")
            return {"status": "failed", "error": "No data returned"}

    def get_mission_status(self, mission_id: str) -> Dict[str, Any]:
        """Get current mission status and metrics."""
        try:
            # Get mission
            mission_result = self.supabase.table("missions").select("*").eq("id", mission_id).single().execute()
            mission = mission_result.data if mission_result.data else None

            if not mission:
                return {"error": "Mission not found"}

            # Get nodes
            nodes_result = self.supabase.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
            nodes = nodes_result.data if nodes_result.data else []

            # Get events
            events_result = self.supabase.table("mission_events").select("*").eq("mission_id", mission_id).execute()
            events = events_result.data if events_result.data else []

            # Get handoffs
            handoffs_result = self.supabase.table("mission_handoffs").select("*").eq("mission_id", mission_id).execute()
            handoffs = handoffs_result.data if handoffs_result.data else []

            # Get workstreams
            ws_result = self.supabase.table("workstream_states").select("*").eq("mission_id", mission_id).execute()
            workstreams = ws_result.data if ws_result.data else []

            # Count by status
            node_status_counts = {}
            for node in nodes:
                status = node.get("status", "unknown")
                node_status_counts[status] = node_status_counts.get(status, 0) + 1

            # Count by event type
            event_type_counts = {}
            for event in events:
                event_type = event.get("event_type", "unknown")
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

            return {
                "mission_id": mission_id,
                "mission_status": mission.get("status"),
                "mission_title": mission.get("title"),
                "node_counts": {
                    "total": len(nodes),
                    "by_status": node_status_counts
                },
                "event_counts": {
                    "total": len(events),
                    "by_type": event_type_counts
                },
                "handoff_count": len(handoffs),
                "workstream_count": len(workstreams),
                "workstream_status": {
                    ws.get("workstream_id"): ws.get("status")
                    for ws in workstreams
                }
            }

        except Exception as e:
            logger.error(f"Error getting mission status: {e}")
            return {"error": str(e)}

    def capture_telemetry(self, mission_id: str, section: str = None) -> Dict[str, Any]:
        """Capture validation telemetry for a mission."""
        logger.info(f"Capturing telemetry for mission {mission_id}...")

        status = self.get_mission_status(mission_id)

        if "error" in status:
            return status

        telemetry = {
            "mission_id": mission_id,
            "mission_type": status.get("mission_title", "unknown"),
            "node_count": status["node_counts"]["total"],
            "execution_time_seconds": 0,  # Would be calculated from timestamps
            "nodes_completed": status["node_counts"]["by_status"].get("completed", 0),
            "nodes_failed": status["node_counts"]["by_status"].get("failed", 0),
            "handoff_count": status["handoff_count"],
            "event_count": status["event_counts"]["total"],
            "checkpoint_count": 0,  # Would be queried from checkpoints table
            "workstream_count": status["workstream_count"],
            "workstreams_blocked": len([
                ws for ws_status in status["workstream_status"].values()
                if ws_status == "blocked"
            ]),
            "validation_section": section,
            "notes": f"Captured at {datetime.now().isoformat()}"
        }

        # Store telemetry
        try:
            result = self.supabase.table("validation_telemetry").insert(telemetry).execute()
            if result.data:
                telemetry["id"] = result.data[0]["id"]
                logger.info(f"✓ Telemetry captured: {telemetry['id']}")
        except Exception as e:
            logger.warning(f"Failed to store telemetry: {e}")

        return telemetry

    def record_check_result(
        self,
        section: str,
        check_number: str,
        check_name: str,
        status: str,
        notes: str = None,
        evidence: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Record a validation check result."""
        check_data = {
            "section": section,
            "check_number": check_number,
            "check_name": check_name,
            "status": status,
            "result_notes": notes,
            "evidence_result": evidence or {},
            "executed_at": datetime.now().isoformat()
        }

        try:
            result = self.supabase.table("validation_results").insert(check_data).execute()
            if result.data:
                logger.info(f"✓ Check recorded: {section}.{check_number} = {status}")
                return {"status": "recorded", "id": result.data[0]["id"]}
        except Exception as e:
            logger.error(f"Failed to record check: {e}")
            return {"status": "failed", "error": str(e)}

        return check_data

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get overall validation summary."""
        try:
            # Get summary from view or aggregate
            results = self.supabase.table("validation_results").select("*").execute()

            summary = {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "pending": 0,
                "by_section": {}
            }

            for result in (results.data or []):
                summary["total_checks"] += 1
                status = result.get("status", "pending")
                section = result.get("section", "unknown")

                if section not in summary["by_section"]:
                    summary["by_section"][section] = {"passed": 0, "failed": 0, "pending": 0, "total": 0}

                summary["by_section"][section][status] = summary["by_section"][section].get(status, 0) + 1
                summary["by_section"][section]["total"] += 1

                if status == "passed":
                    summary["passed"] += 1
                elif status == "failed":
                    summary["failed"] += 1
                else:
                    summary["pending"] += 1

            return summary

        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return {"error": str(e)}


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Phase 5.1 Validation Runner")
    subparsers = parser.add_subparsers(dest="command", help="Validation commands")

    # Reset command
    subparsers.add_parser("reset", help="Reset validation environment")

    # Baseline command
    subparsers.add_parser("baseline", help="Capture baseline state")

    # Create mission command
    create_parser = subparsers.add_parser("create", help="Create validation mission")
    create_parser.add_argument("--title", required=True, help="Mission title")
    create_parser.add_argument("--type", required=True, help="Mission type")
    create_parser.add_argument("--objective", required=True, help="Mission objective")
    create_parser.add_argument("--context", type=json.loads, default={}, help="Mission context JSON")

    # Status command
    status_parser = subparsers.add_parser("status", help="Get mission status")
    status_parser.add_argument("--mission-id", required=True, help="Mission UUID")

    # Telemetry command
    telemetry_parser = subparsers.add_parser("telemetry", help="Capture telemetry")
    telemetry_parser.add_argument("--mission-id", required=True, help="Mission UUID")
    telemetry_parser.add_argument("--section", help="Validation section")

    # Check command
    check_parser = subparsers.add_parser("check", help="Record validation check")
    check_parser.add_argument("--section", required=True, help="Section letter")
    check_parser.add_argument("--number", required=True, help="Check number (e.g., A1)")
    check_parser.add_argument("--name", required=True, help="Check name")
    check_parser.add_argument("--status", required=True, choices=["passed", "failed", "skipped"], help="Check status")
    check_parser.add_argument("--notes", help="Additional notes")

    # Summary command
    subparsers.add_parser("summary", help="Get validation summary")

    args = parser.parse_args()

    # Initialize runner
    runner = ValidationRunner()

    if args.command == "reset":
        result = runner.reset_validation_environment()
        print(json.dumps(result, indent=2))

    elif args.command == "baseline":
        baseline = runner.get_baseline_state()
        print(json.dumps(baseline, indent=2))

    elif args.command == "create":
        result = runner.create_mission({
            "title": args.title,
            "mission_type": args.type,
            "objective": args.objective,
            "context": args.context
        })
        print(json.dumps(result, indent=2))

    elif args.command == "status":
        status = runner.get_mission_status(args.mission_id)
        print(json.dumps(status, indent=2))

    elif args.command == "telemetry":
        telemetry = runner.capture_telemetry(args.mission_id, args.section)
        print(json.dumps(telemetry, indent=2))

    elif args.command == "check":
        result = runner.record_check_result(
            section=args.section,
            check_number=args.number,
            check_name=args.name,
            status=args.status,
            notes=args.notes
        )
        print(json.dumps(result, indent=2))

    elif args.command == "summary":
        summary = runner.get_validation_summary()
        print(json.dumps(summary, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
