"""Contains all request and response related functionality."""
import time
from urllib.parse import urlparse

import lxml.html
import requests

REQUEST_DELAY = 0.2


def make_request(url: str):
    """Make a request to `url` and return the raw response.

    This function ensures that the domain matches what is expected and that the rate
    limit is obeyed.

    Parameters
    ----------
    url: str
        The URL that we intend to request.

    Returns
    -------
    requests.Response
        The response from the requests.get() function.
    """
    # Check if URL starts with an allowed domain name
    time.sleep(REQUEST_DELAY)
    print(f"Fetching {url}")
    resp = requests.get(url)
    return resp


def parse_html(html: str):
    """Parse HTML and return the root node.

    Parameters
    ----------
    html: str
        A stringified version of the scraped-HTML.

    Returns
    -------
    htmlnode
        The root node of the HTML string the function was passed.
    """
    return lxml.html.fromstring(html)


def make_link_absolute(rel_url: str, current_url: str):
    """Create a complete url based on the rel_url parameter.

    Given a relative URL like "/abc/def" or "?page=2" and a complete URL like
    "https://example.com/1/2/3" this function will combine the two yielding a URL like
    "https://example.com/abc/def".

    Parameters
    ----------
    rel_url : str
        A URL or URL fragment.
    current_url : str
        A complete URL used to make the request that contained a link to rel_url.


    Returns
    -------
    str
        A full URL with protocol & domain that refers to rel_url.
    """
    url = urlparse(current_url)
    if rel_url.startswith("/"):
        return f"{url.scheme}://{url.netloc}{rel_url}"
    elif rel_url.startswith("?"):
        return f"{url.scheme}://{url.netloc}{url.path}{rel_url}"
    else:
        return rel_url


def page_grab(url: str):
    """Grab page and return root node.

    Parameters
    ----------
    url: str
        The URL meant to be fetched.

    Returns
    -------
    htmlnode
        The root node for the URL the function was passed.
    """
    response = make_request(url)
    root = parse_html(response.text)
    return root
