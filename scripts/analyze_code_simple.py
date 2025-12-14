#!/usr/bin/env python3
"""
Simple Code Analysis Tool

Analyzes TORQ Console codebase for patterns and file statistics.
"""

import os
from collections import defaultdict, Counter
from pathlib import Path

def analyze_codebase():
    """Analyze the TORQ Console codebase."""
    root_dir = Path(__file__).parent.parent

    print("\n=== TORQ Console Code Analysis ===")

    # Count files by directory
    dirs = defaultdict(int)
    python_files = []
    total_lines = 0
    large_files = []

    for root, dirs_list, files in os.walk(root_dir):
        # Skip certain directories
        dirs_list[:] = [d for d in dirs_list if not d.startswith('.')
                       and d not in ['__pycache__', 'node_modules', '.git', 'archive', 'reports']]

        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_dir)

                # Count lines
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())

                python_files.append((str(rel_path), lines))
                total_lines += lines

                # Track directory
                parent_dir = rel_path.parent
                dirs[str(parent_dir)] += 1

                if lines > 500:
                    large_files.append((str(rel_path), lines))

    # Sort files by size
    python_files.sort(key=lambda x: x[1], reverse=True)

    print(f"\nTotal Python files: {len(python_files)}")
    print(f"Total lines of code: {total_lines:,}")
    print(f"Average file size: {total_lines // len(python_files) if python_files else 0} lines")

    print(f"\nTop 20 largest files:")
    for i, (file, lines) in enumerate(python_files[:20], 1):
        print(f"  {i:2d}. {file:<60} {lines:6,} lines")

    print(f"\nFiles by directory:")
    for dir_path, count in sorted(dirs.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dir_path:<50} {count:3} files")

    # Analyze patterns
    print("\n=== Pattern Analysis ===")

    # Agent files
    agent_files = [f for f in python_files if 'agent' in f[0].lower()]
    print(f"\nAgent-related files: {len(agent_files)}")
    if agent_files:
        print("  Largest agent files:")
        for f, l in sorted(agent_files, key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {f} ({l} lines)")

    # UI files
    ui_files = [f for f in python_files if 'ui' in f[0].lower()]
    print(f"\nUI-related files: {len(ui_files)}")
    if ui_files:
        print("  Largest UI files:")
        for f, l in sorted(ui_files, key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {f} ({l} lines)")

    # Utility files
    util_files = [f for f in python_files if 'util' in f[0].lower()]
    print(f"\nUtility files: {len(util_files)}")

    # Test files
    test_files = [f for f in python_files if 'test' in f[0].lower()]
    print(f"\nTest files: {len(test_files)}")

    # Files over 1000 lines
    huge_files = [f for f in python_files if f[1] > 1000]
    print(f"\nFiles over 1000 lines: {len(huge_files)}")

    # Duplication opportunities
    print("\n=== Duplication Opportunities ===")

    # Check for similar naming patterns
    patterns = {
        'Agent': [f for f in python_files if 'Agent' in f[0]],
        'Manager': [f for f in python_files if 'Manager' in f[0]],
        'Handler': [f for f in python_files if 'Handler' in f[0]],
        'Service': [f for f in python_files if 'Service' in f[0]],
        'Client': [f for f in python_files if 'Client' in f[0]],
        'Engine': [f for f in python_files if 'Engine' in f[0]],
        'Orchestrator': [f for f in python_files if 'Orchestrator' in f[0]],
    }

    for pattern, files in patterns.items():
        if len(files) > 3:
            print(f"\n{pattern} files ({len(files)}):")
            total = sum(f[1] for f in files)
            print(f"  Total lines: {total:,}")
            print(f"  Could potentially consolidate into 2-3 modules")

    # Generate recommendations
    print("\n=== Recommendations ===")

    recommendations = []

    if len(agent_files) > 10:
        recommendations.append(f"1. CONSOLIDATE AGENTS: {len(agent_files)} agent files could be reduced to 3-5 core modules")

    if len(util_files) > 5:
        recommendations.append(f"2. MERGE UTILS: {len(util_files)} utility modules likely have overlapping functionality")

    if len(huge_files) > 5:
        recommendations.append(f"3. SPLIT LARGE FILES: {len(huge_files)} files over 1000 lines should be split")

    if len(test_files) > 20:
        recommendations.append(f"4. ORGANIZE TESTS: {len(test_files)} test files - create shared fixtures")

    # Calculate potential savings
    potential_savings = 0
    if len(agent_files) > 10:
        potential_savings += len(agent_files) * 0.6  # 60% reduction in agents
    if len(util_files) > 5:
        potential_savings += len(util_files) * 0.4  # 40% reduction in utils
    if len(huge_files) > 5:
        potential_savings += len(huge_files) * 0.2  # 20% reduction from splitting

    recommendations.append(f"5. ESTIMATED SAVINGS: {potential_savings * 20:.0f}K lines (20% of codebase)")

    for rec in recommendations:
        print(f"\n{rec}")

    # Save detailed analysis
    analysis_data = {
        "summary": {
            "total_files": len(python_files),
            "total_lines": total_lines,
            "large_files": len(large_files),
            "huge_files": len(huge_files)
        },
        "categories": {
            "agents": agent_files,
            "ui": ui_files,
            "utils": util_files,
            "tests": test_files
        },
        "patterns": {k: v for k, v in patterns.items() if len(v) > 3},
        "largest_files": python_files[:50],
        "recommendations": recommendations
    }

    import json
    output_path = root_dir / "reports" / "code_analysis.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(analysis_data, f, indent=2, default=str)

    print(f"\nDetailed analysis saved to: {output_path}")

    return analysis_data

if __name__ == "__main__":
    analyze_codebase()