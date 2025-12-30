import dataclasses
import joblib
import logging
from datetime import datetime, time

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression


@dataclasses.dataclass(frozen=True)
class Constants:
    """Holds constant values for columns."""

    MES: set[int] = dataclasses.field(default_factory=lambda: set(range(1, 13)))
    TIPOVUELO: set[str] = dataclasses.field(
        default_factory=lambda: {"N", "I"}
    )  # Nacional, Internacional
    OPERA: set[str] = dataclasses.field(
        default_factory=lambda: {
            "American Airlines",
            "Air Canada",
            "Air France",
            "Aeromexico",
            "Aerolineas Argentinas",
            "Austral",
            "Avianca",
            "Alitalia",
            "British Airways",
            "Copa Air",
            "Delta Air",
            "Gol Trans",
            "Iberia",
            "K.L.M.",
            "Qantas Airways",
            "United Airlines",
            "Grupo LATAM",
            "Sky Airline",
            "Latin American Wings",
            "Plus Ultra Lineas Aereas",
            "JetSmart SPA",
            "Oceanair Linhas Aereas",
            "Lacsa",
        }
    )


class DataProcessor:
    """
    Handles feature extraction and data splitting for ML workflows.

    Attributes:
        data (pd.DataFrame): Feature matrix.
        targets (Optional[pd.Series]): Target vector if provided.
    """

    CONSTANTS = Constants()
    FEATURES_COLS = [
        "OPERA_Latin American Wings",
        "MES_7",
        "MES_10",
        "OPERA_Grupo LATAM",
        "MES_12",
        "TIPOVUELO_I",
        "MES_4",
        "MES_11",
        "OPERA_Sky Airline",
        "OPERA_Copa Air",
    ]

    def __init__(
        self,
        data: pd.DataFrame,
        target_column: str | None = None,
        thresh_in_minutes: int = 15,
    ) -> None:
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Data must be a pandas DataFrame")

        self.data = data.copy()
        self.targets: pd.DataFrame | None = None
        self._thresh_in_minutes = thresh_in_minutes
        self._target_col = target_column

    def _check_for_targets(self, target_column: str | None) -> None:
        if target_column is not None:
            if target_column not in self.data.columns:
                raise ValueError(f"Target column '{target_column}' not found in data.")

            self.targets = self.data[target_column].to_frame()
            self.data = self.data.drop(columns=[target_column])

    def _input_sanity_checks(self) -> None:
        """
        Validates input data for expected values and formats.

        Raises:
            ValueError: If any of the checks fail.
        """
        for col, valid_values in dataclasses.asdict(self.CONSTANTS).items():
            invalid_values = set(self.data[col].unique()) - valid_values
            if invalid_values:
                raise ValueError(
                    f"Column '{col}' contains invalid values: {invalid_values}"
                )

    @staticmethod
    def get_period_day(date: str) -> str:
        """
        Classifies a datetime string into a period of the day.

        Args:
            date (str): Datetime string in '%Y-%m-%d %H:%M:%S' format.

        Returns:
            str: One of 'mañana', 'tarde', 'noche'.
        """
        date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").time()

        if time(5, 0) <= date_time <= time(11, 59):
            return "mañana"

        if time(12, 0) <= date_time <= time(18, 59):
            return "tarde"

        # Covers 19:00–23:59 and 00:00–04:59
        return "noche"

    @staticmethod
    def is_high_season(fecha: str) -> int:
        """
        Determines whether a given datetime falls within high season.

        High season ranges:
        - Dec 15 - Dec 31
        - Jan 1 - Mar 3
        - Jul 15 - Jul 31
        - Sep 11 - Sep 30

        Args:
            fecha (str): Datetime string in '%Y-%m-%d %H:%M:%S' format.

        Returns:
            int: 1 if high season, 0 otherwise.
        """
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
        year = fecha_dt.year
        ranges = [
            (datetime(year, 12, 15, 23, 59, 59), datetime(year, 12, 31, 23, 59, 59)),
            (datetime(year, 1, 1, 23, 59, 59), datetime(year, 3, 3, 23, 59, 59)),
            (datetime(year, 7, 15, 23, 59, 59), datetime(year, 7, 31, 23, 59, 59)),
            (datetime(year, 9, 11, 23, 59, 59), datetime(year, 9, 30, 23, 59, 59)),
        ]
        for start, end in ranges:
            if start <= fecha_dt <= end:
                return 1

        return 0

    @staticmethod
    def get_min_diff(data: pd.DataFrame) -> float:
        """
        Computes the difference in minutes between Fecha-O and Fecha-I.

        Args:
            data: Mapping containing 'Fecha-O' and 'Fecha-I' in
                '%Y-%m-%d %H:%M:%S' format.

        Returns:
            float: Difference in minutes (can be negative).
        """
        try:
            fecha_o = datetime.strptime(data["Fecha-O"], "%Y-%m-%d %H:%M:%S")
            fecha_i = datetime.strptime(data["Fecha-I"], "%Y-%m-%d %H:%M:%S")
        except KeyError as e:
            raise KeyError("Missing required field") from e
        except ValueError as e:
            raise ValueError("Invalid date format") from e

        return (fecha_o - fecha_i).total_seconds() / 60

    def compute_columns(self) -> None:
        """
        Computes and adds derived feature columns to the internal dataset.

        This method enriches ``self.data`` with time-based and delay-related
        features commonly used in machine learning pipelines:

        - ``period_day``: Categorical feature representing the period of the day
        (e.g., morning, afternoon, night) derived from ``Fecha-I``.
        - ``high_season``: Binary indicator (1/0) denoting whether ``Fecha-I`` falls
        within a predefined high-season date range.
        - ``min_diff``: Numerical feature representing the difference in minutes
        between ``Fecha-O`` and ``Fecha-I``.
        - ``delay``: Binary target/feature indicating whether the delay exceeds
        ``self._thresh_in_minutes``.

        Assumptions:
            - ``self.data`` is a pandas DataFrame containing at least the columns
            ``Fecha-I`` and ``Fecha-O``.
            - ``Fecha-I`` and ``Fecha-O`` are strings or datetime-like values in a
            format compatible with the corresponding helper methods.
            - Helper methods ``get_period_day``, ``is_high_season``, and
            ``get_min_diff`` are implemented and return valid values.
            - ``self._thresh_in_minutes`` is a numeric threshold defining a delay.

        Side Effects:
            - Mutates ``self.data`` in place by adding new columns.

        Returns:
            None
        """
        self.data["period_day"] = self.data["Fecha-I"].apply(self.get_period_day)
        self.data["high_season"] = self.data["Fecha-I"].apply(self.is_high_season)
        self.data["min_diff"] = self.data.apply(self.get_min_diff, axis=1)
        self.data["delay"] = np.where(
            self.data["min_diff"] > self._thresh_in_minutes, 1, 0
        )

        self._check_for_targets(self._target_col)

    def get_features(self) -> pd.DataFrame:
        """
        Generates a feature matrix using one-hot encoding for categorical variables.

        This method transforms selected categorical columns from ``self.data`` into
        a numerical feature matrix suitable for machine learning models. The
        following columns are one-hot encoded and concatenated:

        - ``OPERA``: Airline or operator identifier
        - ``TIPOVUELO``: Flight type (e.g., national or international)
        - ``MES``: Month of the flight

        Each category is encoded using pandas' ``get_dummies`` function with
        prefixed column names to avoid naming collisions.

        Assumptions:
            - ``self.data`` is a pandas DataFrame containing the columns
            ``OPERA``, ``TIPOVUELO``, and ``MES``.
            - The categorical columns do not contain unseen or missing values
            that would break downstream model assumptions.

        Returns:
            pd.DataFrame: A DataFrame containing the one-hot encoded features,
            where each column represents a binary indicator for a category.
        """
        self._input_sanity_checks()
        features = pd.concat(
            [
                pd.get_dummies(self.data["OPERA"], prefix="OPERA"),
                pd.get_dummies(self.data["TIPOVUELO"], prefix="TIPOVUELO"),
                pd.get_dummies(self.data["MES"], prefix="MES"),
            ],
            axis=1,
        )
        return features.reindex(columns=self.FEATURES_COLS, fill_value=0)


class DelayModel:
    DEFAULT_MODEL_FILE = "logreg.joblib"

    def __init__(self):
        self._model: LogisticRegression | None = (  # type: ignore
            None  # Model should be saved in this attribute.
        )
        self.processor: DataProcessor | None = None  # type: ignore

    def preprocess(
        self, data: pd.DataFrame, target_column: str | None = None
    ) -> tuple[pd.DataFrame, pd.DataFrame] | pd.DataFrame:
        """
        Prepare raw data for training or predict.

        Args:
            data (pd.DataFrame): raw data.
            target_column (str, optional): if set, the target is returned.

        Returns:
            Tuple[pd.DataFrame, pd.Series]: features and target.
            or
            pd.DataFrame: features.
        """
        self.processor = DataProcessor(data, target_column)

        if target_column is not None:
            # Will create delay only for training and save computations during inference
            self.processor.compute_columns()

        if self.processor.targets is not None:
            return self.processor.get_features(), self.processor.targets

        return self.processor.get_features()

    def fit(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        """
        Fit model with preprocessed data.

        Args:
            features (pd.DataFrame): preprocessed data.
            target (pd.DataFrame): target.
        """
        col = target.columns[0]
        n_y0 = (target[col] == 0).sum()
        n_y1 = (target[col] == 1).sum()

        self._model = LogisticRegression(
            class_weight={1: n_y0 / len(target), 0: n_y1 / len(target)}
        )
        self._model.fit(features, target)
        self.save()

    def predict(self, features: pd.DataFrame) -> list[int]:
        """
        Predict delays for new flights.

        Args:
            features (pd.DataFrame): preprocessed data.

        Returns:
            (List[int]): predicted targets.
        """
        if self._model is None:
            logging.warning("Inference process failed.")
            return [0] * features.shape[0]

        for column in DataProcessor.FEATURES_COLS:
            if column not in features.columns:
                raise ValueError(f"Column {column} is missed.")

        predictions = self._model.predict(features).tolist()

        return predictions

    def save(self, path: str | None = None) -> None:
        """
        Saves a trained LogisticRegression model to disk.

        Args:
            model (LogisticRegression): Trained sklearn LogisticRegression model.
            path (str): File path where the model will be saved.
        """
        if self._model is None:
            raise RuntimeError("The model is not defined. Please fit the model first.")

        if path is None:
            path = self.DEFAULT_MODEL_FILE

        joblib.dump(self._model, path)

    def load(self, path: str | None = None) -> None:
        """
        Loads a LogisticRegression model from disk.

        Args:
            path (str): File path to the saved model.

        Returns:
            LogisticRegression: Loaded sklearn LogisticRegression model.
        """
        if path is None:
            path = self.DEFAULT_MODEL_FILE

        model = joblib.load(path)

        if not isinstance(model, LogisticRegression):
            raise ValueError(f"The model loaded is not supported: {path}.")

        self._model = model
