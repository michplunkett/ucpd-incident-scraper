BASEDIR=incident_scraper

.PHONY: format
format:
	black ${BASEDIR}/ test/
	isort ${BASEDIR}/ test/
	nbqa isort ${BASEDIR}/

.PHONY: lint
lint:
	ruff ${BASEDIR}/ test/
	nbqa ruff ${BASEDIR}/

.PHONY: test
test:
	pytest -vs test/

.PHONY: test-and-fail
test-and-fail:
	pytest -vsx test/

.PHONY: run
run:
	python -m project
