# UChicago Incident Page Scraper
This repository houses a scraping engine for the [UCPD's Incident Report webpage](https://incidentreports.uchicago.edu/). The data is stored on
[Google Cloud Platform's Datastore](https://cloud.google.com/datastore) and ran using [Heroku's Dyno](https://devcenter.heroku.com/articles/dyno-types) functionality.

## Primary Application Functions
1. Scrape the UCPD Incident Report webpage every weekday morning, pulling all incidents from the latest reported incident date in the Google Datastore to the current day.
2. Upload all stored UCPD incidents to the _Chicago Maroon_'s Google Drive every Saturday morning.

## Relevant Reading
- Ethical Issues of Crime Mapping: [Link](https://storymaps.arcgis.com/stories/9b71d1fba77641a0ad35b07b23aae66b?utm_source=pocket_saves)

## Acknowledgements
I'd like to thank [@kdumais111](https://github.com/kdumais111) and [@FedericoDM](https://github.com/FedericoDM) for their incredible help in getting the scraping architecture in place.
As well as [@ehabich](https://github.com/ehabich) for adding a bit of testing validation to the project. Thanks, y'all! <3

## Project Requirements
- `uv` version: `0.5.7`
- Download at: [link](https://docs.astral.sh/uv/).

### Required Credentials
- [Census API Key](https://api.census.gov/data/key_signup.html) stored in the environment variable: `CENSUS_API_KEY`
- Google Cloud Platform [service account](https://cloud.google.com/iam/docs/service-account-overview) with location of the `service_account.json` file stored in the environment
variable: `GOOGLE_APPLICATION_CREDENTIALS`
- Google Cloud Platform project ID stored in the environment variable: `GOOGLE_CLOUD_PROJECT`
- [Google Maps API](https://developers.google.com/maps/documentation/geocoding/get-api-key) key stored in the environment variable: `GOOGLE_MAPS_API_KEY`
- [Google Drive Folder ID](https://ploi.io/documentation/database/where-do-i-get-google-drive-folder-id) stored in the environment variable: `GOOGLE_DRIVE_FOLDER_ID`

## Technical Notes
- Any modules should be added via the `uv add [module]` command.
  - Example: `uv add pre-commit`

## Standard Commands
- `make lint`: Runs`pre-commit` on the codebase.
- `make seed`: Save incidents starting from January 1st of 2011 and continuing until today.
- `make update`: Save incidents starting from the most recently saved incident until today.
- `make build-model`: Build a predictive XGBoost model based off of locally saved incident data and save it in the `data` folder.
- `make categorize`: Categorize stored, 'Information' labeled incidents using the locally saved predictive model.
- `make download`: Download all incidents into a locally stored file titled `incident_dump.csv`.
