.PHONY: setup backend frontend test build

setup:
	cd backend && uv venv -q .venv && uv pip install -e ".[dev,ai]"
	cd frontend && npm install

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/pytest && .venv/bin/ruff check app tests
	cd frontend && npm run lint && npx tsc --noEmit

build:
	cd frontend && npm run build
