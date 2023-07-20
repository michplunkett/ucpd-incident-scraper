# UChicago Incident Page Scraper
This repository houses a scraping engine for the [UCPD's Incident Report webpage](https://incidentreports.uchicago.edu/). The function is stored and ran on the Google Cloud Platform as a [Cloud Function](https://cloud.google.com/functions).

### Relevant Reading
- Ethical Issues of Crime Mapping: [Link](https://storymaps.arcgis.com/stories/9b71d1fba77641a0ad35b07b23aae66b?utm_source=pocket_saves)

### Project Requirements
- Python version: `^3.11`
- [Poetry](https://python-poetry.org/)

### Instructions to Run the Project
1. Go into the base directory of the repository and type `poetry shell` into the terminal.
2. Run the command `poetry install` to install the requirements.
3. Use the `make run` command.

### Technical Notes
- Any modules should be added via the `poetry add [module]` command.
  - Example: `poetry add black`

## Standard Commands
- `make lint`: Runs `Black`, `isort`, and `ruff` on the codebase
- `make run`: Runs the `main` function in the `incident_scraper` folder
