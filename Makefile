.PHONY: install run test lint format

install:
	uv sync

run:
	uv run streamlit run app.py

test:
	uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .
