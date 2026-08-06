.PHONY: run test migrate admin check

run:
	uvicorn app.main:app --reload

test:
	pytest -q

migrate:
	alembic upgrade head

admin:
	python -m scripts.create_admin

check:
	python scripts/check_file_sizes.py
	pytest -q
