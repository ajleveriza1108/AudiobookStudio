from pathlib import Path

# ==========================================
# Audiobook Studio Project Generator
# ==========================================

PROJECT_NAME = "AudiobookStudio"

ROOT = Path(r"D:\AI") / PROJECT_NAME

folders = [
    "Books",
    "Output",
    "Logs",
    "Temp",
    "Models",
    "Voices",
    "Scripts",

    "core",
    "engines",

    "ui",
    "ui/templates",
    "ui/static",

    "assets",
    "tests",
]

files = {
    "app.py": "",
    "config.json": "{}",
    "README.md": "# Audiobook Studio\n",
    "requirements.txt": "",

    "core/__init__.py": "",
    "core/parser.py": "",
    "core/cleaner.py": "",
    "core/chapters.py": "",
    "core/exporter.py": "",
    "core/utils.py": "",

    "engines/__init__.py": "",
    "engines/base.py": "",
    "engines/kokoro.py": "",
    "engines/piper.py": "",
    "engines/xtts.py": "",

    "ui/__init__.py": "",
    "ui/server.py": "",
    "ui/templates/index.html": "",
    "ui/static/style.css": "",
    "ui/static/app.js": "",

    "tests/test_parser.py": "",
    "tests/test_engine.py": "",
}


def create_project():
    print(f"Creating project at:\n{ROOT}\n")

    ROOT.mkdir(parents=True, exist_ok=True)

    for folder in folders:
        path = ROOT / folder
        path.mkdir(parents=True, exist_ok=True)
        print(f"[DIR ] {path}")

    print()

    for filename, content in files.items():
        filepath = ROOT / filename

        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")
            print(f"[FILE] {filepath}")

    print("\nProject created successfully!")


if __name__ == "__main__":
    create_project()