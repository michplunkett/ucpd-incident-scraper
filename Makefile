BASEDIR=incident_scraper

.PHONY: lint
lint:
	black ${BASEDIR}/ ./scheduler.py
	isort ${BASEDIR}/ ./scheduler.py
	ruff ${BASEDIR}/ ./scheduler.py

.PHONY: download
download:
	python -m incident_scraper download

.PHONY: seed
seed:
	python -m incident_scraper seed

.PHONY: update
update:
	python -m incident_scraper update

.PHONY: three_days
three_days:
	python -m incident_scraper days-back 3

.PHONY: five_days
five_days:
	python -m incident_scraper days-back 5

.PHONY: ten_days
ten_days:
	python -m incident_scraper days-back 10

.PHONY: twenty_days
twenty_days:
	python -m incident_scraper days-back 20
