from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

SOURCE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "clean_trips_2026_09_30.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "clean_trips_2026_10_01.csv"
)


def main():
    df = pd.read_csv(SOURCE_FILE)

    df["service_date"] = "2026-10-01"

    df["trip_id"] = [
        f"T31{i + 1:04d}"
        for i in range(len(df))
    ]

    df["source_file"] = "trips_2026_10_01.csv"

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"Created {OUTPUT_FILE.name} "
        f"with {len(df)} trips."
    )


if __name__ == "__main__":
    main()