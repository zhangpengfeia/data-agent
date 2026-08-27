# Makefile
META_CONFIG ?= conf/meta_config.yaml

.PHONY: build
build:
	uv run python -m app.scripts.build_meta_knowledge -c $(META_CONFIG)
