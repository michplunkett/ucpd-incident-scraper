import re
from datetime import datetime
from typing import Optional, Tuple

from incident_scraper.utils.constants import (
    INCIDENT_KEY_REPORTED,
    UCPD_DATE_FORMATS,
)


def create_street_tuple(
    street: str, blvd: bool = False
) -> Tuple[str, str, str]:
    street_type = "Ave." if not blvd else "Blvd."

    return street, f"S. {street}", f"S. {street} {street_type}"


STREET_CORRECTIONS = [
    create_street_tuple("Blackstone"),
    create_street_tuple("Cottage Grove"),
    create_street_tuple("Cornell"),
    create_street_tuple("Dorchester"),
    create_street_tuple("Drexel"),
    create_street_tuple("East End"),
    create_street_tuple("Ellis"),
    create_street_tuple("Everett"),
    create_street_tuple("Greenwood"),
    create_street_tuple("Harper"),
    create_street_tuple("Hyde Park", blvd=True),
    create_street_tuple("Ingleside"),
    create_street_tuple("Kenwood"),
    create_street_tuple("Kimbark"),
    create_street_tuple("Lake Park"),
    create_street_tuple("Maryland"),
    create_street_tuple("Oakenwald"),
    create_street_tuple("Oakwood", blvd=True),
    ("Shore", "S. Shore", "South Shore Dr."),
    create_street_tuple("Stony Island"),
    create_street_tuple("University"),
    create_street_tuple("Woodlawn"),
]


def address_correction(address: str) -> str:
    address = (
        address.replace("&", "and")
        .replace(" Drive ", " Dr. ")
        .replace(" .s ", " .S ")
        .replace(" .e ", " .E ")
        .replace(" st. ", " St. ")
        .replace(" Pl ", " Pl. ")
        .replace(" pl. ", " Pl. ")
        .replace("Midway Pl.", "Midway Plaisance")
    )

    address = re.sub(r"\s{2,}", " ", address)

    numerical_streets = [make_ordinal(s) for s in range(37, 66)]
    for s in numerical_streets:
        dir_s = f"E. {s}"
        if s in address and dir_s not in address:
            address = address.replace(s, dir_s)

        full_s = f"{dir_s} St."
        if (
            dir_s in address
            and full_s not in address
            and f"{s} Pl" not in address
        ):
            address = address.replace(dir_s, full_s)

    for sc in STREET_CORRECTIONS:
        name, dir_name, full_name = sc

        if name in address and dir_name not in address:
            address = address.replace(name, dir_name)

        if dir_name in address and full_name not in address:
            address = address.replace(dir_name, full_name)

    return address


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


# Source: https://stackoverflow.com/a/50992575
def make_ordinal(n: int) -> str:
    """
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    """
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix


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
