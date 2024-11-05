# flask_server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import matplotlib.pyplot as plt
import shap
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import io
import base64
import matplotlib
import matplotlib.font_manager as fm
import xgboost
import os

app = Flask(__name__)
CORS(app, resources={
    r"/analyze": {
        "origins": ["https://localhost", "http://localhost:5173"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"]
    }
})

# 모델과 데이터 로드
csv_file_path = 'data/아파트_학습데이터_월세.csv'
xgb_model_file_path = 'data/xgboost_model_apt_m.pkl'

try:
    # 데이터 로드 및 전처리
    df = pd.read_csv(csv_file_path, encoding='cp949')
    df_cleaned = df.replace([float('inf'), float('-inf')], float('nan')).dropna()
    
    # StandardScaler 적용
    scaler = StandardScaler()
    scaler.fit(df_cleaned.filter(regex='^[xa]'))
    
    # 모델 로드 - 새로운 방식으로 저장된 모델 사용
    xgb_model = joblib.load(xgb_model_file_path)
    if hasattr(xgb_model, 'save_model'):
        temp_model_path = 'temp_model.json'
        xgb_model.save_model(temp_model_path)
        xgb_model = xgboost.XGBRegressor()
        xgb_model.load_model(temp_model_path)
        os.remove(temp_model_path)
    
    explainer_xgb = shap.Explainer(xgb_model)
    print("모델과 데이터 로드 완료")
except Exception as e:
    print(f"초기화 중 오류 발생: {str(e)}")
    raise

# matplotlib 설정
import matplotlib
matplotlib.use('Agg')

# 한글 폰트 설정 (시스템에 설치된 한글 폰트 찾기)
import matplotlib.font_manager as fm

# 사용 가능한 폰트 목록 출력 (디버깅용)
print("Available fonts:")
for font in fm.fontManager.ttflist:
    print(font.name)

# 한글 폰트 설정 시도
plt.rcParams['axes.unicode_minus'] = False
for font in fm.fontManager.ttflist:
    if any(name in font.name.lower() for name in ['nanum', 'malgun', 'gulim']):
        plt.rcParams['font.family'] = font.name
        print(f"Using font: {font.name}")
        break

# 기본 그래프 설정
plt.rcParams.update({
    'figure.figsize': [12, 8],
    'figure.dpi': 100,
    'axes.grid': True,
    'grid.linestyle': '--',
    'grid.alpha': 0.5
})

# 변수 이름을 한글로 매핑
feature_name_map = {
    'x1': '총 주택 수', 'x2': '다세대 주택 수', 'x3': '단독 주택 수', 'x4': '아파트 수',
    'x5': '연립주택 수', 'x6': '영업용건물내주택 수', 'x7': '주택이외거처 수', 'x8': '면적20이하',
    'a1': '계약면적', 'a2': '보증금', 'a3': '월세금'
}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    if request.method == 'OPTIONS':
        return '', 204
    try:
        data = request.get_json()
        target_sido = data.get('sido')
        target_sigungu = data.get('sigungu')

        # 데이터 필터링
        target_sample = df_cleaned[
            (df_cleaned['sido'] == target_sido) & 
            (df_cleaned['sigungu'] == target_sigungu)
        ]

        if target_sample.empty:
            return jsonify({
                "success": False, 
                "message": "해당 지역의 데이터를 찾을 수 없습니다."
            }), 404

        # 데이터 전처리
        target_X = scaler.transform(target_sample.filter(regex='^[xa]'))
        shap_values_xgb_sample = explainer_xgb(target_X)

        # SHAP 값 설명 객체 생성
        feature_names_korean = [
            feature_name_map.get(name, name) 
            for name in target_sample.filter(regex='^[xa]').columns
        ]
        
        shap_values_xgb_sample = shap.Explanation(
            values=shap_values_xgb_sample.values,
            base_values=shap_values_xgb_sample.base_values,
            data=target_X,
            feature_names=feature_names_korean
        )

        # 그래프 생성
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.grid(axis='x', linestyle='--', linewidth=0.5, zorder=1)
        ax.grid(axis='y', linestyle='--', linewidth=0.5, zorder=1)
        
        shap_values = shap_values_xgb_sample[0].values
        feature_names = [feature_name_map.get(name, name) 
                        for name in target_sample.filter(regex='^[xa]').columns]
        colors = ['blue' if value > 0 else 'red' for value in shap_values]
        
        ax.barh(range(len(feature_names)), shap_values, color=colors, zorder=2)
        ax.set_yticks(range(len(feature_names)))
        ax.set_yticklabels(feature_names)  # 한글 이름 사용
        ax.set_xlabel("가중치")
        ax.set_title(f"{target_sido} {target_sigungu}의 변수 영향도")
        
        plt.tight_layout()

        # 이미지 저장
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        plt.close()
        buf.seek(0)
        
        # 인코딩 과정 확인
        binary_data = buf.read()
        print(f"Binary data length: {len(binary_data)}")
        
        base64_data = base64.b64encode(binary_data)
        print(f"Base64 data length: {len(base64_data)}")
        
        image_base64 = base64_data.decode('UTF-8')
        print(f"Final string length: {len(image_base64)}")
        
        return jsonify({
            "success": True, 
            "image": image_base64,
            "sido": target_sido,
            "sigungu": target_sigungu
        })

    except Exception as e:
        print(f"Error in analyze: {str(e)}")  # 디버깅을 위한 에러 출력 추가
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
