import datetime

from utils import page_grab


def epochtime_yesterdaymidnight():
    """Returns epoch time for yesterday."""
    now = datetime.datetime.now()  # Current date and time in local timezone
    yesterday = now - datetime.timedelta(
        days=1
    )  # Subtract one day from the current date
    midnight_utc = datetime.datetime.combine(
        yesterday.date(), datetime.time(0, 0)
    ).astimezone(datetime.timezone.utc)
    midnight_epoch = int(midnight_utc.timestamp())
    return midnight_epoch


def get_table(
    url="https://incidentreports.uchicago.edu/incidentReportArchive.php?reportDate=1688360400",
):
    """This function takes a URL and returns the table from that day.

    Parameters:
        * url:  a URL to a page of parks

    Returns:
        A list of URLs to each park on the page.
    """
    inc_dict = dict()
    response = page_grab(url)
    container = response.cssselect("thead")
    categories = container[0].cssselect("th")
    incidents = response.cssselect("tbody")
    incident_rows = incidents[0].cssselect("tr")
    for j in incident_rows:
        if len(j) == 1:
            continue
        id = str(j[6].text)
        if id == "None":
            continue
        inc_dict[id] = dict()
        for i in range(len(categories) - 1):
            inc_dict[id][str(categories[i].text)] = j[i].text

    # track page number, as offset will take you back to zero
    pages = response.cssselect("span.page-link")
    slash_index = pages[0].text.find("/")
    if slash_index != -1:
        pagenumber = int(pages[0].text[: slash_index - 1])
    else:
        pagenumber = 0
    return inc_dict, pagenumber


def get_yesterday():
    """Returns Yesterdays UCPD Crime reports."""
    yesterday = epochtime_yesterdaymidnight()
    return get_table(
        url="https://incidentreports.uchicago.edu/incidentReportArchive.php?reportDate="
        + str(yesterday)
    )


# starting at 2011
initialurl = "https://incidentreports.uchicago.edu/incidentReportArchive.php?startDate=1293861600&endDate=1688274000&offset=0"


def get_alltables(initialurl):
    """Goes through all queried tables until we offset back to the first table.
    inputs:
    initialurl- a url containing all the queried days in question
    output:
    json of dictionary of dictionaries of incidents. Keys of the outer dictionary
    are.
    """
    pagenumber = 100000000
    incid_dict, _ = get_table(url=initialurl)

    # find starting offset
    offset_index = int(initialurl.find("offset="))
    offset = int(initialurl[offset_index + 7 :]) + 5

    # loop until you offset to the start of query
    while pagenumber != 1:
        rev_dict, pagenumber = get_table(
            url="https://incidentreports.uchicago.edu/incidentReportArchive.php?startDate=1293861600&endDate=1688274000&offset="
            + str(offset)
        )
        if pagenumber == 1:
            break
        incid_dict.update(rev_dict)
        offset += 5
    fullreport = str(incid_dict)
    return fullreport


def export_string(jsonString):
    """Save JSON String to File."""
    try:
        with open("output.json", "w") as file:
            file.write(jsonString)
        print("JSON has been saved to file successfully.")
    except IOError as e:
        print("Error writing JSON to file:", str(e))


# code to get full history
j = get_alltables(initialurl)
export_string(j)
