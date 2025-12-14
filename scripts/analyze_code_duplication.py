#!/usr/bin/env python3
"""
Code Duplication Analysis Tool

Analyzes TORQ Console codebase for duplication patterns and identifies
opportunities for code reduction. Target: 50% code reduction.
"""

import ast
import os
import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import json

class CodeDuplicationAnalyzer:
    """Analyzes code duplication patterns in the TORQ Console codebase."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.python_files: List[Path] = []
        self.file_analysis: Dict[str, Dict] = {}
        self.duplication_report: Dict[str, Any] = {
            "summary": {},
            "patterns": {},
            "recommendations": [],
            "files_to_consolidate": [],
            "duplicate_code_blocks": [],
            "similar_functions": [],
            "repeated_imports": []
        }

    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive code duplication analysis."""
        print("\n🔍 Analyzing TORQ Console Code Duplication")
        print("=" * 50)

        # Collect all Python files
        self._collect_python_files()
        print(f"Found {len(self.python_files)} Python files")

        # Analyze each file
        print("\n📊 Analyzing files...")
        for file_path in self.python_files:
            self._analyze_file(file_path)

        # Identify patterns
        print("\n🔄 Identifying duplication patterns...")
        self._find_import_patterns()
        self._find_function_patterns()
        self._find_class_patterns()
        self._find_duplicate_blocks()
        self._analyze_file_sizes()

        # Generate recommendations
        print("\n💡 Generating recommendations...")
        self._generate_recommendations()

        # Create summary
        self._create_summary()

        return self.duplication_report

    def _collect_python_files(self):
        """Collect all Python files in the codebase."""
        for root, dirs, files in os.walk(self.root_dir):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and
                       d not in ['__pycache__', 'node_modules', '.git', 'archive']]

            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    # Calculate relative path
                    rel_path = file_path.relative_to(self.root_dir)
                    self.python_files.append(rel_path)

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file for patterns."""
        full_path = self.root_dir / file_path

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                print(f"⚠️  Could not parse {file_path}")
                return

            # Analyze imports
            imports = self._extract_imports(tree)

            # Analyze functions and classes
            functions = self._extract_functions(tree)
            classes = self._extract_classes(tree)

            # Calculate metrics
            analysis = {
                "path": str(file_path),
                "lines": len(lines),
                "non_empty_lines": len([l for l in lines if l.strip()]),
                "imports": imports,
                "functions": functions,
                "classes": classes,
                "complexity": self._calculate_complexity(tree),
                "duplicates": []
            }

            self.file_analysis[str(file_path)] = analysis

        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")

    def _extract_imports(self, tree: ast.AST) -> List[Dict]:
        """Extract import statements from AST."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append({
                        "type": "from_import",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno
                    })

        return imports

    def _extract_functions(self, tree: ast.AST) -> List[Dict]:
        """Extract function definitions from AST."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": len(node.args.args),
                    "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                })

        return functions

    def _extract_classes(self, tree: ast.AST) -> List[Dict]:
        """Extract class definitions from AST."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": len(methods),
                    "bases": [self._get_name(base) for base in node.bases]
                })

        return classes

    def _get_name(self, node) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)

    def _calculate_complexity(self, tree: ast.AST) -> Dict:
        """Calculate simple complexity metrics."""
        complexity = {
            "cyclomatic": 0,
            "functions": 0,
            "classes": 0,
            "imports": 0
        }

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity["cyclomatic"] += 1
            elif isinstance(node, ast.FunctionDef):
                complexity["functions"] += 1
            elif isinstance(node, ast.ClassDef):
                complexity["classes"] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                complexity["imports"] += 1

        complexity["cyclomatic"] += 1  # Base complexity

        return complexity

    def _find_import_patterns(self):
        """Find common import patterns."""
        import_counter = Counter()

        for file_path, analysis in self.file_analysis.items():
            for imp in analysis["imports"]:
                if imp["type"] == "import":
                    import_counter[imp["module"]] += 1
                elif imp["type"] == "from_import":
                    import_counter[f"{imp['module']}.{imp['name']}"] += 1

        # Find frequently used imports
        common_imports = import_counter.most_common(20)
        self.duplication_report["repeated_imports"] = [
            {"import": imp, "count": count} for imp, count in common_imports if count > 3
        ]

    def _find_function_patterns(self):
        """Find similar function names and patterns."""
        function_names = []
        function_signatures = []

        for file_path, analysis in self.file_analysis.items():
            for func in analysis["functions"]:
                function_names.append(func["name"])
                # Create a simple signature pattern
                signature = f"{func['name']}_{func['args']}args"
                if func["is_async"]:
                    signature = f"async_{signature}"
                function_signatures.append(signature)

        # Find similar names
        name_counter = Counter(function_names)
        similar_names = [
            {"name": name, "count": count}
            for name, count in name_counter.items()
            if count > 2 and not name.startswith('_')
        ]

        # Find common patterns (e.g., get_, set_, create_, etc.)
        patterns = defaultdict(int)
        for name in function_names:
            for prefix in ["get_", "set_", "create_", "init_", "run_", "exec_", "handle_"]:
                if name.startswith(prefix):
                    patterns[prefix] += 1
                    break

        self.duplication_report["similar_functions"] = {
            "duplicate_names": similar_names,
            "common_patterns": dict(patterns)
        }

    def _find_class_patterns(self):
        """Find similar class patterns."""
        class_names = []

        for file_path, analysis in self.file_analysis.items():
            for cls in analysis["classes"]:
                class_names.append(cls["name"])

        # Find common class name patterns
        patterns = defaultdict(int)
        for name in class_names:
            for suffix in ["Agent", "Manager", "Handler", "Service", "Client", "Engine", "Orchestrator"]:
                if name.endswith(suffix):
                    patterns[suffix] += 1
                    break

        self.duplication_report["patterns"]["class_suffixes"] = dict(patterns)

    def _find_duplicate_blocks(self):
        """Find duplicate code blocks using simple line-based detection."""
        # This is a simplified version - a production tool would use more sophisticated algorithms
        line_blocks = defaultdict(list)

        for file_path, analysis in self.file_analysis.items():
            if analysis["lines"] > 100:  # Only check larger files
                with open(self.root_dir / file_path, 'r') as f:
                    lines = f.readlines()

                # Look for 5-line blocks (simplified)
                for i in range(len(lines) - 4):
                    block = ''.join(lines[i:i+5]).strip()
                    if len(block) > 50:  # Skip very small blocks
                        # Normalize the block for comparison
                        normalized = re.sub(r'\s+', ' ', block)
                        line_blocks[normalized].append({
                            "file": file_path,
                            "start_line": i + 1,
                            "block": block
                        })

        # Find blocks that appear multiple times
        duplicates = [
            {"block": block[:50] + "...", "count": len(occurrences), "locations": occurrences[:3]}
            for block, occurrences in line_blocks.items()
            if len(occurrences) > 1
        ]

        self.duplication_report["duplicate_code_blocks"] = duplicates[:10]  # Top 10

    def _analyze_file_sizes(self):
        """Analyze file sizes to identify candidates for consolidation."""
        files_by_size = sorted(
            [(path, analysis["lines"]) for path, analysis in self.file_analysis.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # Categorize files
        large_files = [(path, size) for path, size in files_by_size if size > 500]
        medium_files = [(path, size) for path, size in files_by_size if 100 < size <= 500]
        small_files = [(path, size) for path, size in files_by_size if size <= 100]

        self.duplication_report["files_by_size"] = {
            "large": large_files,
            "medium": medium_files,
            "small": small_files
        }

    def _generate_recommendations(self):
        """Generate recommendations based on analysis."""
        recommendations = []

        # Check for agent consolidation
        agent_files = [p for p in self.file_analysis.keys() if 'agent' in p.lower()]
        if len(agent_files) > 5:
            recommendations.append({
                "category": "Agent Consolidation",
                "priority": "HIGH",
                "description": f"Found {len(agent_files)} agent-related files - consider consolidating into fewer, more focused modules",
                "savings": "30-40% code reduction in agent modules"
            })

        # Check for similar functions
        similar_funcs = self.duplication_report["similar_functions"].get("duplicate_names", [])
        if similar_funcs:
            recommendations.append({
                "category": "Function Deduplication",
                "priority": "MEDIUM",
                "description": f"Found {len(similar_funcs)} functions with duplicate names - create base classes or utility functions",
                "savings": "10-20% code reduction"
            })

        # Check for large files
        large_files = self.duplication_report["files_by_size"]["large"]
        if large_files:
            recommendations.append({
                "category": "File Splitting",
                "priority": "MEDIUM",
                "description": f"Found {len(large_files)} files over 500 lines - consider splitting into smaller modules",
                "savings": "Improved maintainability"
            })

        # Check for utility consolidations
        utils_files = [p for p in self.file_analysis.keys() if 'utils' in p.lower() or 'util' in p.lower()]
        if len(utils_files) > 3:
            recommendations.append({
                "category": "Utility Consolidation",
                "priority": "HIGH",
                "description": f"Found {len(utils_files)} utility modules - consolidate overlapping functionality",
                "savings": "20-30% code reduction"
            })

        # Check for test files
        test_files = [p for p in self.file_analysis.keys() if 'test' in p.lower()]
        if len(test_files) > 10:
            recommendations.append({
                "category": "Test Organization",
                "priority": "LOW",
                "description": f"Found {len(test_files)} test files - use shared fixtures and base test classes",
                "savings": "15-25% test code reduction"
            })

        self.duplication_report["recommendations"] = recommendations

    def _create_summary(self):
        """Create analysis summary."""
        total_files = len(self.file_analysis)
        total_lines = sum(analysis["lines"] for analysis in self.file_analysis.values())

        self.duplication_report["summary"] = {
            "total_python_files": total_files,
            "total_lines": total_lines,
            "average_file_size": total_lines / total_files if total_files > 0 else 0,
            "largest_file": max(self.file_analysis.items(),
                               key=lambda x: x[1]["lines"]) if self.file_analysis else None,
            "duplication_score": self._calculate_duplication_score(),
            "potential_savings": self._estimate_potential_savings()
        }

    def _calculate_duplication_score(self) -> float:
        """Calculate a score from 0-100 representing duplication level."""
        score = 0

        # Factor in duplicate functions
        similar_funcs = self.duplication_report["similar_functions"].get("duplicate_names", [])
        score += min(30, len(similar_funcs) * 5)

        # Factor in duplicate imports
        repeated_imports = len(self.duplication_report["repeated_imports"])
        score += min(20, repeated_imports * 2)

        # Factor in duplicate blocks
        duplicate_blocks = len(self.duplication_report["duplicate_code_blocks"])
        score += min(30, duplicate_blocks * 3)

        # Factor in file count vs unique functionality
        total_files = len(self.file_analysis)
        if total_files > 50:
            score += 20

        return min(100, score)

    def _estimate_potential_savings(self) -> Dict:
        """Estimate potential code reduction savings."""
        dup_score = self._calculate_duplication_score()

        # Conservative estimates
        conservative = dup_score * 0.2  # 20% of duplication score as percent
        aggressive = dup_score * 0.4     # 40% of duplication score as percent

        total_lines = self.duplication_report["summary"]["total_lines"]

        return {
            "conservative_percent": f"{conservative:.1f}%",
            "aggressive_percent": f"{aggressive:.1f}%",
            "conservative_lines": int(total_lines * conservative / 100),
            "aggressive_lines": int(total_lines * aggressive / 100)
        }

    def save_report(self, output_path: Path):
        """Save the analysis report to a JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.duplication_report, f, indent=2, default=str)
        print(f"\n📄 Report saved to: {output_path}")


def main():
    """Run code duplication analysis."""
    root_dir = Path(__file__).parent.parent
    analyzer = CodeDuplicationAnalyzer(root_dir)

    # Run analysis
    report = analyzer.analyze()

    # Print summary
    print("\n" + "=" * 50)
    print("📊 CODE DUPLICATION ANALYSIS SUMMARY")
    print("=" * 50)

    summary = report["summary"]
    print(f"\n📁 Total Python files: {summary['total_python_files']}")
    print(f"📄 Total lines of code: {summary['total_lines']:,}")
    print(f"📏 Average file size: {summary['average_file_size']:.0f} lines")

    if summary["largest_file"]:
        largest = summary["largest_file"]
        print(f"📈 Largest file: {largest[0]} ({largest[1]['lines']:,} lines)")

    print(f"\n🔄 Duplication score: {summary['duplication_score']}/100")

    savings = summary["potential_savings"]
    print(f"\n💰 Potential savings:")
    print(f"   Conservative: {savings['conservative_percent']} ({savings['conservative_lines']:,} lines)")
    print(f"   Aggressive:   {savings['aggressive_percent']} ({savings['aggressive_lines']:,} lines)")

    # Print top recommendations
    print("\n🎯 TOP RECOMMENDATIONS:")
    for i, rec in enumerate(report["recommendations"][:5], 1):
        print(f"\n{i}. {rec['category']} ({rec['priority']})")
        print(f"   {rec['description']}")
        print(f"   💡 Savings: {rec['savings']}")

    # Save detailed report
    output_path = root_dir / "reports" / "code_duplication_analysis.json"
    output_path.parent.mkdir(exist_ok=True)
    analyzer.save_report(output_path)


if __name__ == "__main__":
    main()