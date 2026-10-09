CREATE TABLE IF NOT EXISTS routes (
    route_id VARCHAR(20) PRIMARY KEY,
    route_name VARCHAR(150) NOT NULL,
    origin VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    distance_km NUMERIC(6,2) NOT NULL CHECK (distance_km > 0),
    base_travel_minutes INTEGER NOT NULL CHECK (base_travel_minutes > 0)
);


CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id VARCHAR(20) PRIMARY KEY,
    vehicle_type VARCHAR(50) NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0)
);


CREATE TABLE IF NOT EXISTS trips (
    trip_id VARCHAR(30) PRIMARY KEY,

    service_date DATE NOT NULL,

    route_id VARCHAR(20) NOT NULL,
    vehicle_id VARCHAR(20) NOT NULL,

    scheduled_departure TIMESTAMP NOT NULL,
    scheduled_arrival TIMESTAMP NOT NULL,

    actual_departure TIMESTAMP NULL,
    actual_arrival TIMESTAMP NULL,

    delay_minutes INTEGER NULL CHECK (delay_minutes >= 0),

    status VARCHAR(20) NOT NULL
        CHECK (status IN ('completed', 'cancelled')),

    passenger_count INTEGER NOT NULL
        CHECK (passenger_count >= 0),

    weather_condition VARCHAR(50),
    traffic_level VARCHAR(20),
    event_type VARCHAR(50),

    source_file VARCHAR(255) NOT NULL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_trip_route
        FOREIGN KEY (route_id)
        REFERENCES routes(route_id),

    CONSTRAINT fk_trip_vehicle
        FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id),

    CONSTRAINT chk_trip_times
        CHECK (scheduled_arrival >= scheduled_departure),

    CONSTRAINT chk_actual_times
        CHECK (
            actual_departure IS NULL
            OR actual_arrival IS NULL
            OR actual_arrival >= actual_departure
        )
);


CREATE TABLE IF NOT EXISTS pipeline_state (
    pipeline_name VARCHAR(100) PRIMARY KEY,
    last_processed_date DATE NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO pipeline_state (
    pipeline_name,
    last_processed_date
)
VALUES (
    'public_transport_reliability',
    NULL
)
ON CONFLICT (pipeline_name) DO NOTHING;