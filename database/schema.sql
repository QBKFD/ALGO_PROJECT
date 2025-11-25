-- database/schema.sql (CLEAN VERSION)

-- ============================================================
-- HISTORICAL DATA - ONLY 1-MINUTE BARS
-- ============================================================
CREATE TABLE IF NOT EXISTS ohlcv_historical_1min (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(12, 4) NOT NULL,
    high DECIMAL(12, 4) NOT NULL,
    low DECIMAL(12, 4) NOT NULL,
    close DECIMAL(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    bar_count INTEGER,
    average DECIMAL(12, 4),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_hist_1min_symbol_time ON ohlcv_historical_1min(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_hist_1min_timestamp ON ohlcv_historical_1min(timestamp DESC);

-- ============================================================
-- REAL-TIME DATA - ONLY 1-MINUTE BARS (PARTITIONED)
-- ============================================================
CREATE TABLE IF NOT EXISTS ohlcv_realtime_1min (
    id SERIAL,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(12, 4) NOT NULL,
    high DECIMAL(12, 4) NOT NULL,
    low DECIMAL(12, 4) NOT NULL,
    close DECIMAL(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    bar_count INTEGER,
    average DECIMAL(12, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id, timestamp),
    UNIQUE(symbol, timestamp)
) PARTITION BY RANGE (timestamp);

CREATE INDEX IF NOT EXISTS idx_rt_1min_symbol_time ON ohlcv_realtime_1min(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_rt_1min_recent ON ohlcv_realtime_1min(timestamp DESC);

-- Create partitions
CREATE TABLE IF NOT EXISTS ohlcv_realtime_1min_default PARTITION OF ohlcv_realtime_1min DEFAULT;

CREATE TABLE IF NOT EXISTS ohlcv_realtime_1min_2025_11_21 PARTITION OF ohlcv_realtime_1min
    FOR VALUES FROM ('2025-11-21 00:00:00') TO ('2025-11-22 00:00:00');

CREATE TABLE IF NOT EXISTS ohlcv_realtime_1min_2025_11_22 PARTITION OF ohlcv_realtime_1min
    FOR VALUES FROM ('2025-11-22 00:00:00') TO ('2025-11-23 00:00:00');

CREATE TABLE IF NOT EXISTS ohlcv_realtime_1min_2025_11_23 PARTITION OF ohlcv_realtime_1min
    FOR VALUES FROM ('2025-11-23 00:00:00') TO ('2025-11-24 00:00:00');

CREATE TABLE IF NOT EXISTS ohlcv_realtime_1min_2025_11_24 PARTITION OF ohlcv_realtime_1min
    FOR VALUES FROM ('2025-11-24 00:00:00') TO ('2025-11-25 00:00:00');

-- ============================================================
-- COMBINED 1-MINUTE VIEW
-- ============================================================
CREATE OR REPLACE VIEW ohlcv_1min AS
    SELECT 
        id, symbol, timestamp, open, high, low, close, volume,
        bar_count, average, 'historical' AS source
    FROM ohlcv_historical_1min
    
    UNION ALL
    
    SELECT 
        id, symbol, timestamp, open, high, low, close, volume,
        bar_count, average, 'realtime' AS source
    FROM ohlcv_realtime_1min
    
    ORDER BY timestamp DESC;

-- ============================================================
-- AGGREGATION FUNCTION
-- ============================================================
CREATE OR REPLACE FUNCTION aggregate_bars(
    p_symbol VARCHAR,
    p_start_time TIMESTAMP,
    p_end_time TIMESTAMP,
    p_interval_minutes INTEGER
) RETURNS TABLE (
    bar_timestamp TIMESTAMP,
    open DECIMAL,
    high DECIMAL,
    low DECIMAL,
    close DECIMAL,
    volume BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE_TRUNC('hour', bars.timestamp) + 
            (EXTRACT(MINUTE FROM bars.timestamp)::INTEGER / p_interval_minutes) * 
            (p_interval_minutes || ' minutes')::INTERVAL AS bar_timestamp,
        (ARRAY_AGG(bars.open ORDER BY bars.timestamp))[1] AS agg_open,
        MAX(bars.high) AS agg_high,
        MIN(bars.low) AS agg_low,
        (ARRAY_AGG(bars.close ORDER BY bars.timestamp DESC))[1] AS agg_close,
        SUM(bars.volume) AS agg_volume
    FROM ohlcv_1min bars
    WHERE bars.symbol = p_symbol
      AND bars.timestamp >= p_start_time
      AND bars.timestamp < p_end_time
    GROUP BY bar_timestamp
    ORDER BY bar_timestamp;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- MATERIALIZED VIEWS
-- ============================================================

DROP MATERIALIZED VIEW IF EXISTS ohlcv_5min CASCADE;
CREATE MATERIALIZED VIEW ohlcv_5min AS
SELECT 
    symbol,
    DATE_TRUNC('hour', timestamp) + 
        (EXTRACT(MINUTE FROM timestamp)::INTEGER / 5) * INTERVAL '5 minutes' AS timestamp,
    (ARRAY_AGG(open ORDER BY timestamp))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (ARRAY_AGG(close ORDER BY timestamp DESC))[1] AS close,
    SUM(volume) AS volume,
    SUM(bar_count) AS bar_count,
    AVG(average) AS average,
    MAX(source) AS source
FROM ohlcv_1min
GROUP BY symbol, DATE_TRUNC('hour', timestamp) + 
         (EXTRACT(MINUTE FROM timestamp)::INTEGER / 5) * INTERVAL '5 minutes';

CREATE UNIQUE INDEX idx_mv_5min ON ohlcv_5min(symbol, timestamp DESC);

DROP MATERIALIZED VIEW IF EXISTS ohlcv_15min CASCADE;
CREATE MATERIALIZED VIEW ohlcv_15min AS
SELECT 
    symbol,
    DATE_TRUNC('hour', timestamp) + 
        (EXTRACT(MINUTE FROM timestamp)::INTEGER / 15) * INTERVAL '15 minutes' AS timestamp,
    (ARRAY_AGG(open ORDER BY timestamp))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (ARRAY_AGG(close ORDER BY timestamp DESC))[1] AS close,
    SUM(volume) AS volume,
    SUM(bar_count) AS bar_count,
    AVG(average) AS average,
    MAX(source) AS source
FROM ohlcv_1min
GROUP BY symbol, DATE_TRUNC('hour', timestamp) + 
         (EXTRACT(MINUTE FROM timestamp)::INTEGER / 15) * INTERVAL '15 minutes';

CREATE UNIQUE INDEX idx_mv_15min ON ohlcv_15min(symbol, timestamp DESC);

DROP MATERIALIZED VIEW IF EXISTS ohlcv_30min CASCADE;
CREATE MATERIALIZED VIEW ohlcv_30min AS
SELECT 
    symbol,
    DATE_TRUNC('hour', timestamp) + 
        (EXTRACT(MINUTE FROM timestamp)::INTEGER / 30) * INTERVAL '30 minutes' AS timestamp,
    (ARRAY_AGG(open ORDER BY timestamp))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (ARRAY_AGG(close ORDER BY timestamp DESC))[1] AS close,
    SUM(volume) AS volume,
    SUM(bar_count) AS bar_count,
    AVG(average) AS average,
    MAX(source) AS source
FROM ohlcv_1min
GROUP BY symbol, DATE_TRUNC('hour', timestamp) + 
         (EXTRACT(MINUTE FROM timestamp)::INTEGER / 30) * INTERVAL '30 minutes';

CREATE UNIQUE INDEX idx_mv_30min ON ohlcv_30min(symbol, timestamp DESC);

DROP MATERIALIZED VIEW IF EXISTS ohlcv_1h CASCADE;
CREATE MATERIALIZED VIEW ohlcv_1h AS
SELECT 
    symbol,
    DATE_TRUNC('hour', timestamp) AS timestamp,
    (ARRAY_AGG(open ORDER BY timestamp))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (ARRAY_AGG(close ORDER BY timestamp DESC))[1] AS close,
    SUM(volume) AS volume,
    SUM(bar_count) AS bar_count,
    AVG(average) AS average,
    MAX(source) AS source
FROM ohlcv_1min
GROUP BY symbol, DATE_TRUNC('hour', timestamp);

CREATE UNIQUE INDEX idx_mv_1h ON ohlcv_1h(symbol, timestamp DESC);

DROP MATERIALIZED VIEW IF EXISTS ohlcv_4h CASCADE;
CREATE MATERIALIZED VIEW ohlcv_4h AS
SELECT 
    symbol,
    DATE_TRUNC('day', timestamp) + 
        (EXTRACT(HOUR FROM timestamp)::INTEGER / 4) * INTERVAL '4 hours' AS timestamp,
    (ARRAY_AGG(open ORDER BY timestamp))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (ARRAY_AGG(close ORDER BY timestamp DESC))[1] AS close,
    SUM(volume) AS volume,
    SUM(bar_count) AS bar_count,
    AVG(average) AS average,
    MAX(source) AS source
FROM ohlcv_1min
GROUP BY symbol, DATE_TRUNC('day', timestamp) + 
         (EXTRACT(HOUR FROM timestamp)::INTEGER / 4) * INTERVAL '4 hours';

CREATE UNIQUE INDEX idx_mv_4h ON ohlcv_4h(symbol, timestamp DESC);

DROP MATERIALIZED VIEW IF EXISTS ohlcv_1d CASCADE;
CREATE MATERIALIZED VIEW ohlcv_1d AS
SELECT 
    symbol,
    DATE_TRUNC('day', timestamp) AS timestamp,
    (ARRAY_AGG(open ORDER BY timestamp))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (ARRAY_AGG(close ORDER BY timestamp DESC))[1] AS close,
    SUM(volume) AS volume,
    SUM(bar_count) AS bar_count,
    AVG(average) AS average,
    MAX(source) AS source
FROM ohlcv_1min
GROUP BY symbol, DATE_TRUNC('day', timestamp);

CREATE UNIQUE INDEX idx_mv_1d ON ohlcv_1d(symbol, timestamp DESC);

-- ============================================================
-- REFRESH FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION refresh_all_timeframes() RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY ohlcv_5min;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ohlcv_15min;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ohlcv_30min;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ohlcv_1h;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ohlcv_4h;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ohlcv_1d;
    
    RAISE NOTICE 'Refreshed all materialized views';
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- HELPER VIEWS
-- ============================================================

CREATE OR REPLACE VIEW latest_bars_all_tf AS
SELECT '1min' as timeframe, symbol, MAX(timestamp) as last_bar FROM ohlcv_1min GROUP BY symbol
UNION ALL
SELECT '5min', symbol, MAX(timestamp) FROM ohlcv_5min GROUP BY symbol
UNION ALL
SELECT '15min', symbol, MAX(timestamp) FROM ohlcv_15min GROUP BY symbol
UNION ALL
SELECT '30min', symbol, MAX(timestamp) FROM ohlcv_30min GROUP BY symbol
UNION ALL
SELECT '1H', symbol, MAX(timestamp) FROM ohlcv_1h GROUP BY symbol
UNION ALL
SELECT '4H', symbol, MAX(timestamp) FROM ohlcv_4h GROUP BY symbol
UNION ALL
SELECT '1D', symbol, MAX(timestamp) FROM ohlcv_1d GROUP BY symbol
ORDER BY symbol, timeframe;