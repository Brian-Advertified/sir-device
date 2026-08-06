from pathlib import Path


MAX_LINES = 499
CHECKED_SUFFIXES = {".py", ".html", ".css", ".js", ".toml", ".yml", ".yaml"}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    oversized = []
    excluded = {".venv", ".git", "node_modules"}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in CHECKED_SUFFIXES and not excluded.intersection(path.parts):
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > MAX_LINES:
                oversized.append((path.relative_to(root), line_count))
    if oversized:
        for path, count in oversized:
            print(f"{path}: {count} lines")
        return 1
    print(f"All checked files are under {MAX_LINES + 1} lines.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
