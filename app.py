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
        아래의 최신 임상 데이터를 바탕으로 네이버 블로그에 바로 올릴 수 있는 형태의 글을 쓰세요.
    
        [지시 사항]
        1. 마크다운 기호(예: **, ##, ###)를 절대로 사용하지 마세요.
        2. 소제목이나 강조하고 싶은 부분은 기호 대신 [제목] 또는 <내용>과 같은 괄호를 사용하거나 줄바꿈을 활용하세요.
        3. 번역투(예: 일제삼, проти 등)를 완전히 없애고 한국인이 읽기에 자연스러운 문장으로 작성하세요.
        4. 의학 용어는 일반인도 이해하기 쉽게 풀어서 설명하세요.
        5. 서론-본론-결론의 구성을 유지하고, 마지막에 희망적인 메시지를 담으세요.
    
        [데이터]
        {context}
        """

    # Groq은 Llama 3나 Mixtral 모델을 사용합니다. 속도가 매우 빠릅니다.
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.1-8b-instant", # 무료로 쓰기 가장 안정적인 모델입니다.
    )
    return chat_completion.choices[0].message.content

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
