<template>
  <base-modal ref="symbolSearch" :modalId="'symbolSearch'" :title="'Select Symbol'">
    <div id="symbol-selector-wrapper">
      <n-select
        v-model:value="selectedSymbol"
        placeholder="Select Symbol"
        :options="symbolOptions"
        filterable
        @update:value="selectSymbol"
      />
    </div>

    <template #footer>
      <n-button round class="select-button" @click="loadSymbol"> Load Chart </n-button>
    </template>
  </base-modal>
</template>

<script>
import { useMarketsStore } from "@/stores/marketsStore";
import { useCurrentMarketStore } from "@/stores/currentMarketStore";
import { NSelect, NButton } from "naive-ui";
import BaseModal from "@/components/Common/BaseModal.vue";

export default {
  name: "SymbolFormModal",

  components: { NSelect, NButton, BaseModal },

  data() {
    return {
      marketsStore: useMarketsStore(),
      currentMarketStore: useCurrentMarketStore(),
      selectedSymbol: null,
    };
  },

  computed: {
    symbolOptions() {
      // Transform markets store data into options format
      return this.marketsStore.all.map(market => ({
        label: market.symbol,
        value: market.symbol,
      }));
    },
  },

  methods: {
    selectSymbol(value) {
      this.selectedSymbol = value;
    },

    loadSymbol() {
      if (!this.selectedSymbol) {
        console.error("No symbol selected!");
        return;
      }

      // Find the market in the store
      const market = this.marketsStore.all.find(
        m => m.symbol === this.selectedSymbol
      );

      if (market) {
        // Set as current market
        this.currentMarketStore.setMarket(market);
        
        // Close modal
        this.$refs.symbolSearch.close();
      }
    },
  },
};
</script>

<style scoped>
#symbol-selector-wrapper {
  padding: 20px;
}

.select-button {
  width: 100%;
}
</style>