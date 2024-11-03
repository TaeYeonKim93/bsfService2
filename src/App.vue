<template>
  <v-app>
    <v-main>
      <MiniMap v-if="window.location.pathname === '/map/mini'" />
      <Map v-else />
    </v-main>
  </v-app>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import Map from './components/Map.vue';
import MiniMap from './components/MiniMap.vue';

export default defineComponent({
  name: 'App',
  components: {
    Map,
    MiniMap,
  },
});
</script>
