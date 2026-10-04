<script setup>
import { useData } from '../stores/data'
const data = useData()
</script>

<template>
  <div class="dest-list-wrap">
    <div
      v-for="d in data.items" :key="d.id"
      class="dest-item" :class="{ active: d.id === data.selectedId }"
      @click="data.selectedId = d.id"
    >
      <div class="dest-top">
        <div class="dest-name">{{ d.name }}</div>
        <div class="dest-cap" :style="{ color: d.color }">{{ d.cap }}%</div>
      </div>
      <div class="dest-region">{{ d.region }}</div>
      <div class="dest-bar-track"><div class="dest-bar-fill" :style="{ background: d.color, width: d.cap + '%' }"></div></div>
    </div>
  </div>
</template>
