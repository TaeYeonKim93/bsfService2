<template>
  <div class="risk-analysis-page">
    <v-container>
      <v-row justify="center">
        <v-col cols="12" md="8">
          <v-card class="mt-5">
            <v-card-title class="text-center">
              위험도 분석
            </v-card-title>
            <v-card-text>
              <div v-if="loading" class="text-center">
                <v-progress-circular indeterminate></v-progress-circular>
              </div>
              <div v-else-if="error" class="error-message">
                {{ error }}
              </div>
              <div v-else-if="imageData" class="image-container">
                <img :src="`data:image/png;base64,${imageData}`" alt="위험도 분석 그래프" />
              </div>
              <div v-else class="text-center">
                <v-btn
                  color="primary"
                  @click="handleAnalysisClick"
                >
                  분석 시작
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';

export default defineComponent({
  name: 'RiskAnalysis',
  setup() {
    const loading = ref(false);
    const error = ref('');
    const imageData = ref('');
    const title = ref('');

    const handleAnalysisClick = async () => {
      loading.value = true;
      error.value = '';
      imageData.value = '';

      try {
        const response = await fetch('/xai/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
          credentials: 'include',
          body: JSON.stringify({
            sido: '경상남도',
            sigungu: '고성군'
          })
        });

        const data = await response.json();
        if (data.success) {
          imageData.value = data.image;
          title.value = `${data.sido} ${data.sigungu} 위험도 분석 결과`;
        } else {
          error.value = data.message || '분석 중 오류가 발생했습니다.';
        }
      } catch (err) {
        error.value = '서버 연결에 실패했습니다.';
        console.error('분석 요청 중 오류:', err);
      } finally {
        loading.value = false;
      }
    };

    return {
      loading,
      error,
      imageData,
      title,
      handleAnalysisClick
    };
  }
});
</script>

<style scoped>
.risk-analysis-page {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 20px;
}

.image-container {
  width: 100%;
  text-align: center;
}

.image-container img {
  max-width: 100%;
  height: auto;
}

.error-message {
  color: red;
  text-align: center;
  padding: 20px;
}
</style>
