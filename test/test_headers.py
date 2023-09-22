"""Test functionality of Header class."""
from incident_scraper.scraper.headers import Headers


def test_header_randomization():
    """Test functionality of Header class randomization."""
    header = Headers(seed=999)
    rand_header = header.get_random_header()
    rand_header_2 = header.get_random_header()

    assert (
        rand_header
        == "Mozilla/5.0(iPad; U; CPU OS 4_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F191 Safari/6533.18.5"
        and rand_header_2
        == "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Win64; x64; Trident/7.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; InfoPath.3; Tablet PC 2.0; MDDRJS)"
    )
