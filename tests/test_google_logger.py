"""Test the shutdown of the logging client."""

from incident_scraper.external.google_logger import shutdown_logger


class RecordingClient:
    def __init__(self):
        self.calls = []

    def flush_handlers(self):
        self.calls.append("flush_handlers")

    def close(self):
        self.calls.append("close")


def test_pending_logs_are_flushed_before_the_client_is_closed():
    client = RecordingClient()

    shutdown_logger(client)

    assert client.calls == ["flush_handlers", "close"]
