WITH moving_averages AS (
    SELECT 
        DATE,
        close, 
        symbol,
        -- Calculate 7-day moving average
        AVG(close) OVER (PARTITION BY symbol ORDER BY DATE ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7,
        -- Calculate 30-day moving average
        AVG(close) OVER (PARTITION BY symbol ORDER BY DATE ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS ma_30,
		CONCAT(date, '_', symbol) AS date_symbol,
    current_timestamp() as last_updated_timestamp
    FROM {{ source('raw_data', 'STOCK_PRICES_SYMBOLS') }}
)
-- Output the final table with the calculated moving averages
SELECT 
    DATE,
    close, 
    symbol,
    ma_7,
    ma_30,
	date_symbol,
	last_updated_timestamp
FROM moving_averages