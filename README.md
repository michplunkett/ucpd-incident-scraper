# UChicago Incident Page Scraper
This repository houses a scraping engine for the [UCPD's Incident Report webpage](https://incidentreports.uchicago.edu/). The function is stored and ran on the Google Cloud Platform as a [Cloud Function](https://cloud.google.com/functions).

### Project Requirements
- Python version: `^3.11`
- [Poetry](https://python-poetry.org/)

### Instructions to Run the Project
1. Go into the base directory of the repository and type `poetry shell` into the terminal.
2. Use the `make run` command.

### Technical Notes
- Any modules should be added via the `poetry add [module]` command.
  - Example: `poetry add pytest`

## Standard Commands
- `make format`: Runs `Black` on the codebase
- `make lint`: Runs `ruff` on the codebase
- `make test`: Runs test cases in the `test` directory
- `make run`: Runs the `main` function in the `incident_scraper` folder
