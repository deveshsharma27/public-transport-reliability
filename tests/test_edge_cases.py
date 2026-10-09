from pathlib import Path

import pandas as pd

from src.validation.validator import validate_file


BASE_DIR = Path(__file__).resolve().parents[1]


def test_edge_cases_are_rejected():
    source_file = (
        BASE_DIR
        / "data"
        / "test_input"
        / "edge_cases.csv"
    )

    df = pd.read_csv(source_file)

    # The fixture intentionally contains invalid records.
    assert len(df) == 5

    temp_file = (
        BASE_DIR
        / "data"
        / "test_input"
        / "_edge_case_test.csv"
    )

    df.to_csv(temp_file, index=False)

    try:
        valid_df, invalid_df = validate_file(temp_file)

        assert len(valid_df) == 0
        assert len(invalid_df) == 5

        errors = set(
            invalid_df["validation_error"]
        )

        assert "missing_route_id" in errors
        assert "negative_passenger_count" in errors
        assert "negative_delay" in errors
        assert "actual_arrival_before_departure" in errors
        assert "duplicate_trip_id_in_file" in errors

    finally:
        temp_file.unlink(missing_ok=True)