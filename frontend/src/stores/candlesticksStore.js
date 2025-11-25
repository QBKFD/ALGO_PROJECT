import { defineStore } from 'pinia';

export const useCandlesticksStore = defineStore('candlesticks', {
  state: () => ({
    type: 'candlestick',
    data: [],
  }),

  actions: {
    async fetch(symbolID, timeframe, startDate = null, endDate = null, limit = 1000, append = false) {
      try {
        // Convert numeric timeframe to API format
        const timeframeMap = {
          1: '1min',
          5: '5min',
          15: '15min',
          30: '30min',
          60: '1H',
          240: '4H',
          1440: '1D'
        };
        
        const apiTimeframe = timeframeMap[timeframe] || '1min';
        
        const response = await fetch(
          `http://localhost:8001/api/chart-data/${symbolID}/${apiTimeframe}?limit=${limit}`
        );
        
        const result = await response.json();
        console.log('First bar from API:', result.bars[0]);
        console.log('Mapped bar:', {
          time: result.bars[0].time,
          open: parseFloat(result.bars[0].open),
          high: parseFloat(result.bars[0].high),
          low: parseFloat(result.bars[0].low),
          close: parseFloat(result.bars[0].close),
        });
        if (result.error) {
          console.error('API Error:', result.error);
          return;
        }
        
        let newData = result.bars.map((candle) => ({
          time: candle.time,
          open: parseFloat(candle.open),
          high: parseFloat(candle.high),
          low: parseFloat(candle.low),
          close: parseFloat(candle.close),
        }));
        
        if (append) {
          this.data = [...newData, ...this.data];
        } else {
          this.data = newData;
        }
      } catch (err) {
        console.error('Failed to fetch candlestick data:', err);
      }
    },
  },
});