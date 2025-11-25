import { defineStore } from 'pinia';

export const useMarketsStore = defineStore('markets', {
  state: () => ({
    all: [],
  }),
  actions: {
    async fetch() {
      try {
        const response = await fetch('http://localhost:8001/api/symbols');
        const data = await response.json();
        
        // Get latest price for each symbol to determine min_move
        const symbolsWithMinMove = await Promise.all(
          data.symbols.map(async (symbol) => {
            try {
              const priceResponse = await fetch(`http://localhost:8001/api/latest/${symbol}`);
              const priceData = await priceResponse.json();
              
              // Auto-detect min_move based on price level
              let min_move;
              if (priceData.close > 100) {
                min_move = 0.1;  // Gold, indices
              } else if (priceData.close > 10) {
                min_move = 0.01; // Stocks
              } else {
                min_move = 0.0001; // Forex
              }
              
              return {
                symbol_id: symbol,
                id: symbol,
                symbol: symbol,
                name: symbol,
                min_move: min_move,
              };
            } catch (err) {
              return {
                symbol_id: symbol,
                id: symbol,
                symbol: symbol,
                name: symbol,
                min_move: 0.01, // Fallback
              };
            }
          })
        );
        
        this.all = symbolsWithMinMove;
      } catch (err) {
        console.error('Failed to fetch markets:', err);
      }
    },
  },
});