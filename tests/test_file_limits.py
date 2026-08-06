from pathlib import Path


def test_source_files_stay_below_500_lines():
    root = Path(__file__).resolve().parents[1]
    suffixes = {".py", ".html", ".css", ".js", ".toml", ".yml", ".yaml"}
    oversized = []
    excluded = {".venv", ".git", "node_modules"}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in suffixes and not excluded.intersection(path.parts):
            count = len(path.read_text(encoding="utf-8").splitlines())
            if count >= 500:
                oversized.append((str(path.relative_to(root)), count))
    assert not oversized, oversized
