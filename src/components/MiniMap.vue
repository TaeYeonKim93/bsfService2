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
        // 미니맵 설정
        map.value = L.map('mini-map', {
          zoomControl: true,     // 줌 컨트롤 활성화
          dragging: true,        // 드래그 활성화
          touchZoom: true,       // 터치 줌 활성화
          scrollWheelZoom: true  // 스크롤 줌 활성화
        }).setView([36.5, 127.5], 6.5);  // 더 넓은 뷰로 시작
  
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: ''  // 저작권 표시 제거
        }).addTo(map.value);
  
        // CSV 데이터 로드 및 표시
        const csvData = await loadCsvData();
        
        csvData.forEach((location: any) => {
          try {
            const lat = parseFloat(location.Longitude);
            const lng = parseFloat(location.Latitude);
            
            L.circleMarker([lat, lng], {
              radius: 4,  // 더 작은 원 마커
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