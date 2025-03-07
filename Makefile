default: lint

.PHONY: env
env:
	uv venv

.PHONY: lint
lint:
	uv run pre-commit run --all-files

.PHONY: download
download:
	uv run python -m incident_scraper download

.PHONY: download-and-move
download-and-move: download
	cp ./incident_dump.csv ../one-offs/notebooks/data/
	gzip --k ./incident_dump.csv
	mv ./incident_dump.csv.gz ../ucpd-incident-reporting/incident_reporting/data/

.PHONY: build-model
build-model: download
	uv run python -m incident_scraper build-model

.PHONY: categorize
categorize: build-model
	uv run python -m incident_scraper categorize

.PHONY: lemmatize-categories
lemmatize-categories:
	uv run python -m incident_scraper lemmatize-categories

.PHONY: seed
seed:
	uv run python -m incident_scraper seed

.PHONY: update
update:
	uv run python -m incident_scraper update

.PHONY: three-days
three-days:
	uv run python -m incident_scraper days-back 3

.PHONY: five-days
five-days:
	uv run python -m incident_scraper days-back 5

.PHONY: ten-days
ten-days:
	uv run python -m incident_scraper days-back 10

.PHONY: twenty-days
twenty-days:
	uv run python -m incident_scraper days-back 20

.PHONY: thirty-days
thirty-days:
	uv run python -m incident_scraper days-back 30

.PHONY: test
test:
	uv run pytest -vs tests/
