from datetime import datetime, time

import pytz
from pages import page_grab

from incident_scraper.utils.constants import (
    BASE_UCPD_URL,
    TIMEZONE_CHICAGO,
    UCPD_URL_REPORT_DATE,
)


def get_yesterday_midnight_time():
    """Returns epoch time from yesterday at midnight."""
    # Current date and time in the Chicago time zone
    tz = pytz.timezone(TIMEZONE_CHICAGO)
    today = datetime.now(tz).date()
    # Subtract one day from the current date
    yesterday = today - datetime.timedelta(days=1)
    midnight_utc = tz.localize(datetime.combine(yesterday, time()), is_dst=None)
    return int(midnight_utc.timestamp())


def get_table(
    url: str = UCPD_URL_REPORT_DATE + "1688360400",
):
    """This function takes a URL and returns the table from that day.

    Parameters:
        * url:  a URL to a page of parks

    Returns:
        A list of URLs to each park on the page.
    """
    incident_dict = dict()
    response = page_grab(url)
    container = response.cssselect("thead")
    categories = container[0].cssselect("th")
    incidents = response.cssselect("tbody")
    incident_rows = incidents[0].cssselect("tr")
    for incident in incident_rows:
        if len(incident) == 1:
            continue
        incident_id = str(incident[6].text)
        if incident_id == "None":
            continue
        incident_dict[incident_id] = dict()
        for i in range(len(categories) - 1):
            incident_dict[incident_id][str(categories[i].text)] = incident[
                i
            ].text

    # Track page number, as offset will take you back to zero
    pages = response.cssselect("span.page-link")
    slash_index = pages[0].text.find("/")
    page_number = (
        int(pages[0].text[: slash_index - 1]) if slash_index != -1 else 0
    )
    return incident_dict, page_number


def get_yesterday():
    """Returns yesterday's UCPD Crime reports."""
    yesterday = get_yesterday_midnight_time()
    return get_table(url=BASE_UCPD_URL + str(yesterday))


def get_all_tables(initial_url: str):
    """Goes through all queried tables until we offset back to the first
    table.

    inputs:
        initial_url- a url containing all the queried days in question
        output: json of dictionary of dictionaries of incidents. Keys of the
            outer dictionary are.
    """
    page_number = 100000000
    incidents, _ = get_table(url=initial_url)

    # Find starting offset
    offset_index = int(initial_url.find("offset="))
    offset = int(initial_url[offset_index + 7 :]) + 5

    # Loop until you offset to the start of query
    while page_number != 1:
        rev_dict, page_number = get_table(
            url=BASE_UCPD_URL
            + "?startDate=1293861600&endDate=1688274000&offset="
            + str(offset)
        )
        if page_number == 1:
            break
        incidents.update(rev_dict)
        offset += 5
    return str(incidents)


def export_string(json_string: str):
    """Save JSON String to File."""
    try:
        with open("../output.json", "w") as file:
            file.write(json_string)
        print("JSON has been saved to file successfully.")
    except IOError as e:
        print("Error writing JSON to file:", str(e))


# code to get full history
j = get_all_tables(
    "https://incidentreports.uchicago.edu/incidentReportArchive.php?startDate"
    "=1293861600&endDate=1688274000&offset=0"
)
export_string(j)
