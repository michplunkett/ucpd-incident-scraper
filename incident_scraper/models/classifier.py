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
        self.__vectorizer = TfidfVectorizer(
            lowercase=True,
            max_features=1000,
            stop_words="english",
            max_df=0.85,
        )

        if build_model:
            self.__df = (
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
            self.__unique_types = self.__create_unique_type_list()
            self.__clean_data()
            self.__model = None
        else:
            self.__load_model()

    @staticmethod
    def __reset_category_casing(category: str) -> str:
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

    def __create_unique_type_list(self) -> [str]:
        incidents = self.__df[KEY_INCIDENT_TYPE].to_list()
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

    def __clean_data(self) -> None:
        for i in self.__unique_types:
            self.__df = self.__df.with_columns(
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

        self.__df = self.__df.filter(
            pl.col(KEY_INCIDENT_TYPE) != INCIDENT_TYPE_INFO
        )

        min_type_cnt = (
            self.__df.select(pl.sum(*self.__unique_types))
            .transpose(include_header=True)
            .filter(pl.col("column_0") > MINIMUM_TYPE_FREQUENCY)
        )

        min_type_cnt_list = [t[0] for t in min_type_cnt.select("column").rows()]

        self.__df = self.__df.select(
            KEY_COMMENTS, KEY_INCIDENT_TYPE, *min_type_cnt_list
        )

        self.__df = self.__df.to_pandas(use_pyarrow_extension_array=True)

    def __train(self) -> None:
        X = self.__df[KEY_COMMENTS].tolist()
        y = np.asarray(self.__df[self.__df.columns[2:]], dtype=int)
        self.__vectorizer.fit(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.35
        )

        X_train_tfidf = self.__vectorizer.transform(X_train)
        X_test_tfidf = self.__vectorizer.transform(X_test)

        self.__model = MultiOutputClassifier(
            XGBClassifier(
                eta=0.2, max_depth=10, n_estimators=100, booster="gbtree"
            )
        ).fit(X_train_tfidf, y_train)

        prediction = self.__model.predict(X_test_tfidf)
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

    def __save_model(self) -> None:
        pickle.dump(self.__model, open(SAVED_MODEL_LOCATION, mode="wb"))
        pickle.dump(
            self.__vectorizer, open(SAVED_VECTORIZER_LOCATION, mode="wb")
        )
        pickle.dump(self.__unique_types, open(SAVED_TYPES_LOCATION, mode="wb"))

    def __load_model(self) -> None:
        if os.path.isfile(SAVED_MODEL_LOCATION) and os.path.isfile(
            SAVED_VECTORIZER_LOCATION
        ):
            self.__model = pickle.load(open(SAVED_MODEL_LOCATION, mode="rb"))
            self.__vectorizer = pickle.load(
                open(SAVED_VECTORIZER_LOCATION, mode="rb")
            )
            self.__unique_types = pickle.load(
                open(SAVED_TYPES_LOCATION, mode="rb")
            )

    def train_and_save(self) -> None:
        self.__train()
        self.__save_model()

    def get_predicted_incident_type(self, comment: str) -> Optional[str]:
        comment = reduce(lambda t, f: f(t), TEXT_NORMALIZING_FUNCTIONS, comment)
        vectorized_comment = self.__vectorizer.transform([comment])
        prediction = self.__model.predict(vectorized_comment).tolist()[0]
        label_indexes = [
            i for i in range(len(prediction)) if prediction[i] == 1
        ]
        if label_indexes:
            labels = [self.__unique_types[i] for i in label_indexes]
            return self.__reset_category_casing(" / ".join(labels))

        return None
