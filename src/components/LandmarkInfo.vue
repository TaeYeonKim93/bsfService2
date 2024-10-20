<template>
  <v-card v-if="landmark" max-width="400" class="mx-auto">
    <v-card-title>{{ landmark.title }}</v-card-title>
    <v-card-text>
      <p>{{ landmark.description }}</p>
      <v-btn
        color="primary"
        :href="landmark.wikipediaUrl"
        target="_blank"
        text
      >
        Read more on Wikipedia
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { Landmark } from '../services/wikipediaService';

export default defineComponent({
  name: 'LandmarkInfo',
  props: {
    landmark: {
      type: Object as PropType<Landmark | null>,
      default: null,
    },
  },
});
</script>
