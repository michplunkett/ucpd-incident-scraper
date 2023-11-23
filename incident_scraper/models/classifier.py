import re

import numpy as np
import polars as pl
from neattext import remove_non_ascii, remove_puncts, remove_stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.neighbors import KNeighborsClassifier


INCIDENT_FILE = "incident_dump.csv"
INCIDENT_TYPE_INFO = "Information"
KEY_COMMENTS = "comments"
KEY_INCIDENT_TYPE = "incident"
KEY_VALIDATED_LOCATION = "validated_location"
MINIMUM_TYPE_FREQUENCY = 20
NUM_REGEX = re.compile(r"\d+")


class Classifier:
    def __init__(self):
        self._df = (
            pl.read_csv(
                f"./{INCIDENT_FILE}",
            )
            .select(KEY_COMMENTS, KEY_INCIDENT_TYPE)
            .with_columns(pl.col(KEY_COMMENTS).apply(remove_stopwords))
            .with_columns(pl.col(KEY_COMMENTS).apply(remove_non_ascii))
            .with_columns(pl.col(KEY_COMMENTS).apply(remove_puncts))
        )

        self._vectorizer = TfidfVectorizer(
            lowercase=True, max_features=1000, stop_words="english", max_df=0.85
        )
        self._unique_types = self._create_unique_type_list()
        self._clean_data()

    def _create_unique_type_list(self) -> [str]:
        incidents = self._df[KEY_INCIDENT_TYPE].to_list()
        incident_set = set()
        for element in incidents:
            if "/" in element:
                for p in element.split("/"):
                    fmt_element = p.strip().lower()
                    if p:
                        incident_set.add(fmt_element)
            else:
                fmt_element = element.strip().lower()
                incident_set.add(fmt_element)
        incident_set.remove("")
        incident_list = list(incident_set)
        incident_list.sort()
        return incident_list

    def _clean_data(self):
        for i in self._unique_types:
            self._df = self._df.with_columns(
                pl.col(KEY_INCIDENT_TYPE)
                .str.to_lowercase()
                .str.split(" / ")
                .list.eval(
                    pl.element()
                    .str.starts_with(i)
                    .and_(pl.element().str.ends_with(i))
                )
                .list.any()
                .cast(pl.Int8)
                .alias(i),
            )

        self._df = self._df.filter(
            pl.col(KEY_INCIDENT_TYPE) != INCIDENT_TYPE_INFO
        )

        min_type_cnt = (
            self._df.select(pl.sum(*self._unique_types))
            .transpose(include_header=True)
            .filter(pl.col("column_0") > MINIMUM_TYPE_FREQUENCY)
        )

        min_type_cnt_list = [t[0] for t in min_type_cnt.select("column").rows()]

        self._df = self._df.select(
            KEY_COMMENTS, KEY_INCIDENT_TYPE, *min_type_cnt_list
        )

        self._df = self._df.to_pandas(use_pyarrow_extension_array=True)

    def train(self):
        X = self._df[KEY_COMMENTS].tolist()
        y = np.asarray(self._df[self._df.columns[2:]], dtype=int)
        self._vectorizer.fit(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.30, random_state=330
        )

        X_train_tfidf = self._vectorizer.transform(X_train)
        X_test_tfidf = self._vectorizer.transform(X_test)

        clf = MultiOutputClassifier(KNeighborsClassifier()).fit(
            X_train_tfidf, y_train
        )

        prediction = clf.predict(X_test_tfidf)
        print("Accuracy Score: ", accuracy_score(y_test, prediction))
