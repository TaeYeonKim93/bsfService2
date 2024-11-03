import streamlit as st
import datetime
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Set page config for proper encoding (must be first Streamlit command)
st.set_page_config(page_title="사각지대 손전등 서비스 관리자 페이지",
                   page_icon="🔦",
                   layout="wide")

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
</style>
""",
            unsafe_allow_html=True)

# App header with updated Korean title
st.title("사각지대 손전등 서비스 관리자 페이지")
st.markdown(
    f"마지막 업데이트: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Sidebar with enhanced styling and correct Korean navigation
with st.sidebar:
    st.markdown('<h2 style="color: white; font-weight: 700;">현황</h2>',
                unsafe_allow_html=True)
    st.markdown('''
        <div class="nav-item">
        • DPG API 목록<br><br>
        • 수집된 데이터<br><br>
        • DPG API 연동 내역<br><br>
        • 머신러닝 현황
        </div>
    ''',
                unsafe_allow_html=True)

# DPG API 목록 섹션
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
            reasons_data[['api_title', '선택한 이유']],
            left_on='title',
            right_on='api_title',
            how='left'
        )
        
        # AI 추천이 있는 행을 맨 위로 정렬
        merged_data['has_reason'] = ~merged_data['선택한 이유'].isna()
        merged_data = merged_data.sort_values('has_reason', ascending=False)
        
        # 정렬 후 순번 부여
        merged_data = merged_data.reset_index(drop=True)  # drop=True로 이전 인덱스 제거
        merged_data['순번'] = merged_data.index + 1
        
        # Grid 옵션 설정
        gb = GridOptionsBuilder.from_dataframe(merged_data[['순번', 'title', '선택한 이유','summary', 'description' ]])
        
        gb.configure_column('순번', header_name="No.", width=30)
        gb.configure_column('선택한 이유', header_name="AI 추천", width=200)
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
    

# 수집된 데이터 섹션
collected_data_container = st.container()
with collected_data_container:
    st.markdown('<div class="section-header">수집된 데이터</div>', unsafe_allow_html=True)
    
    cols = st.columns(4)
    with cols[0]:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label="전체 데이터", value="25,430", delta="1,200")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label="오늘 수집", value="1,234", delta="234")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label="유효 데이터", value="23,456", delta="1,100")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label="중복 제거", value="1,974", delta="-100")
        st.markdown('</div>', unsafe_allow_html=True)
    
# DPG API 연동내역 섹션
api_status_container = st.container()
with api_status_container:
    st.markdown('<div class="section-header">DPG API 연동내역</div>', unsafe_allow_html=True)
    
    # API 연동 상태 표시
    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
    st.progress(95, text="API 연동 상태: 95%")
    
    cols = st.columns(3)
    with cols[0]:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label=" API 수", value="50", delta="5")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label="활성 API", value="48", delta="3")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label="오류 API", value="2", delta="-2")
        st.markdown('</div>', unsafe_allow_html=True)
    
