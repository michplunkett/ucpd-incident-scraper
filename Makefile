BASEDIR=incident_scraper

.PHONY: format
format:
	black ${BASEDIR}/ ./
	isort ${BASEDIR}/

.PHONY: lint
lint:
	ruff ${BASEDIR}/

.PHONY: seed_datastore
seed_datastore:
	python -m incident_scraper --seed

.PHONY: three_days
three_days:
	python -m incident_scraper --days-back 3

.PHONY: five_days
five_days:
	python -m incident_scraper --days-back 5

.PHONY: ten_days
ten_days:
	python -m incident_scraper --days-back 10
