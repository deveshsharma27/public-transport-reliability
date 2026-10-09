from typing import Any

import pandas as pd
from sqlalchemy import text

from src.db import get_engine


def get_route_metrics() -> pd.DataFrame:
    """
    Fetch route-level reliability metrics calculated by PostgreSQL.
    """
    engine = get_engine()

    query = text(
        """
        SELECT
            route_id,
            route_name,
            origin,
            destination,
            total_trips,
            completed_trips,
            cancelled_trips,
            on_time_trips,
            delayed_trips,
            avg_delay_minutes,
            max_delay_minutes,
            on_time_rate,
            cancellation_rate,
            reliability_score
        FROM route_reliability
        ORDER BY reliability_score DESC;
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(query, connection)

    return df


def get_worst_route() -> dict[str, Any]:
    """
    Return the lowest-scoring route and its supporting evidence.
    """
    engine = get_engine()

    query = text(
        """
        SELECT
            route_id,
            route_name,
            origin,
            destination,
            total_trips,
            completed_trips,
            cancelled_trips,
            on_time_trips,
            delayed_trips,
            avg_delay_minutes,
            max_delay_minutes,
            on_time_rate,
            cancellation_rate,
            reliability_score
        FROM route_reliability
        ORDER BY reliability_score ASC
        LIMIT 1;
        """
    )

    with engine.connect() as connection:
        row = connection.execute(query).mappings().first()

    if row is None:
        raise ValueError("No route reliability data found.")

    return dict(row)


def print_route_metrics(df: pd.DataFrame) -> None:
    """Display route-level reliability metrics."""
    if df.empty:
        print("No route metrics found.")
        return

    display_columns = [
        "route_id",
        "route_name",
        "total_trips",
        "completed_trips",
        "cancelled_trips",
        "avg_delay_minutes",
        "on_time_rate",
        "cancellation_rate",
        "reliability_score",
    ]

    print("\nRoute Reliability Metrics")
    print("=" * 100)

    print(
        df[display_columns].to_string(
            index=False
        )
    )


def main() -> None:
    metrics_df = get_route_metrics()

    print_route_metrics(metrics_df)

    worst_route = get_worst_route()

    print("\nWorst-performing Route")
    print("=" * 100)

    for key, value in worst_route.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()