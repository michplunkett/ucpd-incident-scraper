import numpy as np
import polars as pl
import polars.selectors as cs
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

from incident_scraper.utils.constants import (
    TIMEZONE_KEY_CHICAGO,
    UCPD_MDY_KEY_DATE_FORMAT,
)


INCIDENT_FILE = "incident_dump.csv"
KEY_INCIDENT = "incident"
KEY_VALIDATED_LOCATION = "validated_location"


class Classifier:
    def __init__(self):
        self._df = pl.read_csv(
            "./incident_dump.csv",
        ).with_columns(
            pl.col("reported")
            .str.strptime(pl.Datetime, format="%Y-%m-%dT%H:%M:%S%z")
            .dt.convert_time_zone(TIMEZONE_KEY_CHICAGO),
            pl.col("reported_date").str.to_date(UCPD_MDY_KEY_DATE_FORMAT),
            pl.col(KEY_VALIDATED_LOCATION)
            .str.split(",")
            .cast(pl.List(pl.Float64)),
        )
        self._vectorizer = TfidfVectorizer(max_features=5000, max_df=0.85)
        self._incidents = self._create_parsed_list()
        self._incidents.sort()

    def _create_parsed_list(self) -> [str]:
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
        incident_set.remove("")
        return list(incident_set)

    def train(self):
        # Mark which KEY_INCIDENT contains a given incident
        for i in self._incidents:
            self._df = self._df.with_columns(
                [
                    pl.col(KEY_INCIDENT)
                    .str.split(" / ")
                    .list.eval(
                        pl.element()
                        .str.starts_with(i)
                        .and_(pl.element().str.ends_with(i))
                    )
                    .list.any()
                    .cast(pl.Int8)
                    .alias(i)
                ],
            ).drop("")

        X = self._df.select("comments")
        y = np.asarray(self._df.select(cs.by_name(self._incidents)))
        self._vectorizer.fit(X)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.30
        )
        self._vectorizer.transform(X_train)
        self._vectorizer.transform(X_test)
