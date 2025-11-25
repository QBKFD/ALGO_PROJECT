# scripts/import_csv.py (UNIVERSAL VERSION)
import sys
sys.path.append('.')

import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

def import_csv(csv_file, symbol=None):
    """
    Universal CSV importer for ANY ticker
    
    Usage:
        python scripts/import_csv.py GC_data.csv XAUUSD
        python scripts/import_csv.py ES_data.csv ES
        python scripts/import_csv.py NQ_data.csv NQ
    """
    
    # Auto-detect symbol from filename if not provided
    if symbol is None:
        # Try to extract from filename
        filename = os.path.basename(csv_file)
        if 'GC' in filename.upper():
            symbol = 'XAUUSD'
        elif 'ES' in filename.upper():
            symbol = 'ES'
        elif 'NQ' in filename.upper():
            symbol = 'NQ'
        else:
            symbol = input("Enter symbol (e.g., XAUUSD, ES, NQ): ").upper()
    
    print(f"Importing {csv_file} as {symbol}...")
    
    # Connect
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    # Load CSV
    print(f"Loading CSV...")
    df = pd.read_csv(csv_file)
    print(f"Found {len(df):,} rows")
    print("\nColumns:", df.columns.tolist())
    print("\nFirst 3 rows:")
    print(df.head(3))
    
    # Add symbol
    df['symbol'] = symbol
    
    # Flexible column mapping (handles different CSV formats)
    column_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'date' in col_lower or 'time' in col_lower:
            column_map[col] = 'timestamp'
        elif 'open' in col_lower:
            column_map[col] = 'open'
        elif 'high' in col_lower:
            column_map[col] = 'high'
        elif 'low' in col_lower:
            column_map[col] = 'low'
        elif 'close' in col_lower:
            column_map[col] = 'close'
        elif 'volume' in col_lower or 'vol' in col_lower:
            column_map[col] = 'volume'
    
    df = df.rename(columns=column_map)
    
    # Verify required columns
    required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    missing = [col for col in required if col not in df.columns]
    if missing:
        print(f"\n Missing required columns: {missing}")
        print(f"Available columns: {df.columns.tolist()}")
        return
    
    # Select columns
    df_clean = df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
    
    # Convert timestamp
    df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
    
    # Handle duplicates (keep first)
    df_clean = df_clean.drop_duplicates(subset=['symbol', 'timestamp'], keep='first')
    
    # Insert to database
    print(f"\nInserting {len(df_clean):,} rows...")
    
    # Chunked insert for large datasets
    chunk_size = 5000
    for i in range(0, len(df_clean), chunk_size):
        chunk = df_clean[i:i+chunk_size]
        chunk.to_sql('ohlcv_historical_1min', engine, if_exists='append', index=False, method='multi')
        print(f"  Progress: {min(i+chunk_size, len(df_clean)):,} / {len(df_clean):,}")
    
    print("✓ Import complete!")
    
    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                symbol,
                COUNT(*) as total_bars,
                MIN(timestamp) as first_bar,
                MAX(timestamp) as last_bar
            FROM ohlcv_historical_1min
            WHERE symbol = :symbol
            GROUP BY symbol
        """), {'symbol': symbol})
        
        print("\n" + "="*60)
        for row in result:
            print(f"Symbol: {row.symbol}")
            print(f"Total bars: {row.total_bars:,}")
            print(f"Date range: {row.first_bar} to {row.last_bar}")
        print("="*60)

if __name__ == "__main__":
    # Get filename and optional symbol
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'data.csv'
    symbol = sys.argv[2].upper() if len(sys.argv) > 2 else None
    
    import_csv(csv_file, symbol)