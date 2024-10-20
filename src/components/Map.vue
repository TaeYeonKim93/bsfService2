<template>
  <div class="map-container">
    <div id="map" style="height: 100vh;"></div>
    <v-tooltip text="현재위치">
      <template v-slot:activator="{ props }">
        <v-btn
          icon
          class="location-btn"
          color="primary"
          @click="getUserLocation"
          v-bind="props"
        >
          <img src="/free-icon-font-location-crosshairs-9245169.png" alt="Get Location" width="24" height="24" />
        </v-btn>
      </template>
    </v-tooltip>
  </div>
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
    const userMarker = ref<L.Marker | null>(null);

    const initMap = () => {
      map.value = L.map('map', { zoomControl: false }).setView([35.907757, 127.766922], 9);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map.value);

      // Add custom zoom control
      L.control.zoom({
        position: 'bottomright'
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
        if (layer instanceof L.Marker && layer !== userMarker.value) {
          map.value?.removeLayer(layer);
        }
      });

      // Add new markers
      landmarks.forEach((landmark) => {
        const marker = L.marker([landmark.lat, landmark.lon]).addTo(map.value!);
        marker.bindPopup(`<b>${landmark.title}</b><br>${landmark.description}`);
      });
    };

    const getUserLocation = () => {
      if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          if (map.value) {
            // Remove existing user marker if any
            if (userMarker.value) {
              map.value.removeLayer(userMarker.value);
            }

            // Create a new marker for user's location
            userMarker.value = L.marker([latitude, longitude], {
              icon: L.icon({
                iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
                shadowSize: [41, 41],
              })
            }).addTo(map.value);

            userMarker.value.bindPopup('You are here').openPopup();

            // Pan and zoom to user's location
            map.value.setView([latitude, longitude], 13);

            // Update landmarks after moving to the user's location
            updateLandmarks();
          }
        },
        (error) => {
          switch(error.code) {
            case error.PERMISSION_DENIED:
              alert("User denied the request for Geolocation.");
              break;
            case error.POSITION_UNAVAILABLE:
              alert("Location information is unavailable.");
              break;
            case error.TIMEOUT:
              alert("The request to get user location timed out.");
              break;
            default:
              alert("An unknown error occurred.");
              break;
          }
        }
      );
    };

    onMounted(() => {
      initMap();
    });

    return {
      getUserLocation
    };
  }
});
</script>

<style scoped>
@import 'leaflet/dist/leaflet.css';

.map-container {
  position: relative;
}

.location-btn {
  position: absolute;
  bottom: 16px;
  right: 16px;
  z-index: 1000;
}

.leaflet-control-zoom {
  position: absolute;
  bottom: 100px;
  right: 16px;
  z-index: 1000;
}
</style>
