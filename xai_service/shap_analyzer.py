import pandas as pd
import numpy as np
import joblib
import xgboost
import shap
import json
import os
from sklearn.preprocessing import StandardScaler

class ShapAnalyzer:
    def __init__(self):
        # 파일 경로 설정
        self.csv_file_path = 'data/아파트_학습데이터_월세.csv'
        self.xgb_model_file_path = 'data/xgboost_model_apt_m.pkl'
        self.output_dir = 'data/shap_results'
        
        # 특성 이름 매핑
        self.feature_name_map = {
            'x1': '총 주택 수', 'x2': '다세대 주택 수', 'x3': '단독 주택 수', 'x4': '아파트 수',
            'x5': '연립주택 수', 'x6': '영업용건물내주택 수', 'x7': '주택이외거처 수', 'x8': '면적20이하',
            'a1': '계약면적', 'a2': '보증금', 'a3': '월세금'
        }
        
        # 초기화
        self._load_data_and_model()
        
    def _load_data_and_model(self):
        """데이터와 모델을 로드하고 전처리합니다."""
        # 데이터 로드 및 전처리
        self.df = pd.read_csv(self.csv_file_path, encoding='cp949')
        self.df_cleaned = self.df.replace([float('inf'), float('-inf')], float('nan')).dropna()
        
        # StandardScaler 적용
        self.scaler = StandardScaler()
        self.scaler.fit(self.df_cleaned.filter(regex='^[xa]'))
        
        # 모델 로드
        self.xgb_model = joblib.load(self.xgb_model_file_path)
        if hasattr(self.xgb_model, 'save_model'):
            temp_model_path = 'temp_model.json'
            self.xgb_model.save_model(temp_model_path)
            self.xgb_model = xgboost.XGBRegressor()
            self.xgb_model.load_model(temp_model_path)
            os.remove(temp_model_path)
        
        self.explainer = shap.Explainer(self.xgb_model)
        
    def analyze_and_save(self):
        """전체 데이터에 대한 SHAP 값을 분석하고 JSON 파일로 저장합니다."""
        # 출력 디렉토리 생성
        os.makedirs(self.output_dir, exist_ok=True)
        
        results = []
        
        # 전체 데이터에 대해 반복
        for idx, row in self.df_cleaned.iterrows():
            print(f"분석 중: {idx+1}/{len(self.df_cleaned)}")
            
            # 데이터 전처리
            X = self.scaler.transform(row.filter(regex='^[xa]').values.reshape(1, -1))
            
            # SHAP 값 계산
            shap_values = self.explainer(X)
            
            # 특성 이름을 한글로 변환
            feature_names = [self.feature_name_map.get(name, name) 
                           for name in self.df_cleaned.filter(regex='^[xa]').columns]
            
            # 결과 저장
            row_result = {
                'sido': row['sido'],
                'sigungu': row['sigungu'],
                '복지위험도 요인': feature_names,
                '복지위험도 요인 shap values': shap_values.values.tolist(),
                'base_values': shap_values.base_values.tolist(),
                'data': X.tolist()
            }
            
            results.append(row_result)
        
        # 전체 결과를 하나의 파일로 저장
        all_results_path = os.path.join(self.output_dir, 'all_shap_values.json')
        with open(all_results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"분석 완료. 결과가 {self.output_dir}/all_shap_values.json 에 저장되었습니다.")

if __name__ == "__main__":
    analyzer = ShapAnalyzer()
    analyzer.analyze_and_save()