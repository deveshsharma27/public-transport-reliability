from pathlib import Path

import pandas as pd

from src.validation.validator import validate_file


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"


def test_valid_trip_file_passes():
    file_path = RAW_DIR / "trips_2026_09_01.csv"

    valid_df, invalid_df = validate_file(file_path)

    assert len(valid_df) == 180
    assert len(invalid_df) == 0


def test_duplicate_trip_is_rejected():
    file_path = RAW_DIR / "trips_2026_09_15.csv"

    valid_df, invalid_df = validate_file(file_path)

    assert len(valid_df) == 180
    assert len(invalid_df) == 5

    assert all(
        invalid_df["validation_error"]
        == "duplicate_trip_id_in_file"
    )


def test_negative_values_are_rejected():
    original_file = RAW_DIR / "trips_2026_09_01.csv"

    df = pd.read_csv(original_file)

    df.loc[0, "delay_minutes"] = -10
    df.loc[1, "passenger_count"] = -5

    temp_file = RAW_DIR / "_test_invalid_values.csv"

    df.to_csv(temp_file, index=False)

    try:
        valid_df, invalid_df = validate_file(temp_file)

        assert len(invalid_df) == 2

        errors = set(
            invalid_df["validation_error"]
        )

        assert "negative_delay" in errors
        assert "negative_passenger_count" in errors

    finally:
        temp_file.unlink(missing_ok=True)


def test_missing_route_is_rejected():
    original_file = RAW_DIR / "trips_2026_09_01.csv"

    df = pd.read_csv(original_file)

    df.loc[0, "route_id"] = ""

    temp_file = RAW_DIR / "_test_missing_route.csv"

    df.to_csv(temp_file, index=False)

    try:
        valid_df, invalid_df = validate_file(temp_file)

        assert len(invalid_df) == 1
        assert invalid_df.iloc[0]["validation_error"] == (
            "missing_route_id"
        )

    finally:
        temp_file.unlink(missing_ok=True)