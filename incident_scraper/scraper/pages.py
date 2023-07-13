"""Contains all request and response related functionality."""
import time
from urllib.parse import urlparse

import lxml.html
import requests

REQUEST_DELAY = 0.2


def make_request(url: str):
    """Make a request to `url` and return the raw response."""
    # Check if URL starts with an allowed domain name
    time.sleep(REQUEST_DELAY)
    print(f"Fetching {url}")
    resp = requests.get(url)
    return resp


def parse_html(html: str):
    """Parse HTML and return the root node."""
    return lxml.html.fromstring(html)


def make_link_absolute(rel_url: str, current_url: str):
    """Create a complete url based on the rel_url parameter.

    Given a relative URL like "/abc/def" or "?page=2" and a complete URL like
    "https://example.com/1/2/3" this function will combine the two yielding a URL like
    "https://example.com/abc/def".
    """
    url = urlparse(current_url)
    if rel_url.startswith("/"):
        return f"{url.scheme}://{url.netloc}{rel_url}"
    elif rel_url.startswith("?"):
        return f"{url.scheme}://{url.netloc}{url.path}{rel_url}"
    else:
        return rel_url


def page_grab(url: str):
    """Grab page and return root node."""
    response = make_request(url)
    root = parse_html(response.text)
    return root
