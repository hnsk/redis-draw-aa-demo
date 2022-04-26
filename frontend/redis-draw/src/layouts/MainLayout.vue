<template>
  <q-layout view="hHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="brush"
          aria-label="Menu"
          @click="toggleLeftDrawer"
          @mouseover="toolbarstore.visible = true"
        />

        <q-toolbar-title> Redis Draw </q-toolbar-title>
        <div>
          <q-chip color="primary" text-color="white" icon="my_location">
            Coords: {{ metrics.x }}, {{ metrics.y }}</q-chip
          >
          <q-chip color="primary" text-color="white" icon="storage"
            >Server: {{ metrics.sdelay }}ms</q-chip
          >

          <q-chip color="primary" text-color="white" icon="web"
            >Client: {{ metrics.cdelay }}ms</q-chip
          >
        </div>
      </q-toolbar>
    </q-header>
    <q-drawer v-model="toolbarstore.visible" overlay bordered side="left">
      <ToolsComponent />
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import ToolsComponent from '../components/ToolsComponent.vue';
import { useToolbarStore } from '../stores/toolbar';
import { useMetricsStore } from '../stores/metrics';

const toolbarstore = useToolbarStore();
const metrics = useMetricsStore();

const toggleLeftDrawer = () => {
  toolbarstore.visible = !toolbarstore.visible;
};
</script>
