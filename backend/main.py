# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Dict, List
import logging

# Import database connection
from backend.database.database import get_db, SessionLocal






# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="algo_bot_api", version="1.0.0")






# ============================================================
# CORS (Allow frontend to call API)
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",

    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Global Variables
# ============================================================
active_websockets: Dict[str, List[WebSocket]] = {}
scheduler = BackgroundScheduler()



@app.on_event("startup")
async def startup_event():
    logger.info(" Starting API...")
    
    # Start scheduler for refreshing materialized views
    scheduler.add_job(
        func=refresh_materialized_views,
        trigger='interval',
        minutes=5,
        id='refresh_views',
        replace_existing=True
    )
    scheduler.start()
    logger.info("✓ Scheduler started (refreshing views every 5 min)")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    scheduler.shutdown()
    logger.info("✓ Scheduler stopped")

# ============================================================
# Helper Functions
# ============================================================
def refresh_materialized_views():
    """Refresh all materialized views"""
    try:
        db = SessionLocal()
        logger.info(" Refreshing materialized views...")
        db.execute(text("SELECT refresh_all_timeframes()"))
        db.commit()
        logger.info("✓ Materialized views refreshed")
    except Exception as e:
        logger.error(f" Error refreshing views: {e}")
    finally:
        db.close()

# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running",
        "message": "API is online",
        "version": "1.0.0"
    }

@app.get("/api/chart-data/{symbol}/{timeframe}")
async def get_chart_data(
    symbol: str, 
    timeframe: str, 
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """
    Fetch OHLCV data for chart
    
    Parameters:
    - symbol: XAUUSD, ES, NQ, etc.
    - timeframe: 1min, 5min, 15min, 30min, 1H, 4H, 1D
    - limit: Number of bars (default 1000)
    """
    try:
        # Map timeframe to view
        view_map = {
            '1min': 'ohlcv_1min',
            '5min': 'ohlcv_5min',
            '15min': 'ohlcv_15min',
            '30min': 'ohlcv_30min',
            '1H': 'ohlcv_1h',
            '4H': 'ohlcv_4h',
            '1D': 'ohlcv_1d'
        }
        
        view_name = view_map.get(timeframe)
        if not view_name:
            return {
                "error": f"Invalid timeframe: {timeframe}",
                "valid_timeframes": list(view_map.keys())
            }
        
        # Query database
        query = text(f"""
            SELECT 
                EXTRACT(EPOCH FROM timestamp)::INTEGER as time,
                open::FLOAT as open,
                high::FLOAT as high,
                low::FLOAT as low,
                close::FLOAT as close,
                volume::BIGINT as volume
            FROM {view_name}
            WHERE symbol = :symbol
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {'symbol': symbol.upper(), 'limit': limit})
        
        # Convert to list
        bars = []
        for row in result:
            bars.append({
                'time': row.time,
                'open': float(row.open),
                'high': float(row.high),
                'low': float(row.low),
                'close': float(row.close),
                'volume': int(row.volume)
            })
        
        # Reverse to chronological order
        bars.reverse()
        
        logger.info(f"✓ Fetched {len(bars)} {timeframe} bars for {symbol}")
        
        return {
            'symbol': symbol.upper(),
            'timeframe': timeframe,
            'count': len(bars),
            'bars': bars
        }
        
    except Exception as e:
        logger.error(f" Error: {e}")
        return {"error": str(e)}

@app.get("/api/symbols")
async def get_symbols(db: Session = Depends(get_db)):
    """Get available symbols"""
    try:
        result = db.execute(text("""
            SELECT DISTINCT symbol 
            FROM ohlcv_1min 
            ORDER BY symbol
        """))
        symbols = [row.symbol for row in result]
        return {"symbols": symbols}
    except Exception as e:
        logger.error(f" Error: {e}")
        return {"error": str(e)}

@app.get("/api/latest/{symbol}")
async def get_latest_bar(symbol: str, db: Session = Depends(get_db)):
    """Get latest bar"""
    try:
        result = db.execute(text("""
            SELECT 
                EXTRACT(EPOCH FROM timestamp)::INTEGER as time,
                open::FLOAT, high::FLOAT, low::FLOAT, 
                close::FLOAT, volume::BIGINT
            FROM ohlcv_1min
            WHERE symbol = :symbol
            ORDER BY timestamp DESC LIMIT 1
        """), {'symbol': symbol.upper()})
        
        row = result.fetchone()
        if row:
            return {
                'symbol': symbol.upper(),
                'time': row.time,
                'open': float(row.open),
                'high': float(row.high),
                'low': float(row.low),
                'close': float(row.close),
                'volume': int(row.volume)
            }
        return {"error": f"No data for {symbol}"}
    except Exception as e:
        logger.error(f" Error: {e}")
        return {"error": str(e)}

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Database statistics"""
    try:
        result = db.execute(text("""
            SELECT 
                symbol,
                COUNT(*) as bar_count,
                MIN(timestamp) as first_bar,
                MAX(timestamp) as last_bar
            FROM ohlcv_historical_1min
            GROUP BY symbol
            ORDER BY symbol
        """))
        
        stats = []
        for row in result:
            stats.append({
                'symbol': row.symbol,
                'bars': row.bar_count,
                'first': str(row.first_bar),
                'last': str(row.last_bar)
            })
        
        return {'stats': stats}
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"error": str(e)}

# ============================================================
# WebSocket
# ============================================================

@app.websocket("/ws/live-data/{symbol}")
async def websocket_live_data(websocket: WebSocket, symbol: str):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    symbol = symbol.upper()
    if symbol not in active_websockets:
        active_websockets[symbol] = []
    active_websockets[symbol].append(websocket)
    
    logger.info(f"✓ WebSocket connected for {symbol}")
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info(f"✗ WebSocket disconnected for {symbol}")
    finally:
        if symbol in active_websockets:
            active_websockets[symbol].remove(websocket)

# ============================================================
# Admin
# ============================================================

@app.post("/api/admin/refresh-views")
async def manual_refresh():
    """Manually refresh views"""
    try:
        refresh_materialized_views()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )