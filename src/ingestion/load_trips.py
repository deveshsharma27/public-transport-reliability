from pathlib import Path
from datetime import date, datetime
import math

import pandas as pd
from sqlalchemy import text

from src.db import get_engine


BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PIPELINE_NAME = "public_transport_reliability"


def get_last_processed_date(connection):
    """Get the last successfully processed service date."""
    result = connection.execute(
        text(
            """
            SELECT last_processed_date
            FROM pipeline_state
            WHERE pipeline_name = :pipeline_name
            """
        ),
        {"pipeline_name": PIPELINE_NAME},
    ).scalar_one_or_none()

    return result


def convert_value(value):
    """Convert Pandas missing/datetime values to database-friendly values."""
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if isinstance(value, float) and math.isnan(value):
        return None

    return value


def load_one_file(connection, file_path: Path) -> int:
    """Load one validated daily file into the trips table."""
    df = pd.read_csv(file_path)

    required_columns = [
        "trip_id",
        "service_date",
        "route_id",
        "scheduled_departure",
        "scheduled_arrival",
        "actual_departure",
        "actual_arrival",
        "delay_minutes",
        "status",
        "vehicle_id",
        "passenger_count",
        "weather_condition",
        "traffic_level",
        "event_type",
        "source_file",
    ]

    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"{file_path.name} is missing columns: {sorted(missing)}"
        )

    # Convert dates and timestamps
    df["service_date"] = pd.to_datetime(
        df["service_date"]
    ).dt.date

    datetime_columns = [
        "scheduled_departure",
        "scheduled_arrival",
        "actual_departure",
        "actual_arrival",
    ]

    for column in datetime_columns:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
        )

    # Convert missing Pandas values to None
    records = []

    for row in df.to_dict(orient="records"):
        clean_row = {
            key: convert_value(value)
            for key, value in row.items()
        }
        records.append(clean_row)

    insert_sql = text(
        """
        INSERT INTO trips (
            trip_id,
            service_date,
            route_id,
            scheduled_departure,
            scheduled_arrival,
            actual_departure,
            actual_arrival,
            delay_minutes,
            status,
            vehicle_id,
            passenger_count,
            weather_condition,
            traffic_level,
            event_type,
            source_file
        )
        VALUES (
            :trip_id,
            :service_date,
            :route_id,
            :scheduled_departure,
            :scheduled_arrival,
            :actual_departure,
            :actual_arrival,
            :delay_minutes,
            :status,
            :vehicle_id,
            :passenger_count,
            :weather_condition,
            :traffic_level,
            :event_type,
            :source_file
        )
        ON CONFLICT (trip_id) DO NOTHING
        """
    )

    result = connection.execute(
        insert_sql,
        records,
    )

    return result.rowcount


def load_incrementally():
    """Load new validated daily files in chronological order."""
    engine = get_engine()

    files = sorted(
        PROCESSED_DIR.glob("clean_trips_*.csv")
    )

    if not files:
        raise FileNotFoundError(
            f"No processed files found in {PROCESSED_DIR}"
        )

    total_inserted = 0
    total_skipped = 0

    with engine.begin() as connection:
        last_processed_date = get_last_processed_date(connection)

        print(
            f"Last processed date: "
            f"{last_processed_date or 'None'}"
        )

        for file_path in files:

            # Read service date from the file
            df = pd.read_csv(
                file_path,
                usecols=["service_date"],
            )

            file_date = pd.to_datetime(
                df["service_date"].iloc[0]
            ).date()

            # Skip files that have already been processed
            if (
                last_processed_date is not None
                and file_date <= last_processed_date
            ):
                print(
                    f"SKIPPED {file_path.name} "
                    f"(already processed)"
                )
                continue

            inserted = load_one_file(
                connection,
                file_path,
            )

            total_inserted += inserted

            file_row_count = len(pd.read_csv(file_path))
            skipped = file_row_count - inserted
            total_skipped += skipped

            # Update state only after successful load
            connection.execute(
                text(
                    """
                    UPDATE pipeline_state
                    SET last_processed_date = :last_processed_date,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE pipeline_name = :pipeline_name
                    """
                ),
                {
                    "last_processed_date": file_date,
                    "pipeline_name": PIPELINE_NAME,
                },
            )

            last_processed_date = file_date

            print(
                f"LOADED {file_path.name} | "
                f"Inserted: {inserted} | "
                f"Skipped duplicates: {skipped}"
            )

    print("\nIncremental loading completed.")
    print(f"Total inserted: {total_inserted}")
    print(f"Total skipped: {total_skipped}")


if __name__ == "__main__":
    load_incrementally()