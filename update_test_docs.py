#!/usr/bin/env python3
"""
Dynamic Test Documentation Updater

This script updates the UNIT_TESTING_GUIDE.md file with live test results,
coverage data, and test statistics for all test files in the tests directory.

Usage:
    python update_test_docs.py [options]

Options:
    --run-tests       Run tests and update documentation for all test files
    --coverage        Include coverage data in update
    --verbose         Show detailed output
    --stats           Show statistics without updating
    --help            Show this help message

Examples:
    python update_test_docs.py --run-tests --coverage
    python update_test_docs.py --stats
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import re
import xml.etree.ElementTree as ET
from collections import defaultdict


class TestDocumentationUpdater:
    """Updates test documentation with live test results for all test files."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.md_file = project_root / "UNIT_TESTING_GUIDE.md"
        self.report_file = project_root / "test-results.json"
        self.coverage_file = project_root / "coverage.xml"
        
    def run_tests(self, coverage: bool = False, verbose: bool = False) -> Dict:
        """Run tests for all files in tests directory and return results."""
        print("Running tests for all files...")
        
        cmd = [sys.executable, "-m", "pytest", str(self.tests_dir)]
        
        cmd.extend([
            "-v",  # Always verbose for parsing
            "--tb=short"
        ])
        
        if verbose:
            cmd.append("-vv")  # Extra verbose if requested
            
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=xml",
                "--cov-report=term-missing"
            ])
            
        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            success = result.returncode == 0 or (result.stdout and "PASSED" in result.stdout)
            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": 1
            }
    
    def parse_test_results(self, coverage: bool = False, verbose: bool = False, result: Optional[Dict] = None) -> Dict:
        """Parse test results from pytest output for all test files."""
        try:
            if result is None:
                cmd = [sys.executable, "-m", "pytest", str(self.tests_dir), "-v", "--tb=no"]
                if verbose:
                    cmd.append("-vv")
                if coverage:
                    cmd.extend([
                        "--cov=app",
                        "--cov-report=xml",
                        "--cov-report=term-missing"
                    ])
                res = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
                stdout = res.stdout
                stderr = res.stderr
            else:
                stdout = result["stdout"]
                stderr = result["stderr"]
            
            # Parse collected tests from the beginning of output
            collect_match = re.search(r"collected (\d+) items?", stdout)
            total_tests = int(collect_match.group(1)) if collect_match else 0
            
            # Find the final summary line (the last line with = characters)
            summary_lines = [line.strip() for line in stdout.split("\n") if line.startswith("=") and "in" in line]
            summary = summary_lines[-1] if summary_lines else ""
            
            # Parse duration
            duration_match = re.search(r"in ([\d.]+)s", summary)
            duration = float(duration_match.group(1)) if duration_match else 0.0
            
            # Parse the summary line more carefully
            # Example: "================== 6 failed, 768 passed, 59 warnings in 55.28s =================="
            passed = failed = skipped = error = warnings = 0
            
            # Extract numbers from summary line
            numbers = re.findall(r'(\d+) (failed|passed|skipped|error|warnings?)', summary)
            for num_str, status in numbers:
                num = int(num_str)
                if status == "passed":
                    passed = num
                elif status == "failed":
                    failed = num
                elif status == "skipped":
                    skipped = num
                elif status in ("error", "errors"):
                    error = num
                elif status in ("warning", "warnings"):
                    warnings = num
            
            # Parse file statistics from individual test lines
            file_stats = defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "total": 0})
            
            # Look for test result lines in the format: tests/test_file.py::test_function PASSED
            for line in stdout.split("\n"):
                if "::" in line and any(status in line for status in ["PASSED", "FAILED", "SKIPPED", "ERROR"]):
                    # Extract file name from path like "tests/test_file.py::test_function"
                    parts = line.split("::")
                    if len(parts) >= 2:
                        file_path = parts[0].strip()
                        file_name = file_path.split("/")[-1] if "/" in file_path else file_path
                        
                        # Only count if it's a test file
                        if file_name.startswith("test_") and file_name.endswith(".py"):
                            file_stats[file_name]["total"] += 1
                            
                            if "PASSED" in line:
                                file_stats[file_name]["passed"] += 1
                            elif "FAILED" in line:
                                file_stats[file_name]["failed"] += 1
                            elif "SKIPPED" in line:
                                file_stats[file_name]["skipped"] += 1
                            elif "ERROR" in line:
                                file_stats[file_name]["error"] += 1
            
            return {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "error": error,
                "warnings": warnings,
                "duration": duration,
                "file_stats": dict(file_stats),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"Error parsing test results: {e}")
            return self._get_empty_results()
    
    def parse_coverage_data(self) -> Dict:
        """Parse coverage data from XML report."""
        if not self.coverage_file.exists():
            return self._get_empty_coverage()
            
        try:
            tree = ET.parse(self.coverage_file)
            root = tree.getroot()
            
            overall_coverage = {
                "line_rate": float(root.get("line-rate", 0)) * 100,
                "branch_rate": float(root.get("branch-rate", 0)) * 100,
                "function_rate": float(root.get("function-rate", 0)) * 100,
                "class_rate": float(root.get("class-rate", 0)) * 100
            }
            
            # Aggregate per-file coverage robustly across Cobertura variants
            file_data = defaultdict(lambda: {"covered": 0, "total": 0})
            # Classes may be under packages/package/classes/class
            for class_elem in root.findall('.//class'):
                filename = class_elem.get('filename') or 'unknown'
                # Lines may be nested as classes/class/lines/line
                for line_elem in class_elem.findall('./lines/line'):
                    hits_attr = line_elem.get('hits', '0')
                    try:
                        hits = int(hits_attr)
                    except Exception:
                        hits = 0
                    file_data[filename]["total"] += 1
                    if hits > 0:
                        file_data[filename]["covered"] += 1
            
            module_coverage = []
            for filename, data in sorted(file_data.items()):
                line_rate = (data["covered"] / data["total"] * 100) if data["total"] > 0 else 0.0
                module_coverage.append({
                    "module": filename,
                    "coverage": line_rate,
                    "lines": data["covered"],
                    "missing": data["total"] - data["covered"]
                })
            
            return {
                "overall": overall_coverage,
                "modules": module_coverage
            }
        except Exception as e:
            print(f"Error parsing coverage data: {e}")
            return self._get_empty_coverage()
    
    def get_test_files(self) -> List[Dict]:
        """Get list of all test files and their basic info."""
        test_files = []
        
        if not self.tests_dir.exists():
            return test_files
            
        for test_file in self.tests_dir.glob("test_*.py"):
            if test_file.name == "__init__.py":
                continue
                
            mtime = datetime.fromtimestamp(test_file.stat().st_mtime)
            
            test_files.append({
                "name": test_file.name,
                "path": str(test_file.relative_to(self.project_root)),
                "size": test_file.stat().st_size,
                "modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                "description": self._get_test_file_description(test_file)
            })
            
        return sorted(test_files, key=lambda x: x["name"])
    
    def _get_test_file_description(self, test_file: Path) -> str:
        """Get description of test file from its content."""
        try:
            with open(test_file, 'r') as f:
                content = f.read()
                
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('class Test') and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        docstring = next_line[3:]
                        if docstring.endswith('"""') or docstring.endswith("'''"):
                            return docstring[:-3].strip()
                        else:
                            for j in range(i + 2, len(lines)):
                                if '"""' in lines[j] or "'''" in lines[j]:
                                    return ' '.join([l.strip() for l in lines[i+1:j]]).replace('"""', '').replace("'''", '').strip()
                elif line.strip().startswith('"""') and i == 0:
                    for j in range(i + 1, len(lines)):
                        if '"""' in lines[j]:
                            return ' '.join([l.strip() for l in lines[i:j]]).replace('"""', '').strip()
        except Exception:
            pass
            
        return "Test file for the application"
    
    def _get_empty_results(self) -> Dict:
        """Return empty test results structure."""
        return {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "error": 0,
            "warnings": 0,
            "duration": 0,
            "file_stats": {},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _get_empty_coverage(self) -> Dict:
        """Return empty coverage structure."""
        return {
            "overall": {
                "line_rate": 0,
                "branch_rate": 0,
                "function_rate": 0,
                "class_rate": 0
            },
            "modules": []
        }
    
    def update_markdown(self, test_results: Dict, coverage_data: Dict, test_files: List[Dict]) -> None:
        """Update the markdown file with new data for all test files."""
        if not self.md_file.exists():
            print(f"Markdown file not found: {self.md_file}")
            return
            
        try:
            with open(self.md_file, 'r') as f:
                content = f.read()
            
            # Update timestamp - handle both placeholder and existing timestamp
            content = re.sub(
                r'\*Last Updated: \[DYNAMIC_TIMESTAMP\]\*',
                f'*Last Updated: {test_results["timestamp"]}*',
                content
            )
            content = re.sub(
                r'\*Last Updated: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\*',
                f'*Last Updated: {test_results["timestamp"]}*',
                content
            )
            
            content = re.sub(r'\[DYNAMIC_TOTAL_TESTS\]', str(test_results["total_tests"]), content)
            content = re.sub(r'\[DYNAMIC_PASSED_TESTS\]', str(test_results["passed"]), content)
            content = re.sub(r'\[DYNAMIC_FAILED_TESTS\]', str(test_results["failed"]), content)
            content = re.sub(r'\[DYNAMIC_ERROR_TESTS\]', str(test_results["error"]), content)
            content = re.sub(r'\[DYNAMIC_WARNING_TESTS\]', str(test_results["warnings"]), content)
            
            coverage_percent = coverage_data["overall"]["line_rate"]
            content = re.sub(r'\[DYNAMIC_COVERAGE_PERCENTAGE\]', f"{coverage_percent:.1f}", content)
            
            # Ensure totals align between sections by recomputing totals consistently
            normalized_file_stats = {}
            for name, stats in test_results["file_stats"].items():
                passed = stats.get("passed", 0)
                failed = stats.get("failed", 0)
                skipped = stats.get("skipped", 0)
                error = stats.get("error", 0)
                total = stats.get("total", 0) or (passed + failed + skipped + error)
                normalized_file_stats[name] = {
                    "passed": passed,
                    "failed": failed,
                    "skipped": skipped,
                    "error": error,
                    "total": total,
                }

            file_stats_table = self._generate_file_stats_table(normalized_file_stats)
            content = re.sub(
                r'\[DYNAMIC_FILE_STATS\]',
                file_stats_table,
                content
            )
            
            content = re.sub(r'\[DYNAMIC_LINE_COVERAGE\]', f"{coverage_data['overall']['line_rate']:.1f}", content)
            
            test_files_table = self._generate_test_files_table(test_files, normalized_file_stats)
            content = re.sub(
                r'\[DYNAMIC_TEST_FILES\]',
                test_files_table,
                content
            )
            
            # Build dynamic individual results for all files
            individual_sections = []
            for file_name in sorted(test_results["file_stats"].keys()):
                stats = test_results["file_stats"][file_name]
                total = stats.get("total", 0) or (stats.get("passed", 0) + stats.get("failed", 0) + stats.get("skipped", 0) + stats.get("error", 0))
                passed = stats.get("passed", 0)
                failed = stats.get("failed", 0)
                warnings = 0
                section = (
                    f"\n#### {file_name}\n"
                    f"- **Total Tests**: {total}\n"
                    f"- **Passed**: {passed}\n"
                    f"- **Failed**: {failed}\n"
                    f"- **Warnings**: {warnings}\n"
                    f"- **Last Run**: {test_results['timestamp']}\n"
                )
                individual_sections.append(section)
            content = re.sub(r'\[DYNAMIC_INDIVIDUAL_RESULTS\]', "".join(individual_sections).strip(), content)
            
            coverage_table = self._generate_coverage_table(coverage_data["modules"])
            content = re.sub(
                r'\[DYNAMIC_COVERAGE_TABLE\]',
                coverage_table,
                content
            )
            
            coverage_status = "✅ PASSED" if coverage_percent >= 80 else "❌ NEEDS IMPROVEMENT"
            content = re.sub(r'\[DYNAMIC_COVERAGE_STATUS\]', coverage_status, content)
            content = re.sub(r'\[DYNAMIC_OVERALL_COVERAGE\]', f"{coverage_percent:.1f}", content)
            
            with open(self.md_file, 'w') as f:
                f.write(content)
                
            print(f"✅ Updated {self.md_file} with latest test results")
            
        except Exception as e:
            print(f"❌ Error updating markdown file: {e}")
    
    def _generate_file_stats_table(self, file_stats: Dict) -> str:
        """Generate file statistics table for all test files."""
        if not file_stats:
            return "| No test data available |"
            
        table = []
        for file_name, stats in sorted(file_stats.items()):
            total = stats.get("total", 0)
            passed = stats.get("passed", 0)
            failed = stats.get("failed", 0)
            skipped = stats.get("skipped", 0)
            error = stats.get("error", 0)
            
            # Calculate total if not provided
            if total == 0:
                total = passed + failed + skipped + error
            
            percent = (passed / total * 100) if total > 0 else 0
            status = "✅" if percent == 100 else "⚠️" if percent >= 80 else "❌"
            
            table.append(f"| {file_name:<30} | {passed:<6} | {total:<5} | {percent:>7.1f}% | {status:<6} |")
            
        return "\n".join(table)
    
    def _generate_test_files_table(self, test_files: List[Dict], file_stats: Dict) -> str:
        """Generate test files table for all test files.
        Last Modified reflects file mtime; this is expected and requested.
        """
        if not test_files:
            return "| No test files found |"
            
        table = []
        for test_file in test_files:
            file_name = test_file["name"]
            description = test_file["description"]
            
            # Get test count from file_stats
            stats = file_stats.get(file_name, {})
            test_count = stats.get("total", 0)
            if test_count == 0:
                test_count = sum(stats.values())
            
            last_run = test_file["modified"]  # mtime, not test run time
            
            table.append(f"| {file_name:<30} | {description:<50} | {test_count:<10} | {last_run:<19} |")
            
        return "\n".join(table)
    
    def _generate_coverage_table(self, modules: List[Dict]) -> str:
        """Generate coverage by module table.
        If line counts are unavailable (0/0), hide the columns and show only module + coverage.
        """
        if not modules:
            return "| No coverage data available |"
            
        has_line_counts = any(m.get("lines", 0) or m.get("missing", 0) for m in modules)
        rows = []
        if has_line_counts:
            rows.append("| Module | Coverage | Lines | Missing |")
            rows.append("|--------|----------|-------|---------|")
            for module in modules[:10]:
                coverage = module["coverage"]
                lines = module.get("lines", 0)
                missing = module.get("missing", 0)
                rows.append(f"| {module['module']:<30} | {coverage:>7.1f}% | {lines:<5} | {missing:<7} |")
        else:
            rows.append("| Module | Coverage |")
            rows.append("|--------|----------|")
            for module in modules[:10]:
                coverage = module["coverage"]
                rows.append(f"| {module['module']:<30} | {coverage:>7.1f}% |")
        return "\n".join(rows)
    
    def show_statistics(self) -> None:
        """Show current test statistics without updating files."""
        print("📊 Current Test Statistics")
        print("=" * 50)
        
        test_results = self.parse_test_results()
        coverage_data = self.parse_coverage_data()
        test_files = self.get_test_files()
        
        print(f"Total Tests: {test_results['total_tests']}")
        print(f"Passed: {test_results['passed']} ✅")
        print(f"Failed: {test_results['failed']} ❌")
        print(f"Errors: {test_results['error']} ⚠️")
        print(f"Warnings: {test_results['warnings']} ⚡")
        print(f"Coverage: {coverage_data['overall']['line_rate']:.1f}%")
        print(f"Last Updated: {test_results['timestamp']}")
        
        print(f"\nTest Files: {len(test_files)}")
        for test_file in test_files:
            print(f"  - {test_file['name']}: {test_file['description']}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Update test documentation with live results for all test files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--run-tests", action="store_true", help="Run tests and update documentation")
    parser.add_argument("--coverage", action="store_true", help="Include coverage data in update")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--stats", action="store_true", help="Show statistics without updating")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.absolute()
    updater = TestDocumentationUpdater(project_root)
    
    if args.stats:
        updater.show_statistics()
        return
    
    result_dict = None
    if args.run_tests or args.coverage:
        print("🚀 Running tests...")
        result_dict = updater.run_tests(
            coverage=args.coverage,
            verbose=args.verbose
        )
        
        if args.verbose:
            print("\nTest Output:\n")
            print(result_dict["stdout"])
        
        if not result_dict["success"]:
            print(f"⚠️ Some tests failed, but continuing with documentation update...")
            if args.verbose:
                print(f"Error details: {result_dict['stderr'][:200]}...")
        
        print("✅ Tests completed")
    
    print("📊 Parsing test results...")
    test_results = updater.parse_test_results(
        coverage=args.coverage if result_dict is None else False,
        verbose=args.verbose if result_dict is None else False,
        result=result_dict
    )
    coverage_data = updater.parse_coverage_data()
    test_files = updater.get_test_files()
    
    print("📝 Updating documentation...")
    updater.update_markdown(test_results, coverage_data, test_files)
    
    print("🎉 Documentation updated successfully!")


if __name__ == "__main__":
    main()