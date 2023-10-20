BASEDIR=incident_scraper

default: create-requirements lint

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: create-requirements
create-requirements:
	poetry export --without-hashes --format=requirements.txt > requirements.txt

.PHONY: download
download:
	python -m incident_scraper download

.PHONY: download-and-move
download-and-move: download
	cp ./incident_dump.csv ../one-offs/notebooks/data/
	gzip ./incident_dump.csv
	cp ./incident_dump.csv.gz ../ucpd-incident-reporting/incident_reporting/data/

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

.PHONY: test
test:
	pytest -vs test/

.PHONY: test-and-fail
test-and-fail:
	pytest -vsx test/
