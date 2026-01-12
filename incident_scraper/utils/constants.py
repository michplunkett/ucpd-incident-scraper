"""Contains constants that are used throughout the application."""

import os

import pytz

# Date/Time Constants
UCPD_DATE_FORMATS = [
    "%m/%d/%y %I:%M %p",
    "%-m/%-d/%y %-I:%M %p",
    "%-m/%-d/%y %-I:%M%p",
    "%m/%d/%y %-H:%M",
    "%m/%d/%Y %-H:%M",
    "%-m/%-d/%Y %-H:%M",
]
UCPD_MDY_DATE_FORMAT = "%m/%d/%Y"
UCPD_MDY_KEY_DATE_FORMAT = "%Y-%m-%d"

# Environment Constants
ENV_GCP_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
ENV_GCP_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
ENV_GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# File Constants
FILE_ENCODING_UTF_8 = "utf-8"
FILE_NAME_INCIDENT_DUMP = "incident_dump.csv"
FILE_OPEN_READ = "r"
FILE_OPEN_WRITE = "w"

# File Type Constants
FILE_TYPE_JSON = "json"

# Incident Key Constants
INCIDENT_KEY_ADDRESS = "ValidatedAddress"
INCIDENT_KEY_COMMENTS = "Comments / Nature of Fire"
INCIDENT_KEY_ID = "UCPD_ID"
INCIDENT_KEY_LATITUDE = "ValidatedLatitude"
INCIDENT_KEY_LOCATION = "Location"
INCIDENT_KEY_LONGITUDE = "ValidatedLongitude"
INCIDENT_KEY_REPORTED = "Reported"
INCIDENT_KEY_REPORTED_DATE = f"{INCIDENT_KEY_REPORTED}Date"
INCIDENT_KEY_SEASON = "Season"
INCIDENT_KEY_TYPE = "Incident"
INCIDENT_PREDICTED_TYPE = "Predicted Incident"

# Incident Type Constants
INCIDENT_TYPE_INFO = "Information"

# Location Constants
LOCATION_CHICAGO = "Chicago"
LOCATION_HYDE_PARK = "Hyde Park, Chicago"
LOCATION_ILLINOIS = "IL"
LOCATION_US = "US"
TIMEZONE_KEY_CHICAGO = f"America/{LOCATION_CHICAGO}"
TIMEZONE_CHICAGO = pytz.timezone(TIMEZONE_KEY_CHICAGO)


# System Constants
class SystemFlags:
    BUILD_MODEL = "build-model"
    CATEGORIZE = "categorize"
    DAYS_BACK = "days-back"
    DOWNLOAD = "download"
    LEMMATIZE_CATEGORIES = "lemmatize-categories"
    SEED = "seed"
    UPDATE = "update"
