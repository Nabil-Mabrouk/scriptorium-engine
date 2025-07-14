import os
from pathlib import Path

# --- Configuration ---
DIRECTORIES = [
    "alembic",
    "src",
    "src/project",
    "src/crew",
    "src/core",
    "tests",
    "tests/project",
    "tests/crew",
    "requirements",
]

FILES = {
    "src": ["__init__.py", "main.py"],
    "src/core": ["__init__.py", "config.py", "database.py", "models.py", "schemas.py", "exceptions.py"],
    "src/project": ["__init__.py", "router.py", "schemas.py", "models.py", "dependencies.py", "service.py", "exceptions.py"],
    "src/crew": ["__init__.py", "router.py", "schemas.py", "agents.py", "tasks.py", "config.py", "worker.py"],
    "tests": ["__init__.py", "conftest.py"],
    "tests/project": ["__init__.py"],
    "tests/crew": ["__init__.py"],
    "requirements": ["base.txt", "dev.txt"],
    ".": [".env", "alembic.ini"],
}

GITIGNORE_CONTENT = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Virtual Environment
.venv/
venv/
ENV/
env/
env.bak/
venv.bak/

# Environment files
.env
.env.*

# Database files
*.db
*.sqlite3

# IDE / Editor specific files
.vscode/
.idea/
*.swp
*.swo

# Test artifacts
.pytest_cache/
.coverage
htmlcov/

# Log files
*.log
"""

def main():
    """Main function to create the project structure."""
    print("🚀 Initializing Scriptorium-Engine project structure...")

    # Create directories
    print("   -> Creating core directories...")
    for directory in DIRECTORIES:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Create empty files
    print("   -> Populating packages with initial .py files...")
    for directory, file_list in FILES.items():
        for filename in file_list:
            Path(directory, filename).touch()

    # Create .gitignore
    print("   -> Creating a foundational .gitignore...")
    with open(".gitignore", "w") as f:
        f.write(GITIGNORE_CONTENT.strip())

    print("\n✅ Project structure for 'scriptorium-engine' created successfully.")
    print("\nNext Steps:")
    print("1. Ensure your Python virtual environment is active.")
    print("2. Populate requirements/base.txt and dev.txt.")
    print("3. Install dependencies: pip install -r requirements/dev.txt")
    print("4. Initialize your Git repository: git init && git add . && git commit -m 'Initial project structure'")
    print("\nSynchronization complete. Ready for development.")

if __name__ == "__main__":
    main()