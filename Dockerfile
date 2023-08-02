FROM python:3.11

RUN mkdir /incident_scraper

COPY /incident_scraper /incident_scraper
COPY pyproject.toml /incident_scraper

WORKDIR /incident_scraper
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev
