#!/usr/bin/env python3
"""
Test runner script for the Bybit Grid Trading Bot.

This script provides various testing options including unit tests,
integration tests, coverage reports, and performance tests.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(command: list, description: str) -> bool:
    """
    Run a command and return success status.
    
    Args:
        command: Command to run as list
        description: Description of the command
        
    Returns:
        True if command succeeded
    """
    print(f"\n🔄 {description}...")
    print(f"Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def run_unit_tests(verbose: bool = False) -> bool:
    """Run unit tests."""
    command = ["pytest", "tests/", "-m", "unit"]
    if verbose:
        command.append("-v")
    
    return run_command(command, "Running unit tests")


def run_integration_tests(verbose: bool = False) -> bool:
    """Run integration tests."""
    command = ["pytest", "tests/", "-m", "integration"]
    if verbose:
        command.append("-v")
    
    return run_command(command, "Running integration tests")


def run_all_tests(verbose: bool = False) -> bool:
    """Run all tests."""
    command = ["pytest", "tests/"]
    if verbose:
        command.append("-v")
    
    return run_command(command, "Running all tests")


def run_coverage_tests() -> bool:
    """Run tests with coverage report."""
    commands = [
        (["pytest", "tests/", "--cov=.", "--cov-report=term-missing"], 
         "Running tests with coverage"),
        (["pytest", "tests/", "--cov=.", "--cov-report=html"], 
         "Generating HTML coverage report")
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
    
    if success:
        print("\n📊 Coverage report generated in htmlcov/index.html")
    
    return success


def run_performance_tests() -> bool:
    """Run performance tests."""
    command = ["pytest", "tests/", "-m", "slow", "--durations=10"]
    return run_command(command, "Running performance tests")


def run_linting() -> bool:
    """Run code linting."""
    commands = [
        (["flake8", ".", "--max-line-length=100", "--exclude=venv,env"], 
         "Running flake8 linting"),
        (["black", ".", "--check"], 
         "Checking code formatting with black"),
        (["isort", ".", "--check-only"], 
         "Checking import sorting with isort")
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
    
    return success


def run_type_checking() -> bool:
    """Run type checking with mypy."""
    command = ["mypy", ".", "--ignore-missing-imports"]
    return run_command(command, "Running type checking with mypy")


def run_security_check() -> bool:
    """Run security checks."""
    commands = [
        (["bandit", "-r", ".", "-x", "tests/"], 
         "Running security check with bandit"),
        (["safety", "check"], 
         "Checking dependencies for security vulnerabilities")
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
    
    return success


def install_test_dependencies() -> bool:
    """Install test dependencies."""
    test_deps = [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
        "flake8>=5.0.0",
        "black>=22.0.0",
        "isort>=5.0.0",
        "mypy>=1.0.0",
        "bandit>=1.7.0",
        "safety>=2.0.0"
    ]
    
    command = ["pip", "install"] + test_deps
    return run_command(command, "Installing test dependencies")


def clean_test_artifacts() -> bool:
    """Clean test artifacts."""
    import shutil
    
    artifacts = [
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        "__pycache__",
        "*.pyc",
        ".mypy_cache"
    ]
    
    print("\n🧹 Cleaning test artifacts...")
    
    for artifact in artifacts:
        if artifact.startswith("*."):
            # Handle glob patterns
            for path in Path(".").rglob(artifact):
                try:
                    path.unlink()
                    print(f"Removed file: {path}")
                except Exception as e:
                    print(f"Failed to remove {path}: {e}")
        else:
            # Handle directories
            path = Path(artifact)
            if path.exists():
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                        print(f"Removed directory: {path}")
                    else:
                        path.unlink()
                        print(f"Removed file: {path}")
                except Exception as e:
                    print(f"Failed to remove {path}: {e}")
    
    print("✅ Cleanup completed")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test runner for Bybit Grid Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all", "coverage", "performance", 
                "lint", "type-check", "security", "install-deps", "clean"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    print("🧪 Bybit Grid Trading Bot - Test Runner")
    print("=" * 50)
    
    success = True
    
    if args.type == "unit":
        success = run_unit_tests(args.verbose)
    elif args.type == "integration":
        success = run_integration_tests(args.verbose)
    elif args.type == "all":
        success = run_all_tests(args.verbose)
    elif args.type == "coverage":
        success = run_coverage_tests()
    elif args.type == "performance":
        success = run_performance_tests()
    elif args.type == "lint":
        success = run_linting()
    elif args.type == "type-check":
        success = run_type_checking()
    elif args.type == "security":
        success = run_security_check()
    elif args.type == "install-deps":
        success = install_test_dependencies()
    elif args.type == "clean":
        success = clean_test_artifacts()
    
    if success:
        print(f"\n🎉 {args.type.title()} completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 {args.type.title()} failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
