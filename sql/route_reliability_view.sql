CREATE VIEW route_reliability AS

WITH route_metrics AS (
    SELECT
        r.route_id,
        r.route_name,
        r.origin,
        r.destination,

        COUNT(t.trip_id) AS total_trips,

        COUNT(*) FILTER (
            WHERE t.status = 'completed'
        ) AS completed_trips,

        COUNT(*) FILTER (
            WHERE t.status = 'cancelled'
        ) AS cancelled_trips,

        COUNT(*) FILTER (
            WHERE t.status = 'completed'
              AND t.delay_minutes <= 5
        ) AS on_time_trips,

        COUNT(*) FILTER (
            WHERE t.status = 'completed'
              AND t.delay_minutes > 5
        ) AS delayed_trips,

        ROUND(
            AVG(t.delay_minutes)
            FILTER (WHERE t.status = 'completed'),
            2
        ) AS avg_delay_minutes,

        MAX(t.delay_minutes)
            FILTER (WHERE t.status = 'completed')
            AS max_delay_minutes

    FROM routes r
    LEFT JOIN trips t
        ON r.route_id = t.route_id

    GROUP BY
        r.route_id,
        r.route_name,
        r.origin,
        r.destination
)

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

    ROUND(
        (
            0.60 * (
                100.0 * on_time_trips
                / NULLIF(completed_trips, 0)
            )
        )
        +
        (
            0.40 * (
                100.0 -
                (
                    100.0 * cancelled_trips
                    / NULLIF(total_trips, 0)
                )
            )
        ),
        2
    ) AS reliability_score,

    ROUND(
        100.0 * on_time_trips
        / NULLIF(completed_trips, 0),
        2
    ) AS on_time_rate,

    ROUND(
        100.0 * cancelled_trips
        / NULLIF(total_trips, 0),
        2
    ) AS cancellation_rate

FROM route_metrics;