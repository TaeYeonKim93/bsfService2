<template>
  <v-app>
    <v-main>
      <Map />
    </v-main>
  </v-app>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import Map from './components/Map.vue';

export default defineComponent({
  name: 'App',
  components: {
    Map,
  },
});
</script>
