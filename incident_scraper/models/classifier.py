import numpy as np
import pandas as pd
import polars as pl
import polars.selectors as cs
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

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
        self._vectorizer = CountVectorizer(
            analyzer="word", max_features=5000, min_df=0.85
        )
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

        X = self._df.select("comments").to_pandas(
            use_pyarrow_extension_array=True
        )
        y = np.asarray(self._df.select(cs.by_name(*self._incidents)))
        self._vectorizer.fit(X)
        print(X)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=334
        )
        self._vectorizer.transform(X_train)
        self._vectorizer.transform(X_test)

        train_ratio = 0.70
        validation_ratio = 0.20
        test_ratio = 0.10

        # performing train test split
        x_train, x_test, y_train, y_test = train_test_split(
            X, y, test_size=1 - train_ratio
        )

        # performing test validation split
        x_val, x_test, y_val, y_test = train_test_split(
            x_test,
            y_test,
            test_size=test_ratio / (test_ratio + validation_ratio),
        )

        # initializing all the base model objects with default parameters
        model_1 = LinearRegression()
        model_2 = XGBRegressor()
        model_3 = RandomForestRegressor()

        # training all the model on the train dataset

        # training first model
        model_1.fit(x_train, y_train)
        val_pred_1 = model_1.predict(x_val)
        test_pred_1 = model_1.predict(x_test)

        # converting to dataframe
        val_pred_1 = pd.DataFrame(val_pred_1)
        test_pred_1 = pd.DataFrame(test_pred_1)

        # training second model
        model_2.fit(x_train, y_train)
        val_pred_2 = model_2.predict(x_val)
        test_pred_2 = model_2.predict(x_test)

        # converting to dataframe
        val_pred_2 = pd.DataFrame(val_pred_2)
        test_pred_2 = pd.DataFrame(test_pred_2)

        # training third model
        model_3.fit(x_train, y_train)
        val_pred_3 = model_1.predict(x_val)
        test_pred_3 = model_1.predict(x_test)

        # converting to dataframe
        val_pred_3 = pd.DataFrame(val_pred_3)
        test_pred_3 = pd.DataFrame(test_pred_3)

        # concatenating validation dataset along with all the predicted validation data (meta features)
        df_val = pd.concat([x_val, val_pred_1, val_pred_2, val_pred_3], axis=1)
        df_test = pd.concat(
            [x_test, test_pred_1, test_pred_2, test_pred_3], axis=1
        )

        # making the final model using the meta features
        final_model = LinearRegression()
        final_model.fit(df_val, y_val)

        # getting the final output
        pred_final = final_model.predict(df_test)

        # printing the mean squared error between real value and predicted value
        print(mean_squared_error(y_test, pred_final))
