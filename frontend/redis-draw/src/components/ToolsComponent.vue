<template>
  <div>
    <div>
      <q-list bordered dense>
        <q-item
          v-for="i in 10"
          :key="i"
          clickable
          @click="drawstore.brushwidth = i"
          :active="drawstore.brushwidth == i"
        >
          <q-item-section avatar>
            <q-icon
              color="primary"
              name="circle"
              :text-color="drawstore.brushcolor"
              :size="`${i}px`"
            />
          </q-item-section>
          <q-item-section>{{ i }}px</q-item-section>
        </q-item>
      </q-list>
      <q-color v-model="drawstore.brushcolor" no-header />
    </div>
    <div></div>
  </div>
</template>

<script setup type="ts">
import { useDrawStore } from '../stores/draw'

const drawstore = useDrawStore()
</script>
