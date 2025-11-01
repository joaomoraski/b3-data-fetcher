install:
	poetry install --no-root
	pre-commit install --hook-type pre-commit --hook-type commit-msg

lint:
	ruff check --select I .
	ruff format --check .

lint-fix:
	ruff check --select I --fix .
	ruff format .

csv-db:
	poetry run python -m app.consumers.csv_to_database

download:
	poetry run python -m app.consumers.download ${year}

generate-migrate:
	alembic revision --autogenerate -m ${msg}

migrate:
	alembic upgrade +1

rollback:
	alembic downgrade -1

pre-commit:
	pre-commit run --all --verbose

run:
	poetry run uvicorn app.main:app --port 8080 --reload

clean:
	rm cache.mouras
