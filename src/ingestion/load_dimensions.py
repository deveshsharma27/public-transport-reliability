from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.db import get_engine


BASE_DIR = Path(__file__).resolve().parents[2]

ROUTES_FILE = BASE_DIR / "data" / "dimensions" / "routes.csv"
VEHICLES_FILE = BASE_DIR / "data" / "dimensions" / "vehicles.csv"


def load_routes(engine) -> None:
    """Insert or update route dimension records."""
    df = pd.read_csv(ROUTES_FILE)

    expected_columns = [
        "route_id",
        "route_name",
        "origin",
        "destination",
        "distance_km",
        "base_travel_minutes",
    ]

    missing = set(expected_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"routes.csv is missing columns: {sorted(missing)}"
        )

    query = text(
        """
        INSERT INTO routes (
            route_id,
            route_name,
            origin,
            destination,
            distance_km,
            base_travel_minutes
        )
        VALUES (
            :route_id,
            :route_name,
            :origin,
            :destination,
            :distance_km,
            :base_travel_minutes
        )
        ON CONFLICT (route_id)
        DO UPDATE SET
            route_name = EXCLUDED.route_name,
            origin = EXCLUDED.origin,
            destination = EXCLUDED.destination,
            distance_km = EXCLUDED.distance_km,
            base_travel_minutes = EXCLUDED.base_travel_minutes
        """
    )

    records = df[expected_columns].to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(query, records)

    print(f"Routes synchronized: {len(records)}")


def load_vehicles(engine) -> None:
    """Insert or update vehicle dimension records."""
    df = pd.read_csv(VEHICLES_FILE)

    expected_columns = [
        "vehicle_id",
        "vehicle_type",
        "capacity",
    ]

    missing = set(expected_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"vehicles.csv is missing columns: {sorted(missing)}"
        )

    query = text(
        """
        INSERT INTO vehicles (
            vehicle_id,
            vehicle_type,
            capacity
        )
        VALUES (
            :vehicle_id,
            :vehicle_type,
            :capacity
        )
        ON CONFLICT (vehicle_id)
        DO UPDATE SET
            vehicle_type = EXCLUDED.vehicle_type,
            capacity = EXCLUDED.capacity
        """
    )

    records = df[expected_columns].to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(query, records)

    print(f"Vehicles synchronized: {len(records)}")


def main() -> None:
    engine = get_engine()

    load_routes(engine)
    load_vehicles(engine)

    print("Dimension ingestion completed successfully.")


if __name__ == "__main__":
    main()