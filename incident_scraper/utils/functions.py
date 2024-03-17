import re
from datetime import datetime
from typing import Optional

from incident_scraper.utils.constants import (
    INCIDENT_KEY_REPORTED,
    UCPD_DATE_FORMATS,
)


# Source: https://www.geeksforgeeks.org/convert-string-to-title-case-in-python/
def custom_title_case(input_string: str) -> str:
    # List of articles.
    articles = ["a", "an", "the"]

    # List of coordinating conjunctions.
    conjunctions = ["and", "but", "for", "nor", "or", "so", "yet"]

    # List of some short articles.
    prepositions = [
        "in",
        "to",
        "for",
        "with",
        "on",
        "at",
        "from",
        "by",
        "about",
        "as",
        "into",
        "like",
        "through",
        "after",
        "over",
        "between",
        "out",
        "against",
        "during",
        "without",
        "before",
        "under",
        "around",
        "among",
        "of",
        "via",
    ]

    lower_case = articles + conjunctions + prepositions
    output_list = []

    # separating each word in the string
    input_list = input_string.split(" ")

    # checking each word
    for word in input_list:
        # if the word exists in the list
        # then no need to capitalize it
        if word in lower_case:
            output_list.append(word)

        # if the word does not exist in
        # the list, then capitalize it
        else:
            output_list.append(word.title())

    return " ".join(output_list)


def parse_scraped_incident_timestamp(i: dict) -> Optional[str]:
    result = None

    # Compensate for date input irregularities
    i[INCIDENT_KEY_REPORTED] = re.sub(
        r"\s{0}AM", " AM", i[INCIDENT_KEY_REPORTED]
    )
    i[INCIDENT_KEY_REPORTED] = re.sub(
        r"\s{0}PM", " PM", i[INCIDENT_KEY_REPORTED]
    )
    i[INCIDENT_KEY_REPORTED] = re.sub(r"\s{2,}", " ", i[INCIDENT_KEY_REPORTED])
    i[INCIDENT_KEY_REPORTED] = (
        i[INCIDENT_KEY_REPORTED]
        .replace("//", "/")
        .replace("!", "1")
        .replace(" at ", " ")
        .replace(":PM", " PM")
        .replace(":AM", " AM")
        .replace(": PM", " PM")
        .replace(": AM", " AM")
        .replace(": ", ":")
    )

    for time_format in UCPD_DATE_FORMATS:
        try:
            result = datetime.strptime(i[INCIDENT_KEY_REPORTED], time_format)
        except ValueError:
            continue
        # If a date is successfully parsed, break from the loop.
        break

    return result


def determine_season(test_date: datetime) -> str:
    test_date_tuple = (test_date.month, test_date.day)
    if (3, 1) <= test_date_tuple < (5, 31):
        return "Spring"
    elif (6, 1) <= test_date_tuple < (8, 31):
        return "Summer"
    elif (9, 1) <= test_date_tuple < (12, 1):
        return "Fall"
    else:
        return "Winter"
