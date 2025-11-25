# find_gold_contract.py
"""
Script to find the correct Gold futures contract details from IBKR
"""
from source.broker.trading_client import create_ibkr_client
from ibapi.contract import Contract
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContractFinder(create_ibkr_client().__class__):
    """Extended client to find contract details"""
    
    def __init__(self):
        super().__init__()
        self.contract_details = []
    
    def contractDetails(self, reqId, contractDetails):
        """Receive contract details"""
        self.contract_details.append(contractDetails)
        logger.info(f"Found contract: {contractDetails.contract.symbol} "
                   f"{contractDetails.contract.lastTradeDateOrContractMonth} "
                   f"({contractDetails.contract.localSymbol})")
    
    def contractDetailsEnd(self, reqId):
        """Signal end of contract details"""
        logger.info(f"Finished receiving contract details (found {len(self.contract_details)})")

def find_gold_contracts():
    """Find available Gold futures contracts"""
    logger.info("=" * 70)
    logger.info("SEARCHING FOR GOLD FUTURES CONTRACTS")
    logger.info("=" * 70)
    
    client = ContractFinder()
    
    if not client.connect_to_ibkr(host="127.0.0.1", port=7497, client_id=1):
        logger.error("❌ Connection failed")
        return None
    
    time.sleep(1)  # Wait for connection to stabilize
    
    try:
        # Search for Gold contracts
        contract = Contract()
        contract.symbol = "GC"
        contract.secType = "FUT"
        contract.exchange = "COMEX"
        contract.currency = "USD"
        # Don't specify expiry - let IBKR tell us what's available
        
        logger.info("\nSearching for available GC contracts on COMEX...")
        
        req_id = 1
        client.reqContractDetails(req_id, contract)
        
        # Wait for results
        time.sleep(5)
        
        if client.contract_details:
            logger.info(f"\n✅ Found {len(client.contract_details)} Gold contracts")
            logger.info("\n📋 Available Contracts:")
            logger.info("-" * 70)
            
            for i, details in enumerate(client.contract_details[:10], 1):  # Show first 10
                c = details.contract
                logger.info(f"{i}. Symbol: {c.localSymbol}")
                logger.info(f"   Trading Class: {c.tradingClass}")
                logger.info(f"   Expiry: {c.lastTradeDateOrContractMonth}")
                logger.info(f"   Contract ID: {c.conId}")
                logger.info("")
            
            # Get the nearest contract
            if len(client.contract_details) > 0:
                nearest = client.contract_details[0].contract
                logger.info("=" * 70)
                logger.info("🎯 NEAREST CONTRACT TO USE:")
                logger.info("=" * 70)
                logger.info(f"Symbol: {nearest.symbol}")
                logger.info(f"Local Symbol: {nearest.localSymbol}")
                logger.info(f"Expiry: {nearest.lastTradeDateOrContractMonth}")
                logger.info(f"Exchange: {nearest.exchange}")
                logger.info(f"Trading Class: {nearest.tradingClass}")
                logger.info(f"Contract ID: {nearest.conId}")
                
                return nearest
        else:
            logger.error("❌ No contracts found")
            logger.error("\nPossible issues:")
            logger.error("1. COMEX market data subscription not active")
            logger.error("2. Try searching with just symbol (no exchange)")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        client.disconnect_from_ibkr()

def test_contract_variations():
    """Try different contract specifications to find what works"""
    logger.info("\n" + "=" * 70)
    logger.info("TESTING DIFFERENT CONTRACT VARIATIONS")
    logger.info("=" * 70)
    
    variations = [
        {
            "name": "GC with Dec 2024",
            "symbol": "GC",
            "secType": "FUT",
            "exchange": "COMEX",
            "expiry": "202412"
        },
        {
            "name": "GC with Dec 24 (short format)",
            "symbol": "GC",
            "secType": "FUT",
            "exchange": "COMEX",
            "expiry": "20241220"  # Try with specific date
        },
        {
            "name": "GC Continuous",
            "symbol": "GC",
            "secType": "CONTFUT",
            "exchange": "COMEX",
            "expiry": None
        },
        {
            "name": "GCZ4 (December symbol)",
            "symbol": "GCZ4",
            "secType": "FUT",
            "exchange": "COMEX",
            "expiry": None
        },
    ]
    
    for var in variations:
        logger.info(f"\n📝 Testing: {var['name']}")
        
        client = ContractFinder()
        if not client.connect_to_ibkr(host="127.0.0.1", port=7497, client_id=2):
            continue
        
        time.sleep(1)
        
        try:
            contract = Contract()
            contract.symbol = var["symbol"]
            contract.secType = var["secType"]
            contract.exchange = var["exchange"]
            contract.currency = "USD"
            if var.get("expiry"):
                contract.lastTradeDateOrContractMonth = var["expiry"]
            
            client.reqContractDetails(1, contract)
            time.sleep(3)
            
            if client.contract_details:
                logger.info(f"   ✅ Found {len(client.contract_details)} contract(s)")
                if len(client.contract_details) > 0:
                    c = client.contract_details[0].contract
                    logger.info(f"   → Use: {c.localSymbol} (expiry: {c.lastTradeDateOrContractMonth})")
            else:
                logger.info("   ❌ No contracts found")
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
        finally:
            client.disconnect_from_ibkr()
            time.sleep(1)

if __name__ == "__main__":
    print("\n🔍 Gold Futures Contract Finder\n")
    
    # First, try to find available contracts
    contract = find_gold_contracts()
    
    if not contract:
        # If that didn't work, try variations
        test_contract_variations()
    
    print("\n" + "=" * 70)
    print("💡 TIPS:")
    print("=" * 70)
    print("1. Make sure your COMEX subscription is fully activated")
    print("2. Try using the 'Local Symbol' (e.g., GCZ4) instead of GC")
    print("3. Some accounts may need to enable futures trading permissions")
    print("4. Check IBKR Account Management > Market Data Subscriptions")
    print("=" * 70 + "\n")