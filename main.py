import os

from flask import Flask

from incident_scraper.__main__ import update_records

app = Flask(__name__)

@app.route("/")
def update_incidents():
    """Update incidents based on the most recent scrape date."""
    update_records()
    return 1


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
