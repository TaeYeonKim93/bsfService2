import streamlit as st
import datetime
import pandas as pd

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
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(0, 0, 0, 0.1);
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
        padding: 0.5rem 0;
        width: 100%;
        position: relative;
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

# Create a container for the DPG API list card
dpg_container = st.container()

with dpg_container:
    st.markdown('''
        <div>
            <div class="card-header">DPG API 목록</div>
    ''',
                unsafe_allow_html=True)

    col1 = st.container()
    with col1:
        try:
            dpg_api_data = pd.read_csv('/app/data/DPG_API_list.csv', encoding='euc-kr')
            # orgId와 version 열만 선택
            selected_columns = dpg_api_data[[
                'orgId', 'title', 'summary', 'description'
            ]]

            # 컬럼 설정
            st.dataframe(
                selected_columns,
                column_config={
                    "orgId":
                    st.column_config.Column(width='small'),  # orgId 열 너비 100px
                    "description": st.column_config.Column(
                        width='medium')  # version 열 너비 100px
                },
                use_container_width=True,
                height=400)
        except UnicodeDecodeError:
            try:
                dpg_api_data = pd.read_csv('/app/data/DPG_API_list.csv',
                                           encoding='cp949')
                # orgId와 version 열만 선택
                selected_columns = dpg_api_data[['orgId', 'version']]
                st.dataframe(selected_columns,
                             use_container_width=True,
                             height=400)
            except Exception as e:
                st.error(f"Error loading DPG API list: {str(e)}")

    st.markdown('''
            </div>
        </div>
    ''',
                unsafe_allow_html=True)

# Main content with updated Korean headers and labels
st.markdown('''
    <div class="card">
        <div class="card-header">수집된 데이터</div>
        <div class="stats-grid">
            <div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">DPG API 연동내역</div>
        <div class="stats-grid">
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">머신러닝 현황</div>
        <div class="stats-grid">
            <div>
            </div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">임시</div>
        <div class="stats-grid">
            <div>
                <div>차트 영역</div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">지도</div>
        <div class="stats-grid">
            <div>
                <div>지도 영역</div>
            </div>
        </div>
    </div>
''',
            unsafe_allow_html=True)
