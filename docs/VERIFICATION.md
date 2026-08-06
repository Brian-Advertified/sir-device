# Verification record

Run from the repository root:

```bash
python -m compileall -q app scripts
pytest -q
python scripts/check_file_sizes.py
alembic upgrade head
```

The delivered package was checked for:

- Python compilation
- automated application tests
- empty-database public rendering
- password and session security
- production configuration fail-closed behaviour
- atomic and idempotent deal import
- cart and checkout behaviour
- Alembic schema creation
- Docker Compose YAML parsing
- backup-script shell syntax
- source, template, stylesheet and script files below 500 lines
- absence of seeded catalogue, customer, order and dashboard records
- absence of C# source files

Production acceptance still requires genuine network deal data, business credentials, legal content, payment sandbox certification and operational security review.
