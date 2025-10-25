install:
	poetry install --no-root
	pre-commit install --hook-type pre-commit --hook-type commit-msg

lint:
	ruff check --select I .
	ruff format --check .

lint-fix:
	ruff check --select I --fix .
	ruff format .

pre-commit:
	pre-commit run --all --verbose

run:
	poetry run uvicorn app.main:app --port 8080 --reload

clean:
	rm cache.mouras
