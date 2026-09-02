# Makefile
META_CONFIG ?= conf/meta_config.yaml
HOST ?= 0.0.0.0
PORT ?= 8000

.PHONY: build run dev
build:
	uv run python -m app.scripts.build_meta_knowledge -c $(META_CONFIG)

run:
	uv run uvicorn app.main:app --host $(HOST) --port $(PORT)

dev:
	uv run uvicorn app.main:app --host $(HOST) --port $(PORT) --reload
