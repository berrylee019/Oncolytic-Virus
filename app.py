import streamlit as st
import requests
import pandas as pd
from openai import OpenAI

# 1. OpenAI 클라이언트 설정 (Secrets에서 키 호출)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def fetch_clinical_trials(keyword="Oncolytic Virus", limit=5):
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": keyword,
        "pageSize": limit,
        # 'BriefSummary' 필드를 추가해서 요약 내용을 가져옵니다.
        "fields": "NCTId,BriefTitle,OverallStatus,LeadSponsorName,BriefSummary",
    }
    
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        studies = data.get('studies', [])
        rows = []
        for study in studies:
            info = study.get('protocolSection', {})
            id_module = info.get('identificationModule', {})
            status_module = info.get('statusModule', {})
            desc_module = info.get('descriptionModule', {})
            
            rows.append({
                "NCT ID": id_module.get('nctId'),
                "Title": id_module.get('briefTitle'),
                "Status": status_module.get('overallStatus'),
                "Sponsor": id_module.get('leadSponsorName', 'N/A'),
                "Summary": desc_module.get('briefSummary', '요약 없음') # AI가 읽을 원문
            })
        return pd.DataFrame(rows)
    return pd.DataFrame()

# 2. AI 블로그 초안 생성 함수
def generate_blog_post(data_df):
    # AI에게 줄 컨텍스트 구성
    context = ""
    for i, row in data_df.iterrows():
        context += f"[{i+1}] 제목: {row['Title']}\n스폰서: {row['Sponsor']}\n요약: {row['Summary']}\n\n"

    prompt = f"""
    당신은 전문 의학 블로거입니다. 아래의 최신 항암 바이러스 임상 데이터 {len(data_df)}건을 바탕으로 
    환자와 보호자들에게 희망을 주는 '네이버 블로그/티스토리' 스타일의 포스팅 초안을 작성하세요.

    [작성 가이드]
    1. 제목: 클릭을 부르는 매력적인 한글 제목 (예: "2026년 항암 바이러스 치료, 어디까지 왔나?")
    2. 서론: 항암 바이러스 치료의 중요성과 최신 트렌드 언급
    3. 본문: 제공된 데이터를 묶어서 알기 쉽게 설명 (전문 용어는 쉬운 우리말로 풀어서 설명)
    4. 결론: 임상 참여 방법(clinicaltrials.gov 활용법)과 응원의 메시지
    5. 말투: 친절하고 신뢰감 있는 '해요체' 사용
    6. 검색 최적화(SEO)를 위해 주요 키워드(항암바이러스, 임상시험, 면역항암제)를 자연스럽게 포함하세요.

    [데이터]
    {context}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- Streamlit UI ---
st.set_page_config(page_title="OV Trial Blog AI", layout="wide")
st.title("🔬 AI 기반 항암 바이러스 블로그 자동 생성기")

with st.sidebar:
    keyword = st.text_input("검색 키워드", "Oncolytic Virus")
    count = st.slider("분석할 임상 수", 3, 10, 5)
    if st.button("1. 데이터 가져오기"):
        st.session_state.df = fetch_clinical_trials(keyword, count)

if 'df' in st.session_state:
    st.subheader("📋 수집된 최신 임상 데이터")
    st.dataframe(st.session_state.df[['NCT ID', 'Title', 'Status', 'Sponsor']], use_container_width=True)

    if st.button("2. AI 블로그 초안 생성하기"):
        with st.spinner('AI가 데이터를 분석하여 글을 쓰고 있습니다...'):
            blog_draft = generate_blog_post(st.session_state.df)
            st.success("포스팅 초안이 완성되었습니다!")
            st.markdown("---")
            st.text_area("복사하여 블로그에 사용하세요", blog_draft, height=600)
