<template>
  <div id="map" style="height: 100vh;"></div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchLandmarks } from '../services/wikipediaService';

export default defineComponent({
  name: 'Map',
  setup() {
    const map = ref<L.Map | null>(null);

    const initMap = () => {
      map.value = L.map('map').setView([0, 0], 2);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map.value);

      map.value.on('moveend', updateLandmarks);
    };

    const updateLandmarks = async () => {
      if (!map.value) return;

      const bounds = map.value.getBounds();
      const landmarks = await fetchLandmarks(
        bounds.getSouth(),
        bounds.getWest(),
        bounds.getNorth(),
        bounds.getEast()
      );

      // Clear existing markers
      map.value.eachLayer((layer) => {
        if (layer instanceof L.Marker) {
          map.value?.removeLayer(layer);
        }
      });

      // Add new markers
      landmarks.forEach((landmark) => {
        const marker = L.marker([landmark.lat, landmark.lon]).addTo(map.value!);
        marker.bindPopup(`<b>${landmark.title}</b><br>${landmark.description}`);
      });
    };

    onMounted(() => {
      initMap();
    });

    return {};
  }
});
</script>

<style scoped>
@import 'leaflet/dist/leaflet.css';
</style>
