import logging
import os
import pickle
from functools import reduce
from typing import Optional

import numpy as np
import polars as pl
from neattext import remove_non_ascii, remove_puncts, remove_stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from xgboost import XGBClassifier

from incident_scraper.utils.constants import INCIDENT_TYPE_INFO
from incident_scraper.utils.functions import custom_title_case


INCIDENT_FILE = "incident_dump.csv"
KEY_COMMENTS = "comments"
KEY_INCIDENT_TYPE = "incident"
KEY_VALIDATED_LOCATION = "validated_location"
MINIMUM_TYPE_FREQUENCY = 20
SAVED_MODEL_LOCATION = (
    os.getcwd().replace("\\", "/")
    + "/incident_scraper/data/xgb_prediction_model.pkl"
)
SAVED_VECTORIZER_LOCATION = (
    os.getcwd().replace("\\", "/") + "/incident_scraper/data/xgb_vectorizer.pkl"
)
SAVED_TYPES_LOCATION = (
    os.getcwd().replace("\\", "/") + "/incident_scraper/data/xgb_types.pkl"
)
TEXT_NORMALIZING_FUNCTIONS = [
    remove_stopwords,
    remove_non_ascii,
    remove_puncts,
    str.lower,
]


class Classifier:
    def __init__(self, build_model: bool = False):
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            max_features=1000,
            stop_words="english",
            max_df=0.85,
        )

        if build_model:
            self._df = (
                pl.read_csv(
                    f"./{INCIDENT_FILE}",
                )
                .select(KEY_COMMENTS, KEY_INCIDENT_TYPE)
                .with_columns(
                    pl.col(KEY_COMMENTS).map_elements(
                        remove_stopwords, return_dtype=pl.String
                    )
                )
                .with_columns(
                    pl.col(KEY_COMMENTS).map_elements(
                        remove_non_ascii, return_dtype=pl.String
                    )
                )
                .with_columns(
                    pl.col(KEY_COMMENTS).map_elements(
                        remove_puncts, return_dtype=pl.String
                    )
                )
            )
            self._unique_types = self._create_unique_type_list()
            self._clean_data()
            self._model = None
        else:
            self._load_model()

    @staticmethod
    def _reset_category_casing(category: str) -> str:
        category = custom_title_case(category)
        replacements: [tuple] = [
            ("Dui", "DUI"),
            ("Cpd", "CPD"),
            ("Uc", "UC"),
            ("Ucpd", "UCPD"),
        ]
        for rep in replacements:
            old, new = rep
            category = category.replace(old, new)

        return category

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

    def _clean_data(self) -> None:
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

    def _train(self) -> None:
        X = self._df[KEY_COMMENTS].tolist()
        y = np.asarray(self._df[self._df.columns[2:]], dtype=int)
        self._vectorizer.fit(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.35
        )

        X_train_tfidf = self._vectorizer.transform(X_train)
        X_test_tfidf = self._vectorizer.transform(X_test)

        self._model = MultiOutputClassifier(
            XGBClassifier(
                eta=0.2, max_depth=10, n_estimators=100, booster="gbtree"
            )
        ).fit(X_train_tfidf, y_train)

        prediction = self._model.predict(X_test_tfidf)
        accuracy = accuracy_score(y_test, prediction)
        precision = precision_score(
            y_test, prediction, average="micro", zero_division=0.0
        )
        recall = recall_score(
            y_test, prediction, average="micro", zero_division=0.0
        )
        logging.info(f"Accuracy Score: {accuracy}")
        logging.info(f"Precision Score: {precision}")
        logging.info(f"Recall Score: {recall}")

    def _save_model(self) -> None:
        pickle.dump(self._model, open(SAVED_MODEL_LOCATION, mode="wb"))
        pickle.dump(
            self._vectorizer, open(SAVED_VECTORIZER_LOCATION, mode="wb")
        )
        pickle.dump(self._unique_types, open(SAVED_TYPES_LOCATION, mode="wb"))

    def _load_model(self) -> None:
        if os.path.isfile(SAVED_MODEL_LOCATION) and os.path.isfile(
            SAVED_VECTORIZER_LOCATION
        ):
            self._model = pickle.load(open(SAVED_MODEL_LOCATION, mode="rb"))
            self._vectorizer = pickle.load(
                open(SAVED_VECTORIZER_LOCATION, mode="rb")
            )
            self._unique_types = pickle.load(
                open(SAVED_TYPES_LOCATION, mode="rb")
            )

    def train_and_save(self) -> None:
        self._train()
        self._save_model()

    def get_predicted_incident_type(self, comment: str) -> Optional[str]:
        comment = reduce(lambda t, f: f(t), TEXT_NORMALIZING_FUNCTIONS, comment)
        vectorized_comment = self._vectorizer.transform([comment])
        prediction = self._model.predict(vectorized_comment).tolist()[0]
        label_indexes = [
            i for i in range(len(prediction)) if prediction[i] == 1
        ]
        if label_indexes:
            labels = [self._unique_types[i] for i in label_indexes]
            return self._reset_category_casing(" / ".join(labels))

        return None
