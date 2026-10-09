from src.ai.summarizer import generate_summary
from src.analytics.metrics import get_route_metrics, get_worst_route
from src.db import get_engine
from src.ingestion.load_dimensions import load_routes, load_vehicles
from src.ingestion.load_trips import load_incrementally
from src.validation.validator import process_all_files


def run_pipeline() -> None:
    """Run the complete public transport reliability pipeline."""

    print("=" * 70)
    print("PUBLIC TRANSPORT RELIABILITY PIPELINE")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Database connection
    # ---------------------------------------------------------
    engine = get_engine()
    print("\n[1/6] PostgreSQL connection ready.")

    # ---------------------------------------------------------
    # 2. Synchronize dimension data
    # ---------------------------------------------------------
    print("\n[2/6] Synchronizing dimensions...")
    load_routes(engine)
    load_vehicles(engine)

    # ---------------------------------------------------------
    # 3. Validate and clean daily source files
    # ---------------------------------------------------------
    print("\n[3/6] Validating daily trip data...")
    process_all_files()

    # ---------------------------------------------------------
    # 4. Incremental trip loading
    # ---------------------------------------------------------
    print("\n[4/6] Loading validated trips incrementally...")
    load_incrementally()

    # ---------------------------------------------------------
    # 5. SQL analytics
    # ---------------------------------------------------------
    print("\n[5/6] Calculating route reliability metrics...")

    metrics_df = get_route_metrics()

    if metrics_df.empty:
        raise RuntimeError(
            "No route reliability metrics were produced."
        )

    worst_route = get_worst_route()

    print(
        f"Worst route: "
        f"{worst_route['route_id']} - "
        f"{worst_route['route_name']}"
    )

    print(
        f"Reliability score: "
        f"{worst_route['reliability_score']}"
    )

    # ---------------------------------------------------------
    # 6. AI summary
    # ---------------------------------------------------------
    print("\n[6/6] Generating AI summary...")

    summary = generate_summary(worst_route)

    print("\nAI SUMMARY")
    print("-" * 70)
    print(summary)

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()