BASEDIR=incident-scraper

.PHONY: format
format:
	black ${BASEDIR}/ test/
	isort ${BASEDIR}/ test/

.PHONY: lint
lint:
	ruff ${BASEDIR}/ test/

.PHONY: test
test:
	pytest -vs test/

.PHONY: test-and-fail
test-and-fail:
	pytest -vsx test/

.PHONY: run
run:
	python -m project
