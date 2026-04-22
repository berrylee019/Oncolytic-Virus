import streamlit as st
import requests
import pandas as pd

# 1. API 호출 함수
def fetch_clinical_trials(keyword="Oncolytic Virus", limit=10):
    # API V2 Endpoint
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    
    # 파라미터 설정 (항암 바이러스 키워드 및 필터)
    params = {
        "query.term": keyword,
        "pageSize": limit,
        "fields": "NCTId,BriefTitle,OverallStatus,Condition,LeadSponsorName",
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        studies = data.get('studies', [])
        
        # 데이터 파싱
        rows = []
        for study in studies:
            info = study.get('protocolSection', {})
            id_module = info.get('identificationModule', {})
            status_module = info.get('statusModule', {})
            design_module = info.get('designModule', {}) # 추가 정보용
            
            rows.append({
                "NCT ID": id_module.get('nctId'),
                "Title": id_module.get('briefTitle'),
                "Status": status_module.get('overallStatus'),
                "Sponsor": id_module.get('leadSponsorName', 'N/A')
            })
        return pd.DataFrame(rows)
    else:
        st.error(f"API 호출 실패: {response.status_code}")
        return pd.DataFrame()

# 2. Streamlit UI 구성
st.set_page_config(page_title="Global Oncolytic Virus Trial Hub", layout="wide")

st.title("🔬 글로벌 항암 바이러스 임상 실시간 허브")
st.markdown("ClinicalTrials.gov API V2를 활용한 실시간 데이터 파이프라인 테스트")

# 검색 인터페이스
with st.sidebar:
    st.header("설정")
    search_term = st.text_input("검색어", value="Oncolytic Virus")
    max_results = st.slider("가져올 결과 수", 5, 50, 10)
    run_btn = st.button("데이터 동기화")

if run_btn:
    with st.spinner('최신 임상 데이터를 가져오는 중...'):
        df = fetch_clinical_trials(search_term, max_results)
        
        if not df.empty:
            st.success(f"{len(df)}개의 최신 임상 정보를 찾았습니다.")
            
            # 결과 테이블
            st.dataframe(df, use_container_width=True)
            
            # 개별 상세 정보 보기 (비즈니스 확장용)
            st.subheader("상세 분석 데이터")
            selected_id = st.selectbox("상세 내용을 확인하려는 NCT ID를 선택하세요", df['NCT ID'])
            
            # 선택한 임상의 상세 데이터 시각화 또는 AI 요약 등을 여기에 추가 가능
            st.info(f"선택된 ID: {selected_id} - 이 정보를 기반으로 AI가 자동 포스팅용 초안을 작성하게 할 수 있습니다.")
        else:
            st.warning("결과가 없습니다.")
