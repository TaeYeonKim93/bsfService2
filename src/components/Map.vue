<template>
  <div class="main-container">
    <div class="left-header">
      <v-list>
        <v-list-item v-for="(button, index) in sidebarButtons" :key="index">
          <v-btn
            block
            class="text-none sidebar-btn"
            :class="{ 'selected': selectedButtons.has(button.text) }"
            @click="handleButtonClick(button)"  
          >
            <img :src="button.icon" :alt="button.text" class="sidebar-btn-icon" />
          </v-btn>
        </v-list-item>
      </v-list>
    </div>
    <div class="right-content">
      <div id="map"></div>
      <div class="sliding-sidebar" :class="{ 'expanded': expanded }">
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
        <div v-if="sidebarData.length > 0" class="mt-4">
          <h4>{{ selectedButton }} 데이터:</h4>
          <v-list>
            <v-list-item v-for="(item, index) in paginatedData" :key="index">
              <v-list-item-title 
                v-if="selectedButton === '위기탐색'"
                @click="moveToLocation(item)" 
                style="cursor: pointer;"
                class="clickable-title"
              >
                {{ item.title }}
              </v-list-item-title>
              <v-list-item-title v-else>
                {{ item.title }}
              </v-list-item-title>
              <v-list-item-subtitle>{{ item.description }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
          <v-pagination
            v-model="currentPage"
            :length="pageCount"
            :total-visible="5"
            class="mt-4"
            prev-text="이전"
            next-text="다음"
          ></v-pagination>
        </div>
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
      <v-btn
        class="chat-btn"
        icon
        elevation="2"
        color="primary"
        @click="toggleChatWindow"
      >
        <v-icon v-if="!chatExpanded" size="32">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
            <path d="M8 4h8l2 4H6l2-4z"/>
            <rect x="9" y="8" width="6" height="12" rx="1"/>
          </svg>
        </v-icon>
        <v-icon v-else>mdi-close</v-icon>
      </v-btn>
      <div class="chat-window" :class="{ 'expanded': chatExpanded }">
        <div class="chat-header">
          <span>(DPG) 손전등 AI 채팅시스템</span>
          <v-btn icon size="small" @click="toggleChatWindow">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>
        <div class="chat-messages">
          <div v-for="(msg, index) in messages" :key="index" 
               :class="['message-container', msg.type]">
            <div class="message-avatar">
              {{ msg.type === 'assistant' ? 'AI' : '나' }}
            </div>
            <div class="message-bubble" v-html="renderMessage(msg.content)">
            </div>
          </div>
          <div v-if="loading" class="message-container assistant">
            <div class="message-avatar">AI</div>
            <div class="message-bubble">
              <v-progress-circular
                indeterminate
                size="20"
                width="2"
                color="primary"
              ></v-progress-circular>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <v-text-field
            v-model="userMessage"
            label="메시지를 입력하세요"
            @keyup.enter="sendMessage"
          ></v-text-field>
          <v-btn @click="sendMessage" :loading="loading">전송</v-btn>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref, computed } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 위기탐색Icon from '/images/위기탐색.png'
import 자원탐색Icon from '/images/자원탐색.png'
import 관리Icon from '/images/관리.png'
import Papa from 'papaparse';
import { marked } from 'marked';

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
    const adminUrl = window.location.origin + '/admin/';
    const sidebarButtons = ref([
      { text: '위기탐색', icon: 위기탐색Icon },
      { text: '자원탐색', icon: 자원탐색Icon },
      { text: '관리자 모드', icon: 관리Icon, url: adminUrl }
    ]);
    const searchedAddress = ref('');
    const sidebarData = ref<any[]>([]);
    const currentPage = ref(1);
    const itemsPerPage = 5;
    const chatExpanded = ref(false);
    const userMessage = ref('');
    const selectedButtons = ref<Set<string>>(new Set());
    const messages = ref<Array<{type: 'user' | 'assistant', content: string}>>([
      {
        type: 'assistant',
        content: `안녕하세요! 저는 지역 위험도 분석, 복지자원 안내 AI 어시스턴트입니다. 
        
예시와 같이 질문해 주시면 상세한 분석 결과를 알려드립니다:

- "인천 연수구 위험도와 위험요인 분석해줘"
- "서울 강남구의 위험도는 어떤가요?"
- "부산 해운대구 위험요인을 알려주세요"
- "인천 연수구 복지자원들은 어떤게 있어?"

어떤 지역의 위험도가 궁금하신가요?`
      }
    ]);
    const loading = ref(false);

    const paginatedData = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage;
      const end = start + itemsPerPage;
      return sidebarData.value.slice(start, end);
    });

    const pageCount = computed(() => Math.ceil(sidebarData.value.length / itemsPerPage));

    const loadCsvData = async () => {
      try {
        const response = await fetch('/Find_sigungu_with_sido_sigungu.csv');
        const buffer = await response.arrayBuffer();
        // EUC-KR 디코더 생성
        const decoder = new TextDecoder('euc-kr');
        const csvText = decoder.decode(buffer);
        
        return new Promise((resolve) => {
          Papa.parse(csvText, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
              // 최대값과 최소값 찾기
              const values = results.data.map((row: any) => parseFloat(row.Result));
              const maxResult = Math.max(...values);
              const minResult = Math.min(...values);

              // 데이터 정규화 및 색상 적용
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

    // 위험도에 따른 색상 계 함수 수정
    const getRiskColor = (normalizedResult: number) => {
      if (normalizedResult >= 80) return '#FF0000';       // 빨강 (매우 높음)
      if (normalizedResult >= 60) return '#FF4500';       // 주황빨강 (높음)
      if (normalizedResult >= 40) return '#FFA500';       // 주황 (중간)
      if (normalizedResult >= 20) return '#FFD700';       // 황금색 (낮음)
      return '#FFEB3B';                                   // 연한 노랑 (매우 낮음)
    };

    // 범례 추가 함수
    const addLegend = () => {
      const legend = L.control({ position: 'topright' });

      legend.onAdd = () => {
        const div = L.DomUtil.create('div', 'info legend');
        div.style.backgroundColor = 'white';
        div.style.padding = '10px';
        div.style.borderRadius = '5px';
        div.style.boxShadow = '0 1px 5px rgba(0,0,0,0.2)';
        div.style.fontSize = '12px';

        const grades = [0, 20, 40, 60, 80];
        const labels = ['매우 낮음', '낮음', '중간', '높음', '매우 높음'];

        div.innerHTML = '<div style="margin-bottom: 5px;"><strong>위험도</strong></div>';

        for (let i = 0; i < grades.length; i++) {
          div.innerHTML += `
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
              <div style="
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background-color: ${getRiskColor(grades[i])};
                border: 1px solid white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                margin-right: 8px;
              "></div>
              <span>${labels[i]}</span>
            </div>
          `;
        }

        return div;
      };

      legend.addTo(map.value!);
    };

    // 3. 지도 초기화 함수
    const initMap = async () => {
      map.value = L.map('map', { zoomControl: false }).setView([36.5, 127.5], 7);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
      }).addTo(map.value);

      L.control.zoom({
        position: 'topright'
      }).addTo(map.value);

      // CSV 데이터 로드 및 표시
      const csvData = await loadCsvData();
      
      const createCircleIcon = (color: string) => {
        return L.divIcon({
          className: 'custom-circle-marker',
          html: `
            <div class="circle" style="background-color: ${color};"></div>
          `,
          iconSize: [20, 20],
          iconAnchor: [10, 10],
          popupAnchor: [0, -10]
        });
      };

      csvData.forEach((location: any) => {
        try {
          const lat = parseFloat(location.Longitude);
          const lng = parseFloat(location.Latitude);
          
          // 위험도 분석 이미지 요청 함수
          const getAnalysisImage = async (sido: string, sigungu: string) => {
            try {
              const response = await fetch('/xai/analyze', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ sido, sigungu })
              });
              
              const data = await response.json();
              return data.success ? data.image : null;
            } catch (error) {
              console.error('위험도 분석 요청 실패:', error);
              return null;
            }
          };

          // 마커 생성 및 팝업 설정
          const marker = L.marker([lat, lng], {
            icon: createCircleIcon(location.color)
          }).addTo(map.value!);

          // 팝업 클릭 이벤트 처리
          marker.on('click', async () => {
            const analysisImage = await getAnalysisImage(location.Sido, location.Sigungu);
            
            const popupContent = `
              <div style="
                font-family: 'Noto Sans KR', sans-serif;
                text-align: center;
                background: white;
                border-radius: 8px;
                min-width: 500px;
              ">
                <strong style="font-size: 24px;">${location.Sido} ${location.Sigungu}</strong><br>
                <span style="font-size: 20px;">위험도: ${location.Result.toFixed(2)}%</span>
                ${analysisImage ? `
                  <div style="margin-top: 20px;">
                    <img src="data:image/png;base64,${analysisImage}" 
                         alt="위험도 분석" 
                         style="width: 500px;
                                max-width: 100%;
                                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                                border-radius: 8px;"/>
                  </div>
                ` : ''}
              </div>
            `;
            
            marker.setPopupContent(popupContent);
          });

          // 초기 팝업 내용 설정
          const initialContent = `
            <div style="
              font-family: 'Noto Sans KR', sans-serif;
              padding: 20px;
              text-align: center;
              background: white;
              border-radius: 8px;
              min-width: 200px;
            ">
              <strong style="font-size: 16px;">${location.Sido} ${location.Sigungu}</strong><br>
              <span style="font-size: 14px;">위험도: ${location.Result.toFixed(2)}%</span>
            </div>
          `;

          // 초기 팝업 설정
          marker.bindPopup(initialContent, {
            maxWidth: 500,
            className: 'custom-popup'
          });

        } catch (error) {
          console.error('마커 생성 중 오류:', error);
        }
      });

      // CSS 스타일
      const style = document.createElement('style');
      style.textContent = `
        .custom-circle-marker {
          background: none !important;
        }
        .circle {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          border: 2px solid white;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
      `;
      document.head.appendChild(style);

      // 범례 추가
      const legend = L.control({ position: 'topright' });

      legend.onAdd = () => {
        const div = L.DomUtil.create('div', 'info legend');
        div.style.backgroundColor = 'white';
        div.style.padding = '10px';
        div.style.borderRadius = '5px';
        div.style.boxShadow = '0 1px 5px rgba(0,0,0,0.2)';
        div.style.fontSize = '12px';
        div.style.marginTop = '10px';

        const grades = [0, 20, 40, 60, 80];
        const labels = ['매우 낮음', '낮음', '중간', '높음', '매우 높음'];

        div.innerHTML = '<div style="margin-bottom: 5px;"><strong>위험도</strong></div>';

        for (let i = 0; i < grades.length; i++) {
          div.innerHTML += `
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
              <div style="
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background-color: ${getRiskColor(grades[i])};
                border: 1px solid white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                margin-right: 8px;
              "></div>
              <span>${labels[i]}</span>
            </div>
          `;
        }

        return div;
      };

      legend.addTo(map.value!);
    };

    const getRiskLevel = (normalizedResult: number) => {
      if (normalizedResult >= 80) return '매우 높음';
      if (normalizedResult >= 60) return '높음';
      if (normalizedResult >= 40) return '중간';
      if (normalizedResult >= 20) return '낮음';
      return '매우 낮음';
    };

    const getClosestRiskData = (coords: { lat: number, lng: number }, csvData: any[], limit: number = 10) => {
      return csvData
        .filter(location => {
          // 효한 데이터만 필링
          const lat = parseFloat(location.Longitude);
          const lng = parseFloat(location.Latitude);
          return !isNaN(lat) && !isNaN(lng) && location.Result !== undefined;
        })
        .map(location => {
          const locationLat = parseFloat(location.Longitude);
          const locationLng = parseFloat(location.Latitude);
          const distance = L.latLng(coords.lat, coords.lng).distanceTo(L.latLng(locationLat, locationLng));
          return { 
            ...location, 
            Result: parseFloat(location.Result) || 0,
            distance 
          };
        })
        .sort((a, b) => a.distance - b.distance)
        .slice(0, limit);
    };

    const getUserLocation = () => {
      if (!navigator.geolocation) {
        alert('브라우저가 위치 정보를 원하지 않습니다');
        return;
      }

      // 아무 모드도 선택되어 있지 않으면 위기탐색 모드 자동 활성화
      if (!selectedButton.value) {
        selectedButtons.value.add('위기탐색');
        expanded.value = true;
        selectedButton.value = '위기탐색';
      }

      // 페이지네이션 초기화
      currentPage.value = 1;

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          if (map.value) {
            if (userMarker.value) {
              map.value.removeLayer(userMarker.value);
            }

            // 위기탐색 데이터 처리
            if (selectedButton.value === '위기탐색') {
              const csvData = await loadCsvData();
              const nearestLocations = getClosestRiskData({ lat: latitude, lng: longitude }, csvData);
              const closestLocation = nearestLocations[0];

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

              userMarker.value.bindPopup(`
                <div style="font-family: 'Noto Sans KR', sans-serif;">
                  <b>현재 위치</b><br>
                  가장 가까운 지역 위험도: <span style="color: ${closestLocation.color}; font-weight: bold; 
                      text-shadow: 1px 1px 3px #000">
                    ${closestLocation.Result.toFixed(1)}%
                  </span><br>
                  <small>(${closestLocation.Sido} ${closestLocation.Sigungu})</small>
                </div>
              `).openPopup();

              sidebarData.value = nearestLocations.map(location => ({
                title: `${location.Sido} ${location.Sigungu}`,
                description: `지역 위험도: ${getRiskLevel(location.Result)} (${location.Result.toFixed(1)}%) - ${(location.distance / 1000).toFixed(1)}km`,
                lat: parseFloat(location.Longitude),
                lng: parseFloat(location.Latitude)
              }));
            }
            // 자원탐색 데이터 처리
            else if (selectedButton.value === '자원탐색') {
              // 위험도 데이터 먼저 로드
              const csvData = await loadCsvData();
              const nearestLocations = getClosestRiskData({ lat: latitude, lng: longitude }, csvData);
              const closestLocation = nearestLocations[0];

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

              // 카카오 지도 API를 사용하여 재 위치의 주소 정 가져오
              const geocoder = new window.kakao.maps.services.Geocoder();
              
              geocoder.coord2RegionCode(longitude, latitude, (result: any, status: any) => {
                if (status === window.kakao.maps.services.Status.OK) {
                  const sido = result[0].region_1depth_name;
                  const sigungu = result[0].region_2depth_name;
                  const gu = result[0].region_3depth_name;
                  
                  // 전체 결과 로깅
                  console.log('카카오 지도 API 전 응답:', result);
                  
                  // 행정동 기준 값 사용 (result[0])
                  const fullSigungu = sigungu + ' ' + gu;           // "수원시 권선구"
                  
                  console.log('정규화 전 주소 정보:', { sido, sigungu: fullSigungu });

                  // 검색 위치 정규화
                  const searchLocation = normalizeLocation({
                    sido: sido,
                    sigungu: fullSigungu
                  });

                  console.log('정규화된 검색 위치:', searchLocation);

                  userMarker.value?.bindPopup(`
                    <div style="font-family: 'Noto Sans KR', sans-serif;">
                      <b>현재 위치</b><br>
                      가장 가까운 지역 위험도: <span style="color: ${closestLocation.color}; font-weight: bold; 
                          text-shadow: 1px 1px 3px #000">
                        ${closestLocation.Result.toFixed(1)}%
                      </span><br>
                      <small>(${closestLocation.Sido} ${closestLocation.Sigungu})</small>
                    </div>
                  `).openPopup();

                  // 복지자원 데이터 로드 및 필터링
                  fetch('/bokjiro_content.json')
                    .then(response => response.json())
                    .then(data => {
                      const localResources = data
                        .filter((item: any) => {
                          const isMatch = item.sido === sido && (!item.gu || item.gu === sigungu);
                          return isMatch;
                        })
                        .sort((a: any, b: any) => {
                          // 1. 현재 구와 일치하는 항목 우선
                          const aMatchesCurrentGu = a.gu === sigungu;
                          const bMatchesCurrentGu = b.gu === sigungu;
                          if (aMatchesCurrentGu && !bMatchesCurrentGu) return -1;
                          if (!aMatchesCurrentGu && bMatchesCurrentGu) return 1;

                          // 2. 구 정보가 있는 항목 우선
                          const aHasGu = !!a.gu;
                          const bHasGu = !!b.gu;
                          if (aHasGu && !bHasGu) return -1;
                          if (!aHasGu && bHasGu) return 1;

                          // 3. 제목 기준 가나다순 정렬
                          return a.title.localeCompare(b.title, 'ko-KR');
                        });

                      sidebarData.value = localResources.map((resource: any) => {
                        let descriptionText = '';
                        
                        if (resource.gu) {
                          descriptionText = `${resource.sido} ${resource.gu}`;
                        } else {
                          descriptionText = `${resource.sido} 전체`;
                        }
                        
                        if (resource.target) {
                          descriptionText += `\n지원대상: ${resource.target}`;
                        }
                        if (resource.content) {
                          descriptionText += `\n지원내용: ${resource.content}`;
                        }
                        
                        return {
                          title: resource.title,
                          description: descriptionText || '상세정보 없음'
                        };
                      });

                      if (sidebarData.value.length === 0) {
                        sidebarData.value = [{
                          title: '검색 결과 없음',
                          description: '해당 지역의 등록된 복지자원이 없습니다.'
                        }];
                      }
                    })
                    .catch(error => {
                      console.error('복지자원 데이터 처리 중 오류:', error);
                      sidebarData.value = [{
                        title: '데이터 로드 오류',
                        description: '복지자원 정보를 불러오는데 실패했습니다.'
                      }];
                    });
                }
              });
            }

            map.value.setView([latitude, longitude], 14);
          }
        },
        (error) => {
          alert("위치 정보를 가져오는데 실패했습니다: " + error.message);
        }
      );
    };

    const expandSidebar = async (buttonText: string) => {
      if (selectedButtons.value.has(buttonText)) {
        selectedButtons.value.delete(buttonText);
        expanded.value = false;
        selectedButton.value = '';
        return;
      }

      selectedButtons.value.clear();
      selectedButtons.value.add(buttonText);
      selectedButton.value = buttonText;
      expanded.value = true;

      // 여기서 fetchSidebarData 호출
      await fetchSidebarData(buttonText);
    };

    const fetchSidebarData = async (buttonType: string) => {
      console.log('사이드바 데이터 로드 시작:', buttonType);
      
      if (!window.kakao?.maps) {
        try {
          await loadKakaoMapsScript();
        } catch (error) {
          console.error('카카오맵 API 로드 실패:', error);
          return;
        }
      }

      switch (buttonType) {
        case '위기탐색':
          if (userMarker.value) {
            const position = userMarker.value.getLatLng();
            loadCsvData().then(csvData => {
              const nearestLocations = getClosestRiskData({ lat: position.lat, lng: position.lng }, csvData);
              
              sidebarData.value = nearestLocations.map(location => {
                const result = parseFloat(location.Result) || 0;
                const distance = location.distance || 0;
                
                return {
                  title: `${location.Sido || ''} ${location.Sigungu || ''}`,
                  description: `지역 위험도: ${getRiskLevel(result)} (${result.toFixed(1)}%) - ${(distance / 1000).toFixed(1)}km`,
                  lat: parseFloat(location.Longitude),
                  lng: parseFloat(location.Latitude)
                };
              });
            }).catch(error => {
              console.error('데이터 로드 중 오류:', error);
              sidebarData.value = [{
                title: '데이터 로드 오류',
                description: '데이터를 불러오는 중 문제가 발생했습니다.'
              }];
            });
          }
          break;
        case '자원탐색':
          if (userMarker.value) {
            const position = userMarker.value.getLatLng();
            const geocoder = new window.kakao.maps.services.Geocoder();
            
            geocoder.coord2RegionCode(position.lng, position.lat, (result: any, status: any) => {
              if (status === window.kakao.maps.services.Status.OK) {
                const sido = result[0].region_1depth_name;
                const sigungu = result[0].region_2depth_name;
                
                fetch('/bokjiro_content.json')
                  .then(response => response.json())
                  .then(data => {
                    const localResources = data
                      .filter((item: any) => {
                        // 복지자원 치 정규화
                        const itemLocation = normalizeLocation({
                          sido: item.sido,
                          sigungu: item.gu
                        });

                        // 검색 위치 정규화
                        const searchLocation = normalizeLocation({
                          sido: sido,
                          sigungu: sigungu
                        });

                        // 도 레벨 매칭
                        const sidoMatch = itemLocation.sido === searchLocation.sido;
                        
                        // 시군구 레벨 매칭 (시 전체 데이터도 포함)
                        const sigunguMatch = !item.gu || // 시 전체 데이터
                          item.gu.includes(sigungu.split(' ')[0]); // 시군구  어로 매칭

                        return sidoMatch && (sigunguMatch || !item.gu);
                      })
                      .sort((a, b) => {
                        // 1. 현 시군구와 정확히 일치하는 항목 우선
                        const exactSigunguMatch = (item: any) => 
                          item.gu && item.gu.includes(sigungu.split(' ')[0]);
                        const aExactMatch = exactSigunguMatch(a);
                        const bExactMatch = exactSigunguMatch(b);
                        
                        if (aExactMatch && !bExactMatch) return -1;
                        if (!aExactMatch && bExactMatch) return 1;

                        // 2. 구체적인 지역 정보가 있는 항목 우선
                        if (a.gu && !b.gu) return -1;
                        if (!a.gu && b.gu) return 1;

                        // 3. 제목 기준 가나다순
                        return a.title.localeCompare(b.title, 'ko-KR');
                      });

                    sidebarData.value = localResources.map((resource: any) => ({
                      title: resource.title,
                      description: `${resource.sido} ${resource.gu || '전체'}\n${resource.target ? `지원대상: ${resource.target}\n` : ''}${resource.content ? `지원내용: ${resource.content}` : ''}`
                    }));

                    if (sidebarData.value.length === 0) {
                      sidebarData.value = [{
                        title: '검색 결과 없음',
                        description: '해당 지역의 등록된 복지자원이 없습니다.'
                      }];
                    }
                  })
                  .catch(error => {
                    console.error('복지자원 데이터 처리 중 오류:', error);
                    sidebarData.value = [{
                      title: '데이터 로드 오류',
                      description: '복지자원 정보를 불러오는데 실패했습니다.'
                    }];
                  });
              }
            });
          }
          break;
      }
    };

    const loadKakaoMapsScript = (): Promise<void> => {
      return new Promise((resolve, reject) => {
        if (window.kakao?.maps) {
          resolve();
          return;
        }

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
      console.log('주소 검색 시작');
      if (!window.daum) {
        console.error('Daum Postcode script not loaded');
        return;
      }
      
      try {
        await loadKakaoMapsScript();
        console.log('Kakao Maps API 로드 완료');
        
        new window.daum.Postcode({
          oncomplete: async function(data: any) {
            console.log('선택된 주소 데이터:', data);
            if (map.value) {
              try {
                const coords = await getAddressCoords(data.address);
                console.log('좌표 변환 결과:', coords);
                
                if (userMarker.value) {
                  map.value.removeLayer(userMarker.value);
                }
                
                const csvData = await loadCsvData();
                const nearestLocations = getClosestRiskData(coords, csvData);
                const closestLocation = nearestLocations[0];
                
                userMarker.value = L.marker([coords.lat, coords.lng]).addTo(map.value);
                userMarker.value.bindPopup(`
                  <div style="font-family: 'Noto Sans KR', sans-serif;">
                    <b>${data.address}</b><br>
                    가장 가까운 지역 위험도: <span style="color: ${closestLocation.color}; font-weight: bold; 
                    text-shadow: 1px 1px 3px #000">
                      ${closestLocation.Result.toFixed(1)}%
                    </span><br>
                    <small>(${closestLocation.Sido} ${closestLocation.Sigungu})</small>
                  </div>
                `).openPopup();

                if (selectedButton.value === '위기탐색') {
                  sidebarData.value = nearestLocations.map(location => ({
                    title: `${location.Sido} ${location.Sigungu}`,
                    description: `지역 위험도: ${getRiskLevel(location.Result)} (${location.Result.toFixed(1)}%) - ${(location.distance / 1000).toFixed(1)}km`,
                    lat: parseFloat(location.Longitude),
                    lng: parseFloat(location.Latitude)
                  }));
                }

                if (selectedButton.value === '자원탐색') {
                  console.log('자원탐색 이터 로드 시작');
                  fetch('/bokjiro_content.json')
                    .then(response => {
                      console.log('복지자원 데이터 응답 받음');
                      return response.json();
                    })
                    .then(jsonData => {
                      console.log('전체 복지자원 데이터 수:', jsonData.length);
                      
                      // 검색 위치 정규화
                      const searchLocation = normalizeLocation({
                        sido: data.sido,
                        sigungu: data.sigungu
                      });
                      
                      console.log('정규화된 검색 위치:', searchLocation);

                      const localResources = jsonData
                        .filter((item: any) => {
                          // 복지자원 위치 정화
                          const itemLocation = normalizeLocation({
                            sido: item.sido,
                            sigungu: item.gu
                          });

                          // 검색 위치 정규화
                          const searchLocation = normalizeLocation({
                            sido: data.sido,
                            sigungu: data.sigungu
                          });

                          // 시도 레벨 매칭
                          const sidoMatch = itemLocation.sido === searchLocation.sido;
                          
                          // 시군구 레벨 매칭 (시 전체 데이터도 포함)
                          const sigunguMatch = !item.gu || // 시 전체 데이터
                            item.gu.includes(data.sigungu.split(' ')[0]); // 시군 예: "성남시")

                          return sidoMatch && (sigunguMatch || !item.gu);
                        })
                        .sort((a, b) => {
                          // 1. 현재 시군구와 정확히 일치하는 항목 우선
                          const exactSigunguMatch = (item: any) => 
                            item.gu && item.gu.includes(data.sigungu.split(' ')[0]);
                          const aExactMatch = exactSigunguMatch(a);
                          const bExactMatch = exactSigunguMatch(b);
                          
                          if (aExactMatch && !bExactMatch) return -1;
                          if (!aExactMatch && bExactMatch) return 1;

                          // 2. 구체적인 지역 정보가 있는 항목 우선
                          if (a.gu && !b.gu) return -1;
                          if (!a.gu && b.gu) return 1;

                          // 3. 제목 기준 가나다순
                          return a.title.localeCompare(b.title, 'ko-KR');
                        });

                      console.log('정렬된 복지자원 순서:');
                      localResources.forEach((resource, index) => {
                        console.log(`${index + 1}. [${resource.gu ? '구단위' : '시단위'}] ${resource.title} (${resource.sido} ${resource.gu || '전체'})`);
                      });

                      sidebarData.value = localResources.map((resource: any) => ({
                        title: resource.title,
                        description: resource.gu 
                          ? `${resource.sido} ${resource.gu}` 
                          : `${resource.sido} 전체`
                      }));

                      if (localResources.length === 0) {
                        console.log('검색 결과 없음. 상세 정보:', {
                          original: {
                            sido: data.sido,
                            sigungu: data.sigungu
                          },
                          normalized: searchLocation,
                          sampleData: jsonData.slice(0, 5).map(item => ({
                            sido: item.sido,
                            gu: item.gu
                          }))
                        });
                        sidebarData.value = [{
                          title: '검색 결과 없음',
                          description: '해 지역의 등록된 복지자원이 없습니다.'
                        }];
                      } else {
                        console.log(`총 ${sidebarData.value.length}개의 복지자이 검색되었습니다.`);
                      }
                    })
                    .catch(error => {
                      console.error('복지자원 데이터 처리 중 오류:', error);
                      sidebarData.value = [{
                        title: '데이터 로드 오류',
                        description: '복지자원 정보를 불러오는데 실패했습니다.'
                      }];
                    });
                }
              } catch (error) {
                console.error('주소 좌표 변환 중 오류:', error);
                alert('주소를 도에서 찾을 수 없습니다. 다른 주소를 시도해 주세요.');
              }
            }
          }
        }).open();
      } catch (error) {
        console.error('Kakao Maps API 로드 실패:', error);
        alert('지도 서비스를 로드하는 데 실패했습니다. 잠시 후 다시 시도해 주세요.');
      }
    };

    const toggleChatWindow = () => {
      chatExpanded.value = !chatExpanded.value;
    };

    const sendMessage = async () => {
      if (!userMessage.value.trim()) return;
      
      const message = userMessage.value;
      console.log('사용자 메시지:', message);
      messages.value.push({ type: 'user', content: message });
      userMessage.value = '';
      loading.value = true;

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message }),
        });

        if (!response.ok) throw new Error('채팅 요청 실패');
        
        const data = await response.json();
        console.log('서 응답 데이터:', data);

        // AI 응답이 있을 경우에만 메시지 추가
        if (data.response) {
          console.log('AI 응답 추가:', data.response);
          messages.value.push({ type: 'assistant', content: data.response });
        }

        // functionCall 처리 로깅
        if (data.functionCall) {
          console.log('Function call 감지:', data.functionCall);
          
          if (data.functionCall.name === 'focusLocation') {
            console.log('focusLocation 함수 실행 시작');
            const { sido, sigungu } = data.functionCall.arguments;
            console.log('정규화 전 위치 정보:', { sido, sigungu });
            
            // 위치 정보 정규화
            const normalizedLocation = normalizeLocation({
              sido,
              sigungu
            });
            console.log('정규화된 위치 정보:', normalizedLocation);
            
            const coordinates = await findLocationCoordinates(
              normalizedLocation.sido, 
              normalizedLocation.sigungu
            );
            console.log('좌표 변환 결과:', coordinates);
            
            if (coordinates) {
              console.log('지도 이동 시작:', coordinates);
              map.value.setView([coordinates.lat, coordinates.lng], 14);
              
              // 해당 위치의 원형 마커 찾기
              map.value.eachLayer((layer: any) => {
                if (layer instanceof L.Marker) {
                  const markerLatLng = layer.getLatLng();
                  if (markerLatLng.lat === coordinates.lat && markerLatLng.lng === coordinates.lng) {
                    // 원형 마커를 찾으면 클릭 이벤트 발생
                    layer.fire('click');
                  }
                }
              });
            }
          }
        }
      } catch (error) {
        console.error('Chat error:', error);
        messages.value.push({ type: 'assistant', content: '죄송합니다. 오류가 발생했습니다.' });
      } finally {
        loading.value = false;
      }
    };

    const findLocationCoordinates = async (sido: string, sigungu: string) => {
      console.log('findLocationCoordinates 시작:', { sido, sigungu });
      const csvData = await loadCsvData();
      console.log('CSV 데이터 로드됨:', csvData.length, '개의 항목');
      
      const location = csvData.find((item: any) => {
        console.log('검색중:', item.Sido, item.Sigungu);
        return item.Sido === sido && item.Sigungu === sigungu;
      });
      
      console.log('찾은 위치 데이터:', location);
      
      if (location) {
        const result = {
          // 위도와 경도를 올바르게 매핑
          lat: parseFloat(location.Longitude),  // 위도
          lng: parseFloat(location.Latitude),   // 경도
          riskLevel: parseFloat(location.Result)
        };
        console.log('변환된 좌표:', result);
        return result;
      }
      console.log('위치를 찾지 못함');
      return null;
    };

    const moveToLocation = (item: any) => {
      if (item.lat && item.lng && map.value) {
        // 지도 뷰 이동
        map.value.setView([item.lat, item.lng], 14);
        
        // 기존 마커가 있다면 제거
        if (userMarker.value) {
          map.value.removeLayer(userMarker.value);
        }
        
        // 새 마커 성
        userMarker.value = L.marker([item.lat, item.lng], {
          icon: L.icon({
            iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
            shadowSize: [41, 41],
          })
        }).addTo(map.value);

        // 팝업 추가
        userMarker.value.bindPopup(`
          <div style="font-family: 'Noto Sans KR', sans-serif;">
            <b>${item.title}</b><br>
            ${item.description}
          </div>
        `).openPopup();
      }
    };

    const normalizeLocation = (location: { sido: string, sigungu?: string }) => {
      // 시도 정규화
      let normalizedSido = location.sido
        .replace(/^서울광역시$/, '서울특별시')
        .replace(/^서울$/, '서울특별시')
        .replace(/^(부산|대구|인천|광주|대전|울산)$/, '$1광역시')
        .replace(/^전남$/, '전라남도')
        .replace(/^전북$/, '전라북도')
        .replace(/^충남$/, '충청남도')
        .replace(/^충북$/, '충청북도')
        .replace(/^경남$/, '경상남도')
        .replace(/^경북$/, '경상북도')
        .replace(/^강원$/, '강원도')
        .replace(/^경기$/, '경기도')
        .replace(/^세종$/, '세종특별자치시')
        .replace(/^제주특별자치도$/, '제주도')
        .replace(/^제주$/, '제주도');

      // 시군구 정규화 - 첫 번째 시군구만 추출
      let normalizedSigungu = '';
      if (location.sigungu) {
        const parts = location.sigungu.split(' ');
        if (parts.length >= 2) {
          // "성남시 분당구"와 같은 형태면 "성남시"만 사용
          normalizedSigungu = parts[0];
        } else {
          normalizedSigungu = location.sigungu;
        }
      }

      return {
        sido: normalizedSido,
        sigungu: normalizedSigungu
      };
    };

    const handleButtonClick = (button: any) => {
      if (button.url) {
        window.open(button.url, '_blank');
      } else {
        expandSidebar(button.text);
      }
    };

    // marked 설정 추가
    marked.setOptions({
      breaks: true,  // 줄바꿈 활성화
      gfm: true      // GitHub Flavored Markdown 활성화
    });

    // 메시지 렌더링을 위한 computed 속성 추가
    const renderMessage = (content: string) => {
      return marked(content);
    };

    onMounted(async () => {
      await initMap();
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
      expandSidebar,
      performSearch,
      searchedAddress,
      sidebarData,
      currentPage,
      paginatedData,
      pageCount,
      chatExpanded,
      
      userMessage,
      toggleChatWindow,
      sendMessage,
      selectedButtons, // 이 줄을 추가
      messages,
      loading,
      moveToLocation,
      handleButtonClick,
      renderMessage,
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
.v-list-item .v-btn.sidebar-btn {
  padding: 0 !important;
  height: 80px !important;
  width: 80px !important;
  min-width: 80px !important;
  max-width: 80px !important;
  margin: 0 !important;
  background-color: transparent !important;
  border: none !important;
}

.v-list-item .v-btn.sidebar-btn .v-btn__content {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  height: 100% !important;
  width: 100% !important;
  padding: 0 !important;
}

.sidebar-btn-icon {
  width: 60px;
  height: 60px;
  object-fit: contain;
}

/* 추가: v-list-item의 패딩 제거 */
.v-list-item {
  padding: 0 !important;
}

/* 추가: v-list의 패딩 제거 */
.v-list {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
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

.chat-btn {
  position: fixed;
  bottom: 80px;
  right: 20px;
  z-index: 1000;
  border-radius: 50% !important;
  width: 56px !important;
  height: 56px !important;
  background-color: #1976d2 !important;
  color: white !important;
  box-shadow: 0 3px 5px -1px rgba(0,0,0,.2),
              0 6px 10px 0 rgba(0,0,0,.14),
              0 1px 18px 0 rgba(0,0,0,.12) !important;
  transition: all 0.3s ease !important;
}

.chat-btn:hover {
  transform: scale(1.05);
  background-color: #1565c0 !important;
}

.chat-btn .v-icon {
  transition: transform 0.3s ease;
}

.chat-btn:hover .v-icon {
  transform: scale(1.1);
}

.chat-window {
  position: fixed;
  bottom: -600px;
  right: 20px;
  width: 400px;
  max-width: none;
  height: 600px;
  background-color: white;
  transition: bottom 0.3s ease;
  z-index: 1001;
  display: flex;
  flex-direction: column;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
}

.chat-window.expanded {
  bottom: 0;
}

.chat-header {
  padding: 10px;
  background-color: #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-messages {
  flex-grow: 1;
  overflow-y: auto;
  padding: 10px;
}

.chat-input {
  padding: 10px;
  display: flex;
}

.message-container {
  display: flex;
  margin: 8px 0;
  gap: 8px;
}

.message-container.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.user .message-avatar {
  background-color: #1976d2;
  color: white;
}

.assistant .message-avatar {
  background-color: #4caf50;
  color: white;
}

.message-bubble {
  max-width: 70%;
  padding: 8px 12px;
  border-radius: 12px;
  background-color: #f5f5f5;
}

.user .message-bubble {
  background-color: #1976d2;
  color: white;
}

.assistant .message-bubble {
  background-color: #f5f5f5;
  color: #333;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.chat-window {
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.legend {
  line-height: 18px;
  color: #555;
}

.legend span {
  width: 16px;
  height: 16px;
  float: left;
  margin-right: 8px;
  border-radius: 50%;
  border: 1px solid #999;
}

.custom-marker {
  border-radius: 50%;
}

.custom-popup .leaflet-popup-content-wrapper {
  padding: 0;
  border-radius: 8px;
  box-shadow: 0 3px 14px rgba(0,0,0,0.2);
}

.custom-popup .leaflet-popup-content {
  margin: 0;
  width: auto !important;
}

.custom-popup .leaflet-popup-tip {
  box-shadow: 0 3px 14px rgba(0,0,0,0.2);
}

.search-pin {
  width: 30px;
  height: 30px;
  background-color: #4285f4;
  border: 2px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.custom-popup {
  padding: 8px;
  font-family: 'Noto Sans KR', sans-serif;
  background: white;
}

.location-title {
  font-weight: bold;
  margin-bottom: 8px;
}

.risk-label {
  font-size: 14px;
  color: #333;
}

.risk-value {
  color: #FFD700;
  font-weight: bold;
  text-shadow: 
    -1px -1px 0 #000,  /* 왼쪽 위 */
    1px -1px 0 #000,   /* 오른쪽 위 */
    -1px 1px 0 #000,   /* 왼쪽 아래 */
    1px 1px 0 #000;    /* 오른쪽 아래 */
}

.v-pagination .v-btn {
  background-color: white !important;
  color: rgba(0, 0, 0, 0.87) !important;
  border: 1px solid #e0e0e0;
  min-width: 70px !important;  /* 버튼 너비 조정 */
}

.v-pagination .v-btn--active {
  background-color: #1976d2 !important;
  color: white !important;
}

.title {
  font-weight: bold;
  margin-bottom: 4px;
}

.title:hover {
  color: #1976d2;
  text-decoration: underline;
}

.clickable-title {
  color: #1976d2;
  cursor: pointer;
}

.clickable-title:hover {
  text-decoration: underline;
}

/* 마크다운 스타일 추가 */
.message-bubble :deep(p) {
  margin: 0;
  line-height: 1.5;
}

.message-bubble :deep(code) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
}

.message-bubble :deep(pre) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
}

.message-bubble :deep(ul), 
.message-bubble :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-bubble :deep(li) {
  margin: 4px 0;
}

.message-bubble :deep(blockquote) {
  border-left: 4px solid #ccc;
  margin: 8px 0;
  padding-left: 16px;
  color: #666;
}

.message-bubble :deep(strong) {
  font-weight: 600;
  color: #2c3e50;
}

.message-bubble :deep(em) {
  font-style: italic;
  color: #34495e;
}
</style>






