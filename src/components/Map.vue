<template>
  <div class="main-container">
    <div class="left-header">
      <v-list>
        <v-list-item v-for="(button, index) in sidebarButtons" :key="index">
          <v-btn
            block
            class="text-none sidebar-btn"
            @click="expandSidebar(button.text)"
          >
            <v-icon>{{ button.icon }}</v-icon>
          </v-btn>
        </v-list-item>
      </v-list>
    </div>
    <div class="right-content">
      <div id="map"></div>
      <div class="sliding-sidebar" :class="{ 'expanded': expanded }">
        <h3>{{ selectedButton }}</h3>
        <v-text-field
          v-if="['위기탐색', '자원탐색'].includes(selectedButton)"
          v-model="searchQuery"
          label="장소, 버스, 지하철, 도로 검색"
          prepend-inner-icon="mdi-magnify"
          outlined
          dense
          class="search-bar"
          @keyup.enter="handleSearch"
          :loading="isLoading"
        ></v-text-field>
        <!-- Add more detailed content here based on the selected button -->
      </div>
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
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchLandmarks } from '../services/wikipediaService';
import axios from 'axios';

export default defineComponent({
  name: 'Map',
  setup() {
    const map = ref<L.Map | null>(null);
    const userMarker = ref<L.Marker | null>(null);
    const expanded = ref(false);
    const selectedButton = ref('');
    const searchQuery = ref('');
    const isLoading = ref(false);
    const sidebarButtons = ref([
      { text: '위기탐색', icon: 'mdi-alert' },
      { text: '자원탐색', icon: 'mdi-magnify' },
      { text: '통계', icon: 'mdi-chart-bar' },
      { text: '관리자 모드', icon: 'mdi-account-cog' }
    ]);

    const initMap = () => {
      map.value = L.map('map', { zoomControl: false }).setView([37.4981, 127.0275], 10);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
      }).addTo(map.value);

      L.control.zoom({
        position: 'topright'
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

      map.value.eachLayer((layer) => {
        if (layer instanceof L.Marker && layer !== userMarker.value) {
          map.value?.removeLayer(layer);
        }
      });

      landmarks.forEach((landmark) => {
        const marker = L.marker([landmark.lat, landmark.lon]).addTo(map.value!);
        marker.bindPopup(`<b>${landmark.title}</b>`);
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
            if (userMarker.value) {
              map.value.removeLayer(userMarker.value);
            }

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
            map.value.setView([latitude, longitude], 14);
            updateLandmarks();
          }
        },
        (error) => {
          alert("Error: " + error.message);
        }
      );
    };

    const expandSidebar = (buttonText: string) => {
      expanded.value = !expanded.value;
      selectedButton.value = buttonText;
      console.log(`Sidebar expanded: ${expanded.value}, Selected button: ${selectedButton.value}`);
    };

    const performSearch = async (query: string) => {
      try {
        isLoading.value = true;
        const response = await axios.get(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`);
        const results = response.data;
        
        // Clear previous search results
        map.value?.eachLayer((layer) => {
          if (layer instanceof L.Marker && layer !== userMarker.value) {
            map.value?.removeLayer(layer);
          }
        });

        results.forEach((result: any) => {
          const marker = L.marker([result.lat, result.lon]).addTo(map.value!);
          marker.bindPopup(`<b>${result.display_name}</b>`);
        });

        if (results.length > 0) {
          map.value?.fitBounds(L.latLngBounds(results.map((result: any) => [result.lat, result.lon])));
        } else {
          alert('No results found');
        }
      } catch (error) {
        console.error('Error performing search:', error);
        alert('Error performing search. Please try again.');
      } finally {
        isLoading.value = false;
      }
    };

    const handleSearch = () => {
      console.log('Search query:', searchQuery.value);
      performSearch(searchQuery.value);
    };

    onMounted(() => {
      initMap();
      console.log('Map component mounted');
    });

    return {
      getUserLocation,
      sidebarButtons,
      expanded,
      selectedButton,
      expandSidebar,
      searchQuery,
      handleSearch,
      isLoading
    };
  }
});
</script>

<style scoped>
@import 'leaflet/dist/leaflet.css';

.main-container {
  display: flex;
  width: 100%;
  height: 100vh;
}

.left-header {
  width: 63px;
  height: 100vh;
  background-color: #f0f0f0;
  z-index: 1000;
}

.right-content {
  flex-grow: 1;
  position: relative;
  overflow: hidden;
}

#map {
  width: 100%;
  height: 100%;
}

.sliding-sidebar {
  position: absolute;
  top: 0;
  left: -390px;
  width: 390px;
  height: 100%;
  background-color: white;
  transition: left 0.3s ease;
  z-index: 1000;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.sliding-sidebar.expanded {
  left: 0;
}

.sidebar-btn {
  font-size: 12px !important;
  padding: 8px 4px !important;
  height: auto !important;
  white-space: normal !important;
  text-align: center !important;
  margin-bottom: 8px !important;
  background-color: #ffffff !important;
  color: #333333 !important;
  border: 1px solid #dddddd !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.sidebar-btn:hover {
  background-color: #e0e0e0 !important;
}

.sidebar-btn .v-icon {
  margin-right: 0;
}

.location-btn {
  position: absolute;
  bottom: 20px;
  right: 10px;
  z-index: 1000;
  background-color: white !important;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
  border-radius: 50% !important;
}

.location-btn:hover {
  background-color: #f0f0f0 !important;
}

.leaflet-control-zoom {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
}

.leaflet-control-zoom a {
  background-color: white;
  color: #333;
  border: none;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.leaflet-control-zoom a:hover {
  background-color: #f4f4f4;
}

.search-bar {
  margin-top: 20px;
}

.search-bar :deep(.v-field__outline) {
  border-color: #4CAF50 !important;
}

.search-bar :deep(.v-field__input) {
  padding-left: 40px;
}

.search-bar :deep(.v-input__prepend-inner) {
  margin-top: 8px;
  margin-right: -30px;
}
</style>
