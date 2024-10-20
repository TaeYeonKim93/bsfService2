<template>
  <div class="main-container">
    <div class="left-sidebar">
      <v-list>
        <v-list-item v-for="(button, index) in sidebarButtons" :key="index">
          <v-btn
            block
            class="text-none sidebar-btn"
            @click="selectButton(button.text)"
          >
            <img :src="button.icon" :alt="button.text" class="sidebar-btn-icon" />
          </v-btn>
        </v-list-item>
      </v-list>
    </div>
    <div class="right-content">
      <div id="map"></div>
      <div class="content-sidebar" :class="{ 'expanded': expanded }">
        <h3>{{ selectedButton }}</h3>
        <v-btn
          v-if="['위기탐색', '자원탐색'].includes(selectedButton)"
          @click="performSearch"
          color="primary"
          block
          class="mb-4"
        >
          주소 검색
        </v-btn>
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
import 위기탐색Icon from '/위기탐색.png'
import 자원탐색Icon from '/자원탐색.png'
import 통계Icon from '/통계내용.png'
import 관리Icon from '/관리.png'

declare global {
  interface Window {
    daum: any;
    kakao: any;
  }
}

export default defineComponent({
  name: 'Map',
  setup() {
    const map = ref<L.Map | null>(null);
    const userMarker = ref<L.Marker | null>(null);
    const expanded = ref(false);
    const selectedButton = ref('');
    const sidebarButtons = ref([
      { text: '위기탐색', icon: 위기탐색Icon },
      { text: '자원탐색', icon: 자원탐색Icon },
      { text: '통계', icon: 통계Icon },
      { text: '관리자 모드', icon: 관리Icon }
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

    const selectButton = (buttonText: string) => {
      selectedButton.value = buttonText;
      expanded.value = true;
      console.log(`Selected button: ${selectedButton.value}`);
    };

    const loadKakaoMapsScript = (): Promise<void> => {
      return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=0dcea486f580f014e17750c6dc3af271&libraries=services&autoload=false`;
        script.async = true;
        script.onload = () => {
          window.kakao.maps.load(() => {
            console.log('Kakao Maps API loaded');
            resolve();
          });
        };
        script.onerror = () => reject(new Error('Failed to load Kakao Maps API'));
        document.head.appendChild(script);
      });
    };

    const getAddressCoords = (address: string): Promise<{lat: number, lng: number}> => {
      return new Promise((resolve, reject) => {
        if (!window.kakao || !window.kakao.maps) {
          reject(new Error('Kakao Maps API not loaded'));
          return;
        }
        const geocoder = new window.kakao.maps.services.Geocoder();
        geocoder.addressSearch(address, (result: any, status: any) => {
          if (status === window.kakao.maps.services.Status.OK) {
            resolve({
              lat: parseFloat(result[0].y),
              lng: parseFloat(result[0].x)
            });
          } else {
            reject(new Error('Geocoding failed'));
          }
        });
      });
    };

    const performSearch = async () => {
      if (!window.daum) {
        console.error('Daum Postcode script not loaded');
        return;
      }
      
      try {
        await loadKakaoMapsScript();
        
        new window.daum.Postcode({
          oncomplete: async function(data: any) {
            console.log('Selected address:', data);
            if (map.value) {
              try {
                const coords = await getAddressCoords(data.address);
                console.log('Geocoded coordinates:', coords);
                map.value.setView([coords.lat, coords.lng], 16);
                
                if (userMarker.value) {
                  map.value.removeLayer(userMarker.value);
                }
                
                userMarker.value = L.marker([coords.lat, coords.lng]).addTo(map.value);
                userMarker.value.bindPopup(`<b>${data.address}</b>`).openPopup();
              } catch (error) {
                console.error('Error geocoding address:', error);
                alert('주소를 지도에서 찾을 수 없습니다. 다른 주소를 시도해 주세요.');
              }
            }
          }
        }).open();
      } catch (error) {
        console.error('Failed to load Kakao Maps API:', error);
        alert('지도 서비스를 로드하는 데 실패했습니다. 잠시 후 다시 시도해 주세요.');
      }
    };

    onMounted(async () => {
      initMap();
      console.log('Map component mounted');

      // Load Daum Postcode script
      const postcodeScript = document.createElement('script');
      postcodeScript.src = '//t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js';
      postcodeScript.async = true;
      document.head.appendChild(postcodeScript);
    });

    return {
      getUserLocation,
      sidebarButtons,
      expanded,
      selectedButton,
      selectButton,
      performSearch
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

.left-sidebar {
  width: 80px;
  height: 100vh;
  background-color: #f0f0f0;
  z-index: 1000;
  padding: 0;
}

.right-content {
  flex-grow: 1;
  position: relative;
  overflow: hidden;
  display: flex;
}

#map {
  flex-grow: 1;
  height: 100%;
}

.content-sidebar {
  width: 0;
  height: 100%;
  background-color: white;
  transition: width 0.3s ease;
  overflow: hidden;
  box-shadow: -2px 0 5px rgba(0, 0, 0, 0.1);
  padding: 20px;
  box-sizing: border-box;
}

.content-sidebar.expanded {
  width: 300px;
}

.sidebar-btn {
  padding: 0 !important;
  height: 80px !important;
  width: 80px !important;
  min-width: 80px !important;
  margin-bottom: 0 !important;
  background-color: transparent !important;
  border: none !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.sidebar-btn:hover {
  background-color: #e0e0e0 !important;
}

.sidebar-btn-icon {
  width: 60px;
  height: 60px;
  object-fit: contain;
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
</style>
