# UChicago Incident Page Scraper
This repository houses a scraping engine for the [UCPD's Incident Report webpage](https://incidentreports.uchicago.edu/). The data is stored on
[Google Cloud Platform's Datastore](https://cloud.google.com/datastore) and ran using [GitHub Actions](https://docs.github.com/en/actions).

## Primary Application Functions
Scrape the UCPD Incident Report webpage every weekday morning, pulling all incidents from the latest reported incident date in the Google Datastore to the current day.

## Relevant Reading
- Ethical Issues of Crime Mapping: [Link](https://storymaps.arcgis.com/stories/9b71d1fba77641a0ad35b07b23aae66b?utm_source=pocket_saves)
- The Maroon Launches UChicago Police Department Incident Reporter: [Link](https://chicagomaroon.com/41255/grey-city/the-maroon-launches-uchicago-police-department-incident-reporter/)

## Acknowledgements
I'd like to thank [@kdumais111](https://github.com/kdumais111) and [@FedericoDM](https://github.com/FedericoDM) for their incredible help in getting the scraping architecture in place.
As well as [@ehabich](https://github.com/ehabich) for adding a bit of testing validation to the project. Thanks, y'all! <3

## Project Requirements
- Python version: `^3.14`
- `uv` version: `0.5.7`
  - Download at: [link](https://docs.astral.sh/uv/).

### Required Credentials
- [Census API Key](https://api.census.gov/data/key_signup.html) stored in the environment variable: `CENSUS_API_KEY`
- Google Cloud Platform [service account](https://cloud.google.com/iam/docs/service-account-overview) with location of the `service_account.json` file stored in the environment
variable: `GOOGLE_APPLICATION_CREDENTIALS`
- Google Cloud Platform project ID stored in the environment variable: `GOOGLE_CLOUD_PROJECT`
- [Google Maps API](https://developers.google.com/maps/documentation/geocoding/get-api-key) key stored in the environment variable: `GOOGLE_MAPS_API_KEY`

## Technical Notes
- Any modules should be added via the `uv add [module]` command.
  - Example: `uv add pre-commit`

## Standard Commands
- `make build-model`: Build a predictive neural network (three hidden layers) based off of locally saved incident data and save it in the `data` folder. Commit the rebuilt files in `data` so the scheduled `update` job uses them.
- `make categorize`: Categorize stored, 'Information' labeled incidents using the locally saved predictive model.
- `make download`: Download all incidents into a locally stored file titled `incident_dump.csv`.
- `make env`: Creates or activates a `uv` virtual environment.
- `make lint`: Runs`pre-commit` on the codebase.
- `make seed`: Save incidents starting from January 1st of 2011 and continuing until today.
- `make update`: Save incidents starting from the most recently saved incident until today.

## Incident Type Model
'Information' incidents are categorized by a neural network (three hidden layers) trained on TF-IDF features of the incident comments. It replaced an XGBoost model after the two were compared on the same data.

Each model was trained and scored on the same three random 65/35 train/test splits for every feature set, and the table shows the mean ± standard deviation across those splits. Accuracy is strict: every label of an incident has to match. Precision, recall and F1 are micro-averaged. The times are seconds to fit and to predict the whole test set.

The feature sets are `baseline` (1,000 single-word terms, what the model uses), `5k_unigrams` (5,000 single words) and `5k_bigrams` (5,000 single words and two-word phrases).

| model                        | accuracy        | precision       | recall          | f1              | fit_seconds      | predict_seconds |
|------------------------------|-----------------|-----------------|-----------------|-----------------|------------------|-----------------|
| xgboost [baseline]           | 0.7320 ± 0.0008 | 0.9022 ± 0.0029 | 0.7981 ± 0.0016 | 0.8470 ± 0.0022 | 29.6859 ± 1.1088 | 0.2299 ± 0.0084 |
| neural_network [baseline]    | 0.7472 ± 0.0045 | 0.8914 ± 0.0050 | 0.8143 ± 0.0011 | 0.8511 ± 0.0020 | 8.8608 ± 1.2693  | 0.0264 ± 0.0002 |
| xgboost [5k_unigrams]        | 0.7340 ± 0.0024 | 0.9011 ± 0.0014 | 0.8014 ± 0.0018 | 0.8483 ± 0.0009 | 35.4232 ± 0.1379 | 0.2747 ± 0.0194 |
| neural_network [5k_unigrams] | 0.7242 ± 0.0024 | 0.8923 ± 0.0111 | 0.7919 ± 0.0097 | 0.8390 ± 0.0034 | 32.3943 ± 2.2905 | 0.0285 ± 0.0013 |
| xgboost [5k_bigrams]         | 0.7352 ± 0.0039 | 0.9040 ± 0.0053 | 0.7991 ± 0.0025 | 0.8483 ± 0.0037 | 53.4456 ± 0.7072 | 0.2940 ± 0.0330 |
| neural_network [5k_bigrams]  | 0.7313 ± 0.0043 | 0.8916 ± 0.0073 | 0.8006 ± 0.0017 | 0.8436 ± 0.0030 | 30.4135 ± 6.8297 | 0.0343 ± 0.0017 |

The two models score about the same, with the network training roughly 3x faster and predicting roughly 9x faster. Larger vocabularies did not help either model, so the network uses the baseline features.
