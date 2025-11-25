# test_ibkr_data.py
"""
Test IBKR historical data capabilities
"""

from ibapi.contract import Contract
from source.broker.trading_client import create_ibkr_client
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ibkr_historical_data():
    """Test getting historical data from IBKR"""
    
    client = create_ibkr_client()
    
    # Add historical data handling to the client
    client.historical_data = []
    
    def historicalData(self, reqId, bar):
        """Handle historical data bars"""
        self.historical_data.append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })
    
    def historicalDataEnd(self, reqId, start, end):
        """Signal end of historical data"""
        logger.info(f"Historical data complete: {len(self.historical_data)} bars")
    
    # Add methods to client
    client.historicalData = historicalData.__get__(client)
    client.historicalDataEnd = historicalDataEnd.__get__(client)
    
    if client.connect_to_ibkr():
        logger.info("Testing historical data requests...")
        
        # Test 1: Get AAPL daily data
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        
        try:
            client.reqHistoricalData(
                reqId=1,
                contract=contract,
                endDateTime="",  # Most recent
                durationStr="30 D",  # 30 days
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=1,  # Regular trading hours
                formatDate=1
            )
            
            # Wait for data
            time.sleep(5)
            
            if client.historical_data:
                logger.info(f"SUCCESS: Got {len(client.historical_data)} AAPL bars")
                logger.info(f"Date range: {client.historical_data[0]['date']} to {client.historical_data[-1]['date']}")
                logger.info(f"Recent close: ${client.historical_data[-1]['close']:.2f}")
                return True
            else:
                logger.error("FAILED: No historical data received")
                return False
                
        except Exception as e:
            logger.error(f"Historical data request failed: {e}")
            return False
    
    else:
        logger.error("Failed to connect to IBKR")
        return False

if __name__ == "__main__":
    success = test_ibkr_historical_data()
    
    if success:
        print("\n✅ IBKR historical data works!")
        print("You can use IBKR for data collection")
    else:
        print("\n❌ IBKR historical data failed")
        print("Recommend using yfinance for data collection")