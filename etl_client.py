from __future__ import annotations

import argparse
import asyncio
import json
import os
from abc import ABCMeta, abstractmethod
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import pytz
import requests

#################
# General Utils #
#################


class Singleton:
    SINGLETON_INSTANCE: Optional[Singleton] = None

    def __new__(cls, *args, **kwargs) -> Singleton:
        if cls.SINGLETON_INSTANCE is None:
            cls.SINGLETON_INSTANCE = object.__new__(cls, *args, **kwargs)
        return cls.SINGLETON_INSTANCE


SLEEP_SECONDS = 1
MAX_NUM_URL_ATTEMPTS = 5


async def get_url_data(url: str) -> str:
    for _ in range(MAX_NUM_URL_ATTEMPTS):
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        await asyncio.sleep(SLEEP_SECONDS)
    raise RuntimeError(
        f"Could not get results from {url} after {MAX_NUM_URL_ATTEMPTS} attempts"
    )


####################
# Extraction Utils #
####################


def simplify_column_names(df: pd.DataFrame) -> pd.DataFrame:
    new_names = [c.strip().lower().replace(" ", "_") for c in df.columns]
    assert len(set(new_names)) == len(df.columns)
    return df.rename(columns={old: new for old, new in zip(df.columns, new_names)})


def _columns_are_valid(df: pd.DataFrame) -> bool:
    column_names_are_sane = set(df.columns) == {
        "naive_timestamp",
        "variable",
        "value",
        "last_modified_utc",
    }
    return (
        column_names_are_sane
        and pd.api.types.is_object_dtype(df["naive_timestamp"])
        and pd.api.types.is_int64_dtype(df["variable"])
        and pd.api.types.is_float_dtype(df["value"])
        and pd.api.types.is_datetime64tz_dtype(df["last_modified_utc"])
        and df["last_modified_utc"].dt.tz == pytz.UTC
    )


class ExtractionDetails(Singleton, metaclass=ABCMeta):
    @abstractmethod
    def get_output_file_basename(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_url(self, api_key: str, day: date) -> str:
        raise NotImplementedError

    @abstractmethod
    def convert_raw_data_to_df(self, raw_data: str) -> pd.DataFrame:
        raise NotImplementedError


async def _extract_data_for_single_day(
    extraction_details: ExtractionDetails, api_key: str, day: date
) -> pd.DataFrame:
    url = extraction_details.get_url(api_key, day)
    data = await get_url_data(url)
    return extraction_details.convert_raw_data_to_df(data)


async def _extract_data_for_days(
    extraction_details: ExtractionDetails, api_key: str, days: Iterable[date]
) -> pd.DataFrame:
    sub_tasks = (
        _extract_data_for_single_day(extraction_details, api_key, day) for day in days
    )
    dfs = await asyncio.gather(*sub_tasks)
    df = pd.concat(dfs)
    assert _columns_are_valid(df)
    return df


async def extract_data_to_directory(
    extraction_details: ExtractionDetails,
    output_dir: Path,
    api_key: str,
    days: Iterable[date],
) -> None:
    df = await _extract_data_for_days(extraction_details, api_key, days)
    output_location = output_dir / extraction_details.get_output_file_basename()
    df.to_hdf(output_location, key="df", mode="w")
    assert pd.read_hdf(output_location).equals(df)
    return


###########
# Extract #
###########


class SolarExtractionDetails(ExtractionDetails):
    def get_output_file_basename(self) -> str:
        return "solar.h5"

    def get_url(self, api_key: str, day: date) -> str:
        return f"http://127.0.0.1:8000/{day:%Y-%m-%d}/renewables/solargen.json?api_key={api_key}"

    def convert_raw_data_to_df(self, json_str: str) -> pd.DataFrame:
        df = pd.DataFrame(json.loads(json_str))
        df = simplify_column_names(df)
        df["naive_timestamp"] = df["naive_timestamp"].astype(str)
        df["last_modified_utc"] = pd.to_datetime(
            df["last_modified_utc"] * 1e6
        ).dt.tz_localize(pytz.timezone("UTC"))
        return df


class WindExtractionDetails(ExtractionDetails):
    def get_output_file_basename(self) -> str:
        return "wind.h5"

    def get_url(self, api_key: str, day: date) -> str:
        return f"http://127.0.0.1:8000/{day:%Y-%m-%d}/renewables/windgen.csv?api_key={api_key}"

    def convert_raw_data_to_df(self, csv_str: str) -> pd.DataFrame:
        df = pd.read_csv(StringIO(csv_str))
        df = simplify_column_names(df)
        df["last_modified_utc"] = pd.to_datetime(df["last_modified_utc"]).dt.tz_convert(
            pytz.timezone("UTC")
        )
        return df


OUTPUT_PATH = Path("./output")


def extract_data(
    api_key: str,
    days: Iterable[date],
) -> None:
    if not OUTPUT_PATH.exists():
        os.makedirs(OUTPUT_PATH)
    extraction_details = [SolarExtractionDetails(), WindExtractionDetails()]
    tasks = (
        extract_data_to_directory(ed, OUTPUT_PATH, api_key, days)
        for ed in extraction_details
    )
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
    return


###############
# Main Driver #
###############


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api-key", help="The API key used to extract the data from the data source."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    days = [date.today() - timedelta(days=i) for i in range(7)]
    extract_data(args.api_key, days)
    return


if __name__ == "__main__":
    main()
