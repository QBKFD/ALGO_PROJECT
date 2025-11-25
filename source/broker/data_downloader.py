# data_downloader.py
from source.broker.trading_client import create_ibkr_client
from datetime import datetime, timedelta
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def download_gc_data(days=700, bar_size="1 min"):
    """Download Gold futures data - max ~700 days per contract"""
    
    client = create_ibkr_client()
    if not client.connect_to_ibkr(client_id=5):
        return
    
    time.sleep(1)
    all_data = []
    
    logger.info(f"Downloading {days} days of {bar_size} GC data")
    logger.info(f"Estimated time: {(days * 11) / 3600:.1f} hours")
    
    for i in range(days):
        end_date = datetime.now() - timedelta(days=i)
        end_str = end_date.strftime("%Y%m%d 23:59:59")
        
        data = client.get_historical_data(
            symbol="GC",
            exchange="COMEX",
            expiry="20251229",  # December 2025 contract
            duration="1 D",
            bar_size=bar_size,
            end_date_time=end_str
        )
        
        if data:
            all_data.extend(data)
            if (i + 1) % 10 == 0:
                logger.info(f"{i+1}/{days} | {len(all_data):,} bars")
        
        if (i + 1) % 100 == 0:
            df = pd.DataFrame(all_data)
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H:%M:%S US/Eastern')
            df = df.drop_duplicates(subset=['date']).sort_values('date')
            df.to_csv(f"GC_checkpoint_{i+1}.csv", index=False)
            logger.info(f"Saved checkpoint: {len(df):,} unique bars")
        
        time.sleep(11)
    
    # Final save
    df = pd.DataFrame(all_data)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H:%M:%S US/Eastern')
    df = df.drop_duplicates(subset=['date']).sort_values('date')
    df.to_csv("GC_2years_complete.csv", index=False)
    logger.info(f"✅ Done! {len(df):,} unique bars saved")
    
    client.disconnect_from_ibkr()

if __name__ == "__main__":
    download_gc_data(days=700, bar_size="1 min")  # ~2 years