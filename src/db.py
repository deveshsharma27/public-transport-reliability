import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()


def get_engine() -> Engine:
    """Create and return the PostgreSQL SQLAlchemy engine."""
    required_vars = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing)}"
        )

    database_url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
        f"/{os.getenv('DB_NAME')}"
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


def test_connection() -> None:
    """Test PostgreSQL connectivity."""
    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("PostgreSQL connection successful:", result.scalar())


if __name__ == "__main__":
    test_connection()