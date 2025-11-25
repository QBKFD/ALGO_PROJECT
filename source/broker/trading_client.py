# trading_client.py
"""
IBKR client for connection and historical data retrieval
"""
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import logging

logger = logging.getLogger(__name__)

class IBKRClient(EWrapper, EClient):
    """Simple IBKR client for data retrieval"""
    
    def __init__(self):
        EClient.__init__(self, self)
        self.connected = False
        self.orderId = None
        self.historical_data = {}
        self.data_end = {}
        
    def connect_to_ibkr(self, host="127.0.0.1", port=7497, client_id=1):
        """Connect to IBKR TWS/Gateway"""
        logger.info(f"Connecting to IBKR at {host}:{port} with client_id={client_id}")
        
        try:
            self.connect(host, port, client_id)
            
            api_thread = threading.Thread(target=self.run, daemon=True)
            api_thread.start()
            
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("Successfully connected to IBKR")
            else:
                logger.error("Connection timeout")
                
            return self.connected
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def nextValidId(self, orderId):
        """Handle next valid order ID - signals successful connection"""
        self.orderId = orderId
        self.connected = True
        logger.info(f"Connected! Next valid order ID: {orderId}")
    
    def error(self, reqId, errorCode, errorString, advancedOrderReject="", errorTime=""):
        """Handle IBKR errors and messages"""
        if errorCode in [2104, 2106, 2158]:
            logger.info(f"Info {errorCode}: {errorString}")
        elif errorCode == 162:
            logger.warning(f"No market data subscription: {errorString}")
        elif errorCode == 200:
            logger.warning(f"No security definition: {errorString}")
        elif errorCode == 354:
            logger.warning(f"Request limit reached: {errorString}")
        elif errorCode < 1000:
            logger.error(f"Error {errorCode} (reqId {reqId}): {errorString}")
        else:
            logger.debug(f"Message {errorCode}: {errorString}")
    
    def historicalData(self, reqId, bar):
        """Receive historical data bars"""
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        
        self.historical_data[reqId].append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume,
            'barCount': bar.barCount,
            'average': bar.wap
        })
    
    def historicalDataEnd(self, reqId, start, end):
        """Signal end of historical data transmission"""
        self.data_end[reqId] = True
        num_bars = len(self.historical_data.get(reqId, []))
        logger.info(f"Historical data complete for reqId {reqId}: {num_bars} bars")
    
    def create_futures_contract(self, symbol, exchange, expiry, currency="USD"):
        """Create a futures contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.exchange = exchange
        contract.currency = currency
        
        if expiry:
            contract.secType = "FUT"
            contract.lastTradeDateOrContractMonth = expiry
        else:
            contract.secType = "CONTFUT"
        
        return contract
    
    def get_historical_data(self, symbol, exchange, expiry, duration="1 D", 
                           bar_size="1 min", end_date_time=""):
        """Request historical futures data"""
        if not self.connected or self.orderId is None:
            logger.error("Not connected to IBKR")
            return None
        
        req_id = self.orderId
        self.orderId += 1
        
        self.historical_data[req_id] = []
        self.data_end[req_id] = False
        
        contract = self.create_futures_contract(symbol, exchange, expiry)
        
        try:
            logger.info(f"Requesting historical data for {symbol} (reqId: {req_id})")
            
            self.reqHistoricalData(
                reqId=req_id,
                contract=contract,
                endDateTime=end_date_time,
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=0,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
            
            timeout = 30
            start_time = time.time()
            while not self.data_end.get(req_id, False) and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.data_end.get(req_id, False):
                data = self.historical_data.get(req_id, [])
                logger.info(f"Retrieved {len(data)} bars for {symbol}")
                return data
            else:
                logger.error(f"Timeout waiting for historical data for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Historical data request failed: {e}")
            return None

    def disconnect_from_ibkr(self):
        """Disconnect from IBKR"""
        if self.isConnected():
            self.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")

def create_ibkr_client():
    """Create and return an IBKR client instance"""
    return IBKRClient()