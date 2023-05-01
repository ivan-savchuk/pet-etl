include .env

.PHONY: help
help:
	@echo "make run"
	@echo "       Run something"
	@echo "make linter"
	@echo "       Run linter"
	@echo "make test"
	@echo "       Run tests"
	@echo "make build"
	@echo "       Build something"
	@echo "make deploy"
	@echo "       Deploy something"
	@echo "make clean"
	@echo "       Clean something"

.PHONY: linter
linter:
	@echo "Running linter"

.PHONY: test
test:
	@echo "Running tests"
