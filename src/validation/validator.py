from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


REQUIRED_COLUMNS = [
    "trip_id",
    "service_date",
    "route_id",
    "route_name",
    "origin",
    "destination",
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
]


def load_reference_data():
    """Load valid route and vehicle IDs."""
    routes_file = BASE_DIR / "data" / "dimensions" / "routes.csv"
    vehicles_file = BASE_DIR / "data" / "dimensions" / "vehicles.csv"

    routes = pd.read_csv(routes_file)
    vehicles = pd.read_csv(vehicles_file)

    valid_routes = set(routes["route_id"].astype(str))
    vehicle_capacity = dict(
        zip(
            vehicles["vehicle_id"].astype(str),
            vehicles["capacity"],
        )
    )

    return valid_routes, vehicle_capacity


def validate_file(file_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate one daily trip file."""
    df = pd.read_csv(file_path)

    # Check columns
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{file_path.name} is missing columns: "
            f"{sorted(missing_columns)}"
        )

    # Normalize string fields
    string_columns = [
        "trip_id",
        "route_id",
        "status",
        "vehicle_id",
    ]

    for column in string_columns:
        df[column] = df[column].astype("string").str.strip()

    # Parse dates/timestamps
    df["service_date"] = pd.to_datetime(
        df["service_date"],
        errors="coerce",
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

    # Numeric conversion
    df["delay_minutes"] = pd.to_numeric(
        df["delay_minutes"],
        errors="coerce",
    )

    df["passenger_count"] = pd.to_numeric(
        df["passenger_count"],
        errors="coerce",
    )

    valid_routes, vehicle_capacity = load_reference_data()

    errors = pd.Series("", index=df.index, dtype="string")

    def add_error(mask, message):
        nonlocal errors
        errors.loc[mask & errors.eq("")] = message

    # Required fields
    for column in [
        "trip_id",
        "service_date",
        "route_id",
        "scheduled_departure",
        "scheduled_arrival",
        "status",
        "vehicle_id",
        "passenger_count",
    ]:
        add_error(
            df[column].isna() | df[column].astype("string").eq(""),
            f"missing_{column}",
        )

    # Route validation
    add_error(
        ~df["route_id"].isin(valid_routes),
        "invalid_route_id",
    )

    # Vehicle validation
    add_error(
        ~df["vehicle_id"].isin(vehicle_capacity.keys()),
        "invalid_vehicle_id",
    )

    # Status validation
    add_error(
        ~df["status"].isin(["completed", "cancelled"]),
        "invalid_status",
    )

    # Passenger validation
    add_error(
        df["passenger_count"].notna()
        & (df["passenger_count"] < 0),
        "negative_passenger_count",
    )

    # Passenger capacity validation
    known_vehicle = df["vehicle_id"].isin(vehicle_capacity.keys())

    capacity_exceeded = (
        known_vehicle
        & df["passenger_count"].notna()
        & df["passenger_count"]
        .map(vehicle_capacity)
        .notna()
        & (
            df["passenger_count"]
            > df["vehicle_id"].map(vehicle_capacity)
        )
    )

    add_error(
        capacity_exceeded,
        "passenger_count_exceeds_capacity",
    )

    # Delay validation
    add_error(
        df["delay_minutes"].notna()
        & (df["delay_minutes"] < 0),
        "negative_delay",
    )

    # Scheduled time validation
    scheduled_time_error = (
        df["scheduled_departure"].notna()
        & df["scheduled_arrival"].notna()
        & (
            df["scheduled_arrival"]
            < df["scheduled_departure"]
        )
    )

    add_error(
        scheduled_time_error,
        "scheduled_arrival_before_departure",
    )

    # Completed trip validation
    completed = df["status"].eq("completed")

    add_error(
        completed & df["actual_departure"].isna(),
        "completed_trip_missing_actual_departure",
    )

    add_error(
        completed & df["actual_arrival"].isna(),
        "completed_trip_missing_actual_arrival",
    )

    actual_time_error = (
        completed
        & df["actual_departure"].notna()
        & df["actual_arrival"].notna()
        & (
            df["actual_arrival"]
            < df["actual_departure"]
        )
    )

    add_error(
        actual_time_error,
        "actual_arrival_before_departure",
    )

    # Cancelled trip consistency
    cancelled = df["status"].eq("cancelled")

    add_error(
        cancelled & df["actual_departure"].notna(),
        "cancelled_trip_has_actual_departure",
    )

    add_error(
        cancelled & df["actual_arrival"].notna(),
        "cancelled_trip_has_actual_arrival",
    )

    # Duplicate IDs within the same file
    duplicate_ids = df["trip_id"].duplicated(keep="first")

    add_error(
    duplicate_ids,
    "duplicate_trip_id_in_file",
    )

    df["validation_error"] = errors

    invalid_df = df[df["validation_error"].ne("")].copy()
    valid_df = df[df["validation_error"].eq("")].copy()

    # Add source file to both outputs
    valid_df["source_file"] = file_path.name
    invalid_df["source_file"] = file_path.name

    return valid_df, invalid_df


def process_all_files():
    """Validate every daily raw CSV file."""
    total_valid = 0
    total_invalid = 0

    files = sorted(RAW_DIR.glob("trips_*.csv"))

    if not files:
        raise FileNotFoundError(
            f"No daily trip files found in {RAW_DIR}"
        )

    for file_path in files:
        valid_df, invalid_df = validate_file(file_path)

        processed_file = (
            PROCESSED_DIR
            / f"clean_{file_path.name}"
        )

        quarantine_file = (
            QUARANTINE_DIR
            / f"invalid_{file_path.name}"
        )

        valid_df.to_csv(
            processed_file,
            index=False,
        )

        invalid_df.to_csv(
            quarantine_file,
            index=False,
        )

        total_valid += len(valid_df)
        total_invalid += len(invalid_df)

        print(
            f"{file_path.name}: "
            f"{len(valid_df)} valid, "
            f"{len(invalid_df)} invalid"
        )

    print("\nValidation completed.")
    print(f"Total valid records: {total_valid}")
    print(f"Total invalid records: {total_invalid}")


if __name__ == "__main__":
    process_all_files()