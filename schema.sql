-- Car Safety Device Database Schema
-- PostgreSQL

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────────
-- Devices (one row per physical ESP32 unit)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS devices (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id   VARCHAR(64) UNIQUE NOT NULL,   -- MAC address or hardcoded ID from the ESP32
    name        VARCHAR(128),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen   TIMESTAMPTZ
);

-- ─────────────────────────────────────────────
-- Sensor readings  (periodic push from ESP32)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sensor_readings (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id    UUID         NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    temperature  NUMERIC(5,2),
    humidity     NUMERIC(5,2),
    smoke_level  VARCHAR(16)  CHECK (smoke_level  IN ('LOW','MEDIUM','HIGH')),
    air_quality  VARCHAR(16)  CHECK (air_quality  IN ('GOOD','MODERATE','POOR','HAZARDOUS')),
    co_level     VARCHAR(16)  CHECK (co_level     IN ('LOW','MEDIUM','HIGH')),
    latitude     DOUBLE PRECISION,
    longitude    DOUBLE PRECISION,
    recorded_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sensor_device_time
    ON sensor_readings(device_id, recorded_at DESC);

-- ─────────────────────────────────────────────
-- Sound events  (one row per uploaded WAV fragment)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sound_events (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id        UUID         NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    -- per-subject detection results
    is_baby_crying   BOOLEAN      NOT NULL DEFAULT FALSE,
    baby_confidence  NUMERIC(6,4),
    is_dog_detected  BOOLEAN      NOT NULL DEFAULT FALSE,
    dog_confidence   NUMERIC(6,4),
    is_cat_detected  BOOLEAN      NOT NULL DEFAULT FALSE,
    cat_confidence   NUMERIC(6,4),
    top_labels       JSONB,                          -- [{"label": "...", "score": 0.xx}, ...]
    audio_duration_s NUMERIC(7,2),
    recorded_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sound_device_time
    ON sound_events(device_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_sound_crying
    ON sound_events(device_id, is_baby_crying, recorded_at DESC)
    WHERE is_baby_crying = TRUE;

-- ─────────────────────────────────────────────
-- Alerts  (server-generated, never written by ESP32)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id         UUID         NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    sensor_reading_id UUID         REFERENCES sensor_readings(id) ON DELETE SET NULL,
    sound_event_id    UUID         REFERENCES sound_events(id)    ON DELETE SET NULL,
    alert_type        VARCHAR(32)  NOT NULL CHECK (alert_type IN (
                          'BABY_CRYING',
                          'DOG_IN_CAR',
                          'CAT_IN_CAR',
                          'HIGH_CO',
                          'HIGH_SMOKE',
                          'POOR_AIR_QUALITY',
                          'HIGH_TEMP',
                          'COMBINED_DANGER'
                      )),
    severity          VARCHAR(8)   NOT NULL CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    message           TEXT,
    acknowledged      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_unacked
    ON alerts(device_id, acknowledged, created_at DESC)
    WHERE acknowledged = FALSE;
