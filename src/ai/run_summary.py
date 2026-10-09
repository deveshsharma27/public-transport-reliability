from src.analytics.metrics import get_worst_route
from src.ai.summarizer import generate_summary


def main():
    print("Fetching worst-performing route...")

    evidence = get_worst_route()

    print("\nStructured Evidence")
    print("=" * 60)

    for key, value in evidence.items():
        print(f"{key}: {value}")

    print("\nAI Summary")
    print("=" * 60)

    summary = generate_summary(evidence)

    print(summary)


if __name__ == "__main__":
    main()