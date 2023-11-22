import re

import numpy as np
import pandas as pd
import polars as pl
from neattext.functions import remove_non_ascii, remove_puncts, remove_stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier


INCIDENT_FILE = "incident_dump.csv"
KEY_COMMENTS = "comments"
KEY_INCIDENT_TYPE = "incident"
KEY_VALIDATED_LOCATION = "validated_location"
INCIDENT_TYPE_INFO = "Information"
NUM_REGEX = re.compile(r"\d+")


class Classifier:
    def __init__(self):
        self._df = pl.read_csv(
            f"./{INCIDENT_FILE}",
        ).select(KEY_COMMENTS, KEY_INCIDENT_TYPE)

        self._vectorizer = TfidfVectorizer(
            lowercase=True, max_features=2500, stop_words="english", max_df=0.9
        )
        self._unique_types = self._create_unique_type_list()
        self._unique_types.sort()

        # Mark which KEY_INCIDENT contains a given incident
        for i in self._unique_types:
            self._df = self._df.with_columns(
                [
                    pl.col(KEY_INCIDENT_TYPE)
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
            )
        self._df = self._df.filter(
            pl.col(KEY_INCIDENT_TYPE) != INCIDENT_TYPE_INFO
        )
        self._df = self._df.select(pl.col(KEY_COMMENTS).apply(remove_stopwords))
        self._df = self._df.select(pl.col(KEY_COMMENTS).apply(remove_non_ascii))
        self._df = self._df.select(pl.col(KEY_COMMENTS).apply(remove_puncts))

        self._df.write_csv("./dat_new_new.csv", separator=",")

        self._df = self._df.to_pandas(use_pyarrow_extension_array=True)

    def get_vectorized(self):
        df = self._df.to_pandas()

        # vectorize input/x/"comments"
        text = list(df["comments"])
        text = [NUM_REGEX.sub(" ", t) for t in text]  # remove numbers
        x_count_vector = self._vectorizer.fit(text)
        x_df = pd.DataFrame(
            data=x_count_vector,
            columns=self._vectorizer.get_feature_names_out(),
        )
        x_df.index = text

        for i in self._unique_types:
            self._df = self._df.with_columns(
                [
                    pl.col(KEY_INCIDENT_TYPE)
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
            )
            y_df = self._df.to_pandas().iloc[:, 10:]

            self.x = x_df
            self.y = y_df

    def _create_unique_type_list(self) -> [str]:
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
        incident_set.remove(INCIDENT_TYPE_INFO)
        return list(incident_set)

    def train(self):
        X = self._df[KEY_COMMENTS].tolist()
        y = np.asarray(self._df[self._df.columns[2:]], dtype=int)
        self._vectorizer.fit(X)
        print(y)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.30, random_state=42
        )

        X_train_tfidf = self._vectorizer.transform(X_train)
        X_test_tfidf = self._vectorizer.transform(X_test)

        clf = MultiOutputClassifier(LogisticRegression()).fit(
            X_train_tfidf, y_train
        )

        prediction = clf.predict(X_test_tfidf)
        print(prediction)
        print("Accuracy Score: ", accuracy_score(y_test, prediction))
