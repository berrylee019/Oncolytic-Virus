import streamlit as st
import requests
import pandas as pd
from groq import Groq

# 1. Groq 클라이언트 설정
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def fetch_clinical_trials(keyword="Oncolytic Virus", limit=5):
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": keyword,
        "pageSize": limit,
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
                "Summary": desc_module.get('briefSummary', '요약 없음')
            })
        return pd.DataFrame(rows)
    return pd.DataFrame()

# 2. AI 블로그 초안 생성 함수 (Groq Llama 3 모델 사용)
def generate_blog_post_groq(data_df):
    context = ""
    for i, row in data_df.iterrows():
        context += f"[{i+1}] 제목: {row['Title']}\n스폰서: {row['Sponsor']}\n요약: {row['Summary']}\n\n"

    prompt = f"""
    당신은 대한민국 최고의 의학 전문 블로거입니다. 
    마크다운 기호(별표 등)를 절대 사용하지 말고, 한국어로 자연스럽게 작성하세요.
    제목은 [제목] 형식을 사용하세요.

    [데이터]
    {context}
    """

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )
    
    # 이 부분의 들여쓰기를 이전 줄(chat_completion)과 똑같이 맞춰야 합니다.
    raw_content = chat_completion.choices[0].message.content
    
    # 별표(*) 기호를 강제로 삭제하여 출력합니다.
    clean_content = raw_content.replace('*', '')
    
    return clean_content

# --- Streamlit UI ---
st.set_page_config(page_title="OV Trial Blog AI (Groq)", layout="wide")
st.title("🔬 Groq 기반 항암 바이러스 블로그 생성기")
st.info("Groq 엔진을 사용하여 초고속으로 블로그 포스팅 초안을 생성합니다.")

with st.sidebar:
    keyword = st.text_input("검색 키워드", "Oncolytic Virus")
    count = st.slider("분석할 임상 수", 3, 10, 5)
    if st.button("1. 데이터 가져오기"):
        st.session_state.df = fetch_clinical_trials(keyword, count)

if 'df' in st.session_state:
    st.subheader("📋 수집된 최신 임상 데이터")
    st.dataframe(st.session_state.df[['NCT ID', 'Title', 'Status', 'Sponsor']], use_container_width=True)

    if st.button("2. Groq AI 블로그 초안 생성"):
        with st.spinner('Groq이 순식간에 글을 작성하고 있습니다...'):
            try:
                blog_draft = generate_blog_post_groq(st.session_state.df)
                st.success("포스팅 초안이 완성되었습니다!")
                st.markdown("---")
                st.text_area("복사하여 블로그에 사용하세요", blog_draft, height=600)
            except Exception as e:
                st.error(f"에러 발생: {e}")
# app.py 파일의 가장 아랫부분에 추가하세요.

st.markdown("---")  # 구분선
st.caption("🚨 **의학적 면책 조항 (Disclaimer)**")
st.caption("본 정보는 참고용이며 전문의의 진단을 대체할 수 없습니다. 정확한 진단 및 치료를 위해서는 반드시 의사와 상담하시기 바랍니다.")
