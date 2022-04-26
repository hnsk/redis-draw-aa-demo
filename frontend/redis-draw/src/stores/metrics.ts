import { defineStore } from 'pinia';

export const useMetricsStore = defineStore('metrics', {
  state: () => ({
    sdelay: 0,
    cdelay: 0,
    x: 0,
    y: 0,
    wsSent: 0,
    wsReceived: 0,
  }),

  getters: {},

  actions: {
    setReceivedMetrics(sdelay: number, cdelay: number) {
      this.sdelay = sdelay;
      this.cdelay = cdelay;
      this.wsReceived = this.wsReceived + 1;
    },
    setCoordinates(x: number, y: number) {
      this.x = x;
      this.y = y;
    },
    setSentMetrics() {
      this.wsSent++;
    },
  },
});
