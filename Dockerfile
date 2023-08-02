FROM python:3.11-slim

ENV PYTHONPATH=${PYTHONPATH}:${PWD} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN mkdir /incident_scraper
COPY pyproject.toml /incident_scraper

WORKDIR /incident_scraper

RUN pip3 install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

COPY /incident_scraper /incident_scraper

CMD ["poetry", "run", "python", "-m", "incident_scraper", "days-back"]
