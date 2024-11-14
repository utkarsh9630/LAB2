SELECT
    DATE,
	close, 
	symbol
    
FROM {{ source('raw_data', 'STOCK_PRICES_SYMBOLS') }}
