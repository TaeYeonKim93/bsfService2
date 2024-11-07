from dotenv import load_dotenv
import streamlit as st
import datetime
import pandas as pd
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import openai
import os
import json


# Set page config for proper encoding (must be first Streamlit command)
st.set_page_config(page_title="사각지대 손전등 서비스 관리자 페이지",
                   page_icon="🔦",
                   layout="wide")


load_dotenv()
# OpenAI API 키 설정
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    st.error("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
    st.stop()  # API 키가 없으면 여기서 실행 중단
else:
    openai.api_key = OPENAI_API_KEY


app = FastAPI()
# 정적 파일 서빙
app.mount("/", StaticFiles(directory="data"), name="static")


# CSS styling with enhanced Korean font support
st.markdown("""
<style>
    /* Enhanced Korean font support with multiple weights */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
    
    * {
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Malgun Gothic', 
                     'Apple SD Gothic Neo', 'Segoe UI', sans-serif;
    }
    
    .stApp {
        background-color: #f0f2f6;
    }
    
    /* Header styles with enhanced weight */
    h1 {
        color: #1f1f1f;
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif;
        font-weight: 900;
    }
    
    h2, h3 {
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif;
        font-weight: 700;
    }
    
    /* Sidebar styles */
    section[data-testid="stSidebar"] {
        width: 15rem !important;
        background-color: rgb(63, 81, 181);
    }
    section[data-testid="stSidebar"] > div {
        width: 15rem !important;
    }
    
    /* Main content adjustments */
    .main .block-container {
        padding-left: calc(15rem + 2rem) !important;
    }
    
    /* Metric value with medium weight */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif;
        font-weight: 500;
    }
    
    /* Card styling */
    .card {
        background-color: white;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }
    
    .card-header {
        color: #ff4b4b;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 1rem;
        border-bottom: 1px solid #eee;
        padding-bottom: 0.5rem;
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif;
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }

    .stat {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f1f1f;
    }

    .sub-stat {
        font-size: 0.9rem;
        color: #666;
        font-weight: 300;
    }

    /* Additional text styles */
    p {
        font-weight: 400;
        line-height: 1.6;
    }

    /* Navigation menu items */
    .nav-item {
        font-weight: 500;
        color: white;
    }

    /* Table styles */
    .card .stDataFrame {
        width: 100%;
        margin-top: 0;
        padding: 0;
    }
    
    .card .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
    }
    
    .card .stDataFrame th {
        background-color: #f8f9fa;
        font-weight: 500;
        text-align: left;
        padding: 0.75rem;
    }
    
    .card .stDataFrame td {
        padding: 0.75rem;
        border-bottom: 1px solid #eee;
    }

    .stDataFrame {
        width: 100% !important;
        margin: 0 !important;
    }
    
    
    /* Card content wrapper */
    .card-content {
        padding: 1.5rem;
        width: 100%;
        position: relative;
    }

    /* 섹션 스타일링 */
    .section-container {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
        overflow: hidden;
    }
    
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1f1f1f;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .section-header::before {
        content: '';
        display: inline-block;
        width: 4px;
        height: 1.25rem;
        background: #FF4B4B;
        border-radius: 2px;
    }
    
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        transition: transform 0.2s;
    }
    
    .metric-container:hover {
        transform: translateY(-2px);
    }
    
    /* 차트 컨테이너 스타일링 */
    .chart-wrapper {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
    }

    .section-content {
        width: 100%;
        height: 100%;
        position: relative;
    }

    [data-testid="stDataFrame"] {
        background: transparent;
        padding: 0;
        margin: 0;
        box-shadow: none;
    }

    [data-testid="stDataFrame"] table {
        width: 100%;
        font-family: 'Noto Sans KR', sans-serif;
        border-collapse: collapse;
    }

    [data-testid="stDataFrame"] th {
        background-color: #f8f9fa;
        color: #1f1f1f;
        font-weight: 500;
        padding: 0.75rem !important;
        border-bottom: 2px solid #eee;
        position: sticky;
        top: 0;
        z-index: 1;
    }

    [data-testid="stDataFrame"] td {
        color: #4a4a4a;
        padding: 0.75rem !important;
        border-bottom: 1px solid #eee;
    }

    [data-testid="stDataFrame"] tr:has(td[style*="background-color: #e6f3ff"]) {
        background-color: #f8f9fa;
    }

    .recommended {
        background-color: #e6f3ff !important;
    }

    [data-testid="stDataFrame"] td:last-child:not(:empty) {
        background-color: #e6f3ff;
    }

    .ag-theme-streamlit .recommended-row {
        background-color: #e6f3ff !important;
    }

    /* 스크롤 동작 설정 */
    html {
        scroll-behavior: smooth;
    }
    
    /* 링크 호버 효과 */
    .nav-item a:hover {
        color: #e0e0e0 !important;
        text-decoration: underline !important;
    }

    /* 스크롤 시 섹션 헤더 여백 확보 */
    [id^="dpg-api"],
    [id^="collected-data"],
    [id^="risk-analysis"],
    [id^="ml-status"] {
        scroll-margin-top: 2rem;
        padding-top: 2rem;
    }
</style>
""",
            unsafe_allow_html=True)

# App header with updated Korean title
st.title("사각지대 손전등 서비스 관리자 페이지")
st.markdown(
    f"마지막 업데이트: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Sidebar with enhanced styling and correct Korean navigation
with st.sidebar:
    st.markdown('<h2 style="color: white; font-weight: 700;">메뉴</h2>',
                unsafe_allow_html=True)
    st.markdown('''
        <div class="nav-item">
        <a href="#dpg-api" style="color: white; text-decoration: none;">• API 목록 조회</a><br><br>
        <a href="#collected-data" style="color: white; text-decoration: none;">• 데이터 현황</a><br><br>
        <a href="#risk-analysis" style="color: white; text-decoration: none;">• 복지 위험도 분석</a><br><br>
        <a href="#ml-status" style="color: white; text-decoration: none;">• 머신러닝 현황</a><br><br>
        <a href="network3_white_leg.html" target="_blank" style="color: white; text-decoration: none;">• 네트워크 자원 연관도</a>
        </div>
    ''',
                unsafe_allow_html=True)

# DPG API 목록 섹션
st.markdown('<div id="dpg-api" style="padding-top: 2rem;"></div>', unsafe_allow_html=True)
dpg_container = st.container()
with dpg_container:
    st.markdown('<div class="section-header">DPG API 목록</div>', unsafe_allow_html=True)
    
    try:
        # DPG API 목록 데이터 로드
        dpg_api_data = pd.read_csv('/app/data/DPG_API_list.csv', encoding='euc-kr')
        
        # 선택 사유 데이터 로드
        reasons_data = pd.read_csv('/app/data/ml/Customized_Selection_Reasons_for_Social_Security_APIs.csv', encoding='utf-8')
        
        # api_title 기준으로 데이터프레임 병합
        merged_data = pd.merge(
            dpg_api_data,
            reasons_data[['api_title', '활용가능 속성 목록','선택한 이유']],
            left_on='title',
            right_on='api_title',
            how='left'
        )
        
        # AI 추천이 있는 행을 맨 위로 정렬
        merged_data['has_reason'] = ~merged_data['선택한 이유'].isna()
        merged_data = merged_data.sort_values('has_reason', ascending=False)
        
        # 정렬 후 순번 부여
        merged_data = merged_data.reset_index(drop=True)  # drop=True로 이전 인스 제
        merged_data['순번'] = merged_data.index + 1
        
        # Grid 옵션 설정
        gb = GridOptionsBuilder.from_dataframe(merged_data[['순번', 'title', '선택한 이유','summary', 'description' ]])
        
        gb.configure_column('순번', header_name="No.", width=30)
        gb.configure_column('선택한 이유', header_name="AI 추천 사유", width=200)
        gb.configure_column('활용가능 속성 목록', header_name="AI추천 속성", width=200)
        gb.configure_column('title', header_name="제목", width=50)
        gb.configure_column('summary', header_name="요약", width=200)
        gb.configure_column('description', header_name="설명", width=200)
        
        # 툴팁 커스터마이징 옵션 추가
        gb.configure_grid_options(
            tooltipShowDelay=0,
            tooltipHideDelay=2000,
            rowClassRules={
                'recommended-row': 'data.선택한 이유 != null'
            }
        )
        
        grid_options = gb.build()
        
        # AgGrid 표시
        AgGrid(
            merged_data,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            theme='streamlit'
        )
    except Exception as e:
        st.error(f"DPG API 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")
    

# 수집된 데이터와 지도 섹션을 나란히 배치
st.markdown('<div id="collected-data" style="padding-top: 2rem;"></div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    # 수집된 데이터 섹션
    st.markdown('<div class="section-header">데이터 현황</div>', unsafe_allow_html=True)
    
    try:
        # CSV 파일에서 데이터 로드
        reasons_data = pd.read_csv('/app/data/ml/Customized_Selection_Reasons_for_Social_Security_APIs.csv', encoding='utf-8')
        dpg_api_data = pd.read_csv('/app/data/DPG_API_list.csv', encoding='euc-kr')
        
        # 통계 계산
        total_apis = len(dpg_api_data)  # 전체 API 수
        today_apis = len(reasons_data[reasons_data['updated_at'].dt.date == datetime.date.today()]) if 'updated_at' in reasons_data.columns else 0  # 오늘 수집된 데이터
        ai_recommended = len(reasons_data[reasons_data['선택한 이유'].notna()])  # AI 추천이 있는 데이터
        usable_apis = 3
        
        cols = st.columns(4)
        with cols[0]:
            st.metric(label="전체 데이터", value=f"{total_apis:,}", 
                     delta=f"{today_apis}")
        
        with cols[1]:
            st.metric(label="오늘 수집", value=f"{today_apis:,}", 
                     delta=None)
        
        with cols[2]:
            st.metric(label="AI 추천 데이터", value=f"{ai_recommended:,}", 
                     delta=None)
        
        with cols[3]:
            st.metric(label="활용 가능 데이터", value=f"{usable_apis:,}", 
                     delta=None)
    
    except Exception as e:
        st.error(f"데이터 통계를 계산하는 중 오류가 발생했습니다: {str(e)}")

with col2:
    # 위험지도 섹션
    st.markdown('<div class="section-header">위험 지도</div>', unsafe_allow_html=True)
    st.components.v1.iframe(
        src="/map/mini",
        height=300,
        scrolling=False
    )

# OpenAI Assistant ID 설정
ASSISTANT_ID = 'asst_HO7yQOK6MEU1lm7PyJ7Kv1TO'
client = openai.OpenAI()

try:
    assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
    print('Assistant retrieved:', assistant.id)
except Exception as e:
    st.error(f"Assistant 초기화 실패: {str(e)}")
    st.stop()

# DPG API 연동내역 섹션
st.markdown('<div id="risk-analysis" style="padding-top: 2rem;"></div>', unsafe_allow_html=True)
api_status_container = st.container()
with api_status_container:
    st.markdown('<div class="section-header">복지 위험도 분석</div>', unsafe_allow_html=True)
    
    try:
        # 경로와 인코딩 수정
        risk_data = pd.read_csv('./data/Find_sigungu_with_sido_sigungu.csv', encoding='euc-kr')
        
        # 위험도 기준으로 정렬
        risk_data = risk_data.sort_values('Result', ascending=False)
        
        # 상위 5개, 하위 5개 지역 추출
        top_5 = risk_data.head(5)
        bottom_5 = risk_data.tail(5)
        
        # 두 개의 열로 나누어 표시
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div style="background-color: #fff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h4 style="color: #ff4b4b; margin-bottom: 10px;">위험도 상위 5개 지역</h4>
                </div>
            """, unsafe_allow_html=True)
            
            # 상위 5개 지역을 선택 가능한 버튼으로 표시
            for _, row in top_5.iterrows():
                # 상대적 위험도 퍼센트 계산
                risk_percent = row['Result'] * 100
                if st.button(f"🔴 {row['Sido']} {row['Sigungu']} - 위험도: {risk_percent:.1f}%", 
                           key=f"top_{row['Sigungu']}",
                           help="클릭하여 상세 분석 보기"):
                    # 버튼 클릭 시에만 실행되는 코드
                    region_data = row.to_dict()
                    
                    # Thread 생성
                    thread = client.beta.threads.create()
                    
                    # 메시지 작성
                    message_content = f"""
                    지역: {region_data['Sido']} {region_data['Sigungu']}
                    위험도 점수: {region_data['Result']:.3f}
                    위치: 위도 {region_data['Latitude']}, 경도 {region_data['Longitude']}
                    
                    이 지역의 복지 위험도를 분석하고, 구체적인 개선 방안을 제시해주세요.
                    """
                    
                    # 메시지 전송 및 응답 처리
                    with st.spinner('AI가 분석 중입니다...'):
                        # Thread 생성
                        thread = client.beta.threads.create()
                        
                        # 메시지 전송
                        message = client.beta.threads.messages.create(
                            thread_id=thread.id,
                            role="user",
                            content=message_content
                        )
                        
                        # 실행
                        run = client.beta.threads.runs.create(
                            thread_id=thread.id,
                            assistant_id=ASSISTANT_ID
                        )
                        
                        # 결과 대기
                        while True:
                            run = client.beta.threads.runs.retrieve(
                                thread_id=thread.id,
                                run_id=run.id
                            )
                            if run.status == 'completed':
                                break
                        
                        # 응답 받기
                        messages = client.beta.threads.messages.list(thread_id=thread.id)
                        analysis = messages.data[0].content[0].text.value
                        
                        # 분석 결과 표시
                        st.markdown(f"""
                        <div style="background-color: #fff; padding: 20px; border-radius: 10px; margin-top: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <h4 style="color: #1f1f1f; margin-bottom: 15px;">AI 분석 결과</h4>
                            {analysis}
                        </div>
                        """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div style="background-color: #fff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h4 style="color: #2e7d32; margin-bottom: 10px;">위험도 하위 5개 지역</h4>
                </div>
            """, unsafe_allow_html=True)
            
            # 하위 5개 지역을 선택 가능한 버튼으로 표시
            for _, row in bottom_5.iterrows():
                # 상대적 위험도 퍼센트 계산
                risk_percent = (row['Result'] / max_risk) * 100
                if st.button(f"🟢 {row['Sido']} {row['Sigungu']} - 위험도: {risk_percent:.1f}%", 
                           key=f"bottom_{row['Sigungu']}",
                           help="클릭하여 상세 분석 보기"):
                    # 버튼 클릭 시에만 실행되는 코드
                    region_data = row.to_dict()
                    
                    # Thread 생성 및 AI 분석 (상위 5개 지역과 동일한 코드)
                    thread = client.beta.threads.create()
                    
                    # 메시지 작성
                    message_content = f"""
                    지역: {region_data['Sido']} {region_data['Sigungu']}
                    위험도 점수: {region_data['Result']:.3f}
                    위치: 위도 {region_data['Latitude']}, 경도 {region_data['Longitude']}
                    
                    이 지역의 복지 위험도를 분석하고, 구체적인 개선 방안을 제시해주세요.
                    """
                    
                    # 메시지 전송 및 응답 처리
                    with st.spinner('AI가 분석 중입니다...'):
                        # Thread 생성
                        thread = client.beta.threads.create()
                        
                        # 메시지 전송
                        message = client.beta.threads.messages.create(
                            thread_id=thread.id,
                            role="user",
                            content=message_content
                        )
                        
                        # 실행
                        run = client.beta.threads.runs.create(
                            thread_id=thread.id,
                            assistant_id=ASSISTANT_ID
                        )
                        
                        # 결과 대기
                        while True:
                            run = client.beta.threads.runs.retrieve(
                                thread_id=thread.id,
                                run_id=run.id
                            )
                            if run.status == 'completed':
                                break
                        
                        # 응답 받기
                        messages = client.beta.threads.messages.list(thread_id=thread.id)
                        analysis = messages.data[0].content[0].text.value
                        
                        # 분석 결과 표시
                        st.markdown(f"""
                        <div style="background-color: #fff; padding: 20px; border-radius: 10px; margin-top: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <h4 style="color: #1f1f1f; margin-bottom: 15px;">AI 분석 결과</h4>
                            {analysis}
                        </div>
                        """, unsafe_allow_html=True)
        

        # AI 분석 결과 표시 영역
        if 'selected_region' in st.session_state:
            region_parts = st.session_state.selected_region.split()
            
            if region_data:
                # Thread 생성
                thread = client.beta.threads.create()
                
                # 메시지 작성
                message_content = f"""
                지역: {region_data['sido']} {region_data['sigungu']}
                위험도 점수: {region_data['risk_score']:.3f}
                치: 위도 {region_data['latitude']}, 경도 {region_data['longitude']}
                
                이 지역의 복지 위험도를 분석하고, 구체적인 개선 방안을 제시해주세요.
                """
                
                # 메시지 전송
                message = client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=message_content
                )
                
                # 실행
                run = client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=ASSISTANT_ID  # 고정된 Assistant ID 사용
                )
                
                # 결과 대기 및 표시
                with st.spinner('AI가 분석 중입니다...'):
                    while True:
                        run = client.beta.threads.runs.retrieve(
                            thread_id=thread.id,
                            run_id=run.id
                        )
                        if run.status == 'completed':
                            break
                    
                    # 응답 받기
                    messages = client.beta.threads.messages.list(thread_id=thread.id)
                    analysis = messages.data[0].content[0].text.value
                    
                    # 분석 결과 표시
                    st.markdown(f"""
                    <div style="background-color: #fff; padding: 20px; border-radius: 10px; margin-top: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h4 style="color: #1f1f1f; margin-bottom: 15px;">AI 분석 결과</h4>
                        {analysis}
                    </div>
                    """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"위험도 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}")

# 머신러닝 현황 섹션
st.markdown('<div id="ml-status" style="padding-top: 2rem;"></div>', unsafe_allow_html=True)
ml_status_container = st.container()
with ml_status_container:
    st.markdown('<div class="section-header">머신러닝 현황</div>', unsafe_allow_html=True)
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["모델 목록", "모델 성능",  "모델 다운로드"])
    
    with tab1:
        try:
            # JSON 파일에서 모델 정보 로드
            with open('/app/data/ml/model_info.json', 'r', encoding='utf-8') as f:
                model_info = json.load(f)
            model_info_df = pd.DataFrame(model_info['models'])
            
            # Grid 옵션 설정
            gb = GridOptionsBuilder.from_dataframe(model_info_df)
            
            # 컬�� 설정
            gb.configure_column('모델명', header_name="모델명", width=200)
            gb.configure_column('파일명', header_name="파일명", width=200)
            gb.configure_column('용도', header_name="용도", width=300)
            gb.configure_column('학습 데이터', header_name="학습 데이터", width=200)
            
            # 그리드 전체 설정
            gb.configure_grid_options(
                domLayout='normal',
                enableCellTextSelection=True,
                suppressDragLeaveHidesColumns=True,
                suppressRowHoverHighlight=False,
                rowHeight=35,
                headerHeight=35
            )
            
            grid_options = gb.build()
            
            # AgGrid 표시
            AgGrid(
                model_info_df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                allow_unsafe_jscode=True,
                theme='streamlit',
                height=400
            )

        except Exception as e:
            st.error(f"모델 정보를 불러오는 중 오류가 발생했습니다: {str(e)}")
    
    with tab2:
        st.markdown('<div class="section-header">모델 성능 지표</div>', unsafe_allow_html=True)
        
        try:
            image_dir = '/app/data/ml/img'
            
            title_mapping = {
                'f1': '실제가격 vs 예측가격 산포도',
                'f2': '예측 오차 분포도'
            }
            
            image_files = [f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
            
            # 모델별로 이미지 그룹화
            model_images = {}
            for img in image_files:
                parts = img.split('_')
                if len(parts) >= 4:
                    model_name = '_'.join(parts[:-1])
                    metric_type = parts[-1].split('.')[0]
                    
                    if model_name not in model_images:
                        model_images[model_name] = {}
                    model_images[model_name][metric_type] = img

            # 5개의 컬럼 생성
            cols = st.columns(5)
            
            # 모델을 5개씩 그룹화하여 표시
            for idx, (model_name, metrics) in enumerate(model_images.items()):
                col_idx = idx % 5
                
                with cols[col_idx]:
                    st.markdown(f"""
                        <div style="background-color: white; padding: 0.5rem; border-radius: 8px; 
                                box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 0.5rem;">
                            <h3 style="color: #1f1f1f; font-size: 0.8rem; margin-bottom: 0.5rem; text-align: center;">
                                {model_name.replace('_', ' ').upper()}
                            </h3>
                    """, unsafe_allow_html=True)
                    
                    if 'f1' in metrics:
                        st.markdown(f"""
                            <p style="color: #666; font-size: 0.7rem; margin-bottom: 0.3rem; text-align: center;">
                                {title_mapping['f1']}
                            </p>
                        """, unsafe_allow_html=True)
                        st.image(f"{image_dir}/{metrics['f1']}", use_column_width=True)
                    
                    if 'f2' in metrics:
                        st.markdown(f"""
                            <p style="color: #666; font-size: 0.7rem; margin-bottom: 0.3rem; text-align: center;">
                                {title_mapping['f2']}
                            </p>
                        """, unsafe_allow_html=True)
                        st.image(f"{image_dir}/{metrics['f2']}", use_column_width=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # 5개 모델마다 새로운 줄 시작
                if col_idx == 4:
                    st.markdown("<br>", unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"모델 성능 이미지를 불러오는 중 오류가 발생했습니다: {str(e)}")
    
    with tab3:
        st.markdown("### 모델 파일 다운로드")
        
        try:
            model_dir = './data/ml/model_file'
            model_files = [f for f in os.listdir(model_dir) if f.endswith('.pkl')]
            
            # 3개의 컬럼으로 나누어 표시
            cols = st.columns(3)
            
            for idx, model_file in enumerate(model_files):
                col_idx = idx % 3  # 3개 컬럼을 순환하면서 배치 
                
                with cols[col_idx]:
                    file_path = os.path.join(model_dir, model_file)
                    file_size = f"{os.path.getsize(file_path) / 1024:.1f} KB"
                    
                    with open(file_path, 'rb') as f:
                        st.download_button(
                            label=f"📥 {model_file}",
                            data=f.read(),
                            file_name=model_file,
                            mime='application/octet-stream',
                            help=f"크기: {file_size}"
                        )
                
        except Exception as e:
            st.error(f"모델 파일 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")
