"""Test functionality of Header class."""
import random

from incident_scraper.scraper.headers import Headers


def test_header_randomization():
    """Test functionality of Header class randomization."""
    header = Headers(seed=999)
    rand_header = header.get_random_header()

    assert (
        rand_header
        == "Mozilla/5.0(iPad; U; CPU OS 4_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F191 Safari/6533.18.5"
    )
