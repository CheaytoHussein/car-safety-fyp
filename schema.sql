-- Car Safety Device — PostgreSQL Schema
-- Run once against the Render PostgreSQL instance.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────────
-- Users
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- Devices  (pre-registered at manufacturing time)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS devices (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id   VARCHAR(64)  UNIQUE NOT NULL,   -- serial number hardcoded in firmware
    name        VARCHAR(128),                    -- user-assigned name e.g. "My Tesla"
    owner_id    UUID         REFERENCES users(id) ON DELETE SET NULL,  -- NULL until activated
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_seen   TIMESTAMPTZ
);

-- ─────────────────────────────────────────────
-- Sensor readings  (periodic push from ESP32)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sensor_readings (
    id             UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id      UUID             NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    temperature    NUMERIC(5,2),
    humidity       NUMERIC(5,2),
    smoke_level    VARCHAR(16)      CHECK (smoke_level IN ('LOW','MEDIUM','HIGH')),
    air_quality    VARCHAR(16)      CHECK (air_quality IN ('GOOD','MODERATE','POOR','HAZARDOUS')),
    co_level       VARCHAR(16)      CHECK (co_level    IN ('LOW','MEDIUM','HIGH')),
    noise_detected BOOLEAN          NOT NULL DEFAULT FALSE,
    latitude       DOUBLE PRECISION,
    longitude      DOUBLE PRECISION,
    recorded_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sensor_device_time
    ON sensor_readings(device_id, recorded_at DESC);

-- ─────────────────────────────────────────────
-- Sound events  (INMP441 + Edge Impulse — populated once audio is wired)
-- Only non-background detections are stored.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sound_events (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id    UUID        NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    sound_class  VARCHAR(16) NOT NULL CHECK (sound_class IN ('BABY_CRY','CAT_MEOW','DOG_BARK')),
    confidence   NUMERIC(6,4),
    recorded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sound_device_time
    ON sound_events(device_id, recorded_at DESC);
