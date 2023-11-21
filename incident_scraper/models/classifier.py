import polars as pl
from sklearn.feature_extraction.text import TfidfVectorizer

from incident_scraper.utils.constants import (
    TIMEZONE_CHICAGO,
    UCPD_MDY_KEY_DATE_FORMAT,
)

INCIDENT_FILE = "incident_dump.csv"


class Classifier:
    def __init__(self):
        self._df = pl.read_csv(
            "../../incident_dump.csv",
        ).with_columns(
            pl.col("reported")
            .str.strptime(pl.Datetime, format="%Y-%m-%dT%H:%M:%S%z")
            .dt.convert_time_zone(TIMEZONE_CHICAGO),
            pl.col("reported_date").str.to_date(UCPD_MDY_KEY_DATE_FORMAT),
            pl.col("validated_location")
            .str.split(",")
            .cast(pl.List(pl.Float64)),
        )
        self._vectorizer = TfidfVectorizer(max_features=5000, max_df=0.85)
        self._incidents = self._create_parsed_set()


    def _create_parsed_set(self) -> set:
        incidents = self._df["incident"].to_list()
        incident_set = set()
        for element in incidents:
            if "/" in element:
                for p in element.split("/"):
                    fmt_element = p.strip()
                    if p:
                        incident_set.add(fmt_element.title())
            else:
                fmt_element = element.strip()
                incident_set.add(fmt_element.title())
        return incident_set

    def train(self):
        for i in self._incidents:
            self._df = self._df.with_column(pl.lit(0).alias(i))
            
