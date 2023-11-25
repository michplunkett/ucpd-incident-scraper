# UChicago Incident Page Scraper
This repository houses a scraping engine for the [UCPD's Incident Report webpage](https://incidentreports.uchicago.edu/). The data is stored on [Google Cloud Platform's Datastore](https://cloud.google.com/datastore) and ran using [Heroku's Dyno](https://devcenter.heroku.com/articles/dyno-types) functionality.
## Relevant Reading
- Ethical Issues of Crime Mapping: [Link](https://storymaps.arcgis.com/stories/9b71d1fba77641a0ad35b07b23aae66b?utm_source=pocket_saves)

## Project Requirements
- Python version: `^3.11`
- [Poetry](https://python-poetry.org/)

### Required Credentials
- [Census API Key](https://api.census.gov/data/key_signup.html) stored in the environment variable: `CENSUS_API_KEY`
- Google Cloud Platform [service account](https://cloud.google.com/iam/docs/service-account-overview) with location of the `service_account.json` file stored in the environment variable: `GOOGLE_APPLICATION_CREDENTIALS`
- Google Cloud Platform project ID stored in the environment variable: `GOOGLE_CLOUD_PROJECT`
- [Google Maps API](https://developers.google.com/maps/documentation/geocoding/get-api-key) key stored in the environment variable: `GOOGLE_MAPS_API_KEY`

## Instructions to Run the Project
1. Go into the base directory of the repository and type `poetry shell` into the terminal.
2. Run the command `poetry install` to install the requirements.
3. Use the `make update` command.

## Technical Notes
- Any modules should be added via the `poetry add [module]` command.
  - Example: `poetry add black`

## Standard Commands
- `make lint`: Runs `Black`, `isort`, and `ruff` on the codebase.
- `make seed`: Saves incidents starting from January 1st of 2015 and continuing until today.
- `make update`: Saves incidents starting from the most recently saved incident until today.
- `make build_model`: Builds a predictive XGBoost model based off of locally saved incident data and saves it in the `data` folder.
