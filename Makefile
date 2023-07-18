BASEDIR=incident_scraper

.PHONY: format
format:
	black ${BASEDIR}/ ./
	isort ${BASEDIR}/

.PHONY: lint
lint:
	ruff ${BASEDIR}/

.PHONY: run
run:
	python -m project
