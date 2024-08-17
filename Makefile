default: create-requirements lint

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: create-requirements
create-requirements:
	poetry export --format=requirements.txt > requirements.txt

.PHONY: download
download:
	python -m incident_scraper download

.PHONY: download-and-move
download-and-move: download
	cp ./incident_dump.csv ../one-offs/notebooks/data/
	gzip --k ./incident_dump.csv
	mv ./incident_dump.csv.gz ../ucpd-incident-reporting/incident_reporting/data/

.PHONY: build-model
build-model: download
	python -m incident_scraper build-model

.PHONY: categorize
categorize: build-model
	python -m incident_scraper categorize

.PHONY: correct-location
correct-location:
	python -m incident_scraper correct-location

.PHONY: lemmatize-categories
lemmatize-categories:
	python -m incident_scraper lemmatize-categories

.PHONY: seed
seed:
	python -m incident_scraper seed

.PHONY: update
update:
	python -m incident_scraper update

.PHONY: three-days
three-days:
	python -m incident_scraper days-back 3

.PHONY: five-days
five-days:
	python -m incident_scraper days-back 5

.PHONY: ten-days
ten-days:
	python -m incident_scraper days-back 10

.PHONY: twenty-days
twenty-days:
	python -m incident_scraper days-back 20

.PHONY: thirty-days
thirty-days:
	python -m incident_scraper days-back 30

.PHONY: test
test:
	pytest -vs test/
