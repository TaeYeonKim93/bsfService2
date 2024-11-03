<template>
  <div id="mini-map" style="width: 100%; height: 100%;"></div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import Papa from 'papaparse';

export default defineComponent({
  name: 'MiniMap',
  setup() {
    const map = ref<L.Map | null>(null);

    const loadCsvData = async () => {
      try {
        const response = await fetch('/Find_sigungu_with_sido_sigungu.csv');
        const buffer = await response.arrayBuffer();
        const decoder = new TextDecoder('euc-kr');
        const csvText = decoder.decode(buffer);
        
        return new Promise((resolve) => {
          Papa.parse(csvText, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
              const values = results.data.map((row: any) => parseFloat(row.Result));
              const maxResult = Math.max(...values);
              const minResult = Math.min(...values);

              const validData = results.data.map((row: any) => {
                const normalizedResult = ((parseFloat(row.Result) - minResult) / (maxResult - minResult)) * 100;
                return {
                  ...row,
                  Result: normalizedResult,
                  color: getRiskColor(normalizedResult)
                };
              });

              resolve(validData);
            }
          });
        });
      } catch (error) {
        console.error('CSV 파일을 불러오는데 실패했습니다:', error);
        return [];
      }
    };

    const getRiskColor = (normalizedResult: number) => {
      if (normalizedResult >= 80) return '#FF0000';
      if (normalizedResult >= 60) return '#FF4500';
      if (normalizedResult >= 40) return '#FFA500';
      if (normalizedResult >= 20) return '#FFD700';
      return '#FFEB3B';
    };

    const initMap = async () => {
      map.value = L.map('mini-map', {
        zoomControl: true,     // 줌 컨트롤만 활성화
        zoomControlPosition: 'topright',
        dragging: false,       
        touchZoom: false,      
        scrollWheelZoom: false 
      }).setView([36.5, 127.5], 6.5);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: ''
      }).addTo(map.value);

      // 범례 추가
      const legend = L.control({ position: 'bottomright' });
      legend.onAdd = () => {
        const div = L.DomUtil.create('div', 'legend');
        div.innerHTML = `
          <div style="background: white; padding: 5px; border-radius: 5px; font-size: 12px;">
            <div><span style="background: #FF0000"></span>매우 높음</div>
            <div><span style="background: #FF4500"></span>높음</div>
            <div><span style="background: #FFA500"></span>중간</div>
            <div><span style="background: #FFD700"></span>낮음</div>
            <div><span style="background: #FFEB3B"></span>매우 낮음</div>
          </div>
        `;
        return div;
      };
      legend.addTo(map.value);

      const csvData = await loadCsvData();
      
      csvData.forEach((location: any) => {
        try {
          const lat = parseFloat(location.Longitude);
          const lng = parseFloat(location.Latitude);
          
          L.circleMarker([lat, lng], {
            radius: 4,
            color: location.color,
            fillColor: location.color,
            fillOpacity: 0.8,
            weight: 1
          }).addTo(map.value!);
        } catch (error) {
          console.error('데이터 처리 중 오류:', error, location);
        }
      });
    };

    onMounted(async () => {
      await initMap();
    });

    return {};
  }
});
</script>

<style scoped>
#mini-map {
  width: 100%;
  height: 100%;
  border-radius: 8px;
}
</style> 