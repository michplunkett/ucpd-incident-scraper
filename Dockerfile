FROM python:3.11-slim

ENV PYTHONPATH=${PYTHONPATH}:${PWD}
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN mkdir /incident_scraper
COPY pyproject.toml /incident_scraper

WORKDIR /incident_scraper

RUN pip3 install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

COPY /incident_scraper /incident_scraper

CMD ["python", "-m", "incident_scraper", "days-back"]
