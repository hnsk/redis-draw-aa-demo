import { defineStore } from 'pinia';

export const useDrawStore = defineStore('draw', {
  state: () => ({
    brushcolor: '#000000',
    brushwidth: 2,
  }),

  getters: {},

  actions: {},
});
