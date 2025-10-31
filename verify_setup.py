import sys
import importlib
from pathlib import Path


def check_imports():
    """Check that all required packages can be imported."""
    print("Checking package imports...")

    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "chromadb",
        "langchain",
        "sentence_transformers",
        "transformers",
        "httpx",
        "pytest",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"  ✅ {package}")
        except ImportError as e:
            print(f"  ❌ {package}: {e}")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False

    return True


def check_file_structure():
    """Check that all required files and directories exist."""
    print("\nChecking file structure...")

    required_files = [
        "app/__init__.py",
        "app/config.py",
        "app/schemas.py",
        "app/ingestion.py",
        "app/vectordb.py",
        "app/llm_client.py",
        "app/tools/__init__.py",
        "app/tools/qa_tool.py",
        "app/tools/issue_summary_tool.py",
        "app/tools/router_agent.py",
        "app/tools/prompts/qa_prompt.txt",
        "app/tools/prompts/issue_summary_prompt.txt",
        "app/tools/prompts/router_prompt.txt",
        "app/api/__init__.py",
        "app/api/main.py",
        "app/api/routes.py",
        "app/tests/__init__.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "Makefile",
        "README.md",
    ]

    missing_files = []

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n Missing files: {', '.join(missing_files)}")
        return False

    return True


def check_data_files():
    """Check that data files exist."""
    print("\n Checking data files...")

    data_files = [
        "data/ai_test_bug_report.txt",
        "data/ai_test_user_feedback.txt",
        "data/@AI Engineer Test.txt",
    ]

    missing_files = []

    for file_path in data_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n Missing data files: {', '.join(missing_files)}")
        return False

    return True


def check_app_imports():
    """Check that app modules can be imported."""
    print("\n Checking app imports...")

    app_modules = [
        "app.config",
        "app.schemas",
        "app.ingestion",
        "app.vectordb",
        "app.llm_client",
        "app.tools.qa_tool",
        "app.tools.issue_summary_tool",
        "app.tools.router_agent",
        "app.api.main",
        "app.api.routes",
    ]

    missing_modules = []

    for module in app_modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            missing_modules.append(module)

    if missing_modules:
        print(f"\n Import errors in: {', '.join(missing_modules)}")
        return False

    return True


def check_environment():
    """Check environment variables."""
    print("\nChecking environment...")

    # Check if .env file exists
    if Path(".env").exists():
        print(".env file exists")
    else:
        print(".env file not found (create from .env.example)")

    # Check critical environment variables
    env_vars = ["OPENAI_API_BASE", "OPENAI_API_KEY", "OPENAI_MODEL"]

    import os

    missing_vars = []

    for var in env_vars:
        if os.getenv(var):
            print(f"{var} is set")
        else:
            print(f"{var} is not set")
            missing_vars.append(var)

    if missing_vars:
        print("\n  Set these environment variables before running:")
        for var in missing_vars:
            print(f"     export {var}=your_value_here")

    return True


def main():
    """Run all verification checks."""
    print(" Internal AI Assistant Setup Verification")
    print("=" * 50)

    checks = [
        check_imports,
        check_file_structure,
        check_data_files,
        check_app_imports,
        check_environment,
    ]

    results = []

    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"Check failed with error: {e}")
            results.append(False)

    print("\n" + "=" * 50)

    if all(results):
        print("All checks passed! Setup is ready.")
        print("\nNext steps:")
        print("1. Set environment variables: cp .env.example .env")
        print("2. Edit .env with your API credentials")
        print("3. Ingest documents: make ingest")
        print("4. Run server: make run")
        return 0
    else:
        print("Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
