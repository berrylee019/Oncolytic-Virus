import json
import streamlit as st
import os
import pickle
import pandas as pd
from groq import Groq
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ==========================================
# 1. 초기 설정 및 API 키
# ==========================================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
# 블로그 관리자 페이지 URL에서 'blogID=' 뒤의 숫자를 복사해서 넣으세요!
BLOG_ID = "5643916484082800286" 

# ==========================================
# 2. 핵심 로직: AI 글쓰기 함수 ( restored )
# ==========================================
def generate_blog_post_groq(data_df):
    # 데이터 프레임을 텍스트로 변환
    context = ""
    for i, row in data_df.iterrows():
        context += f"[{i+1}] 제목: {row.get('Title', 'N/A')}\n요약: {row.get('Summary', 'N/A')}\n\n"

    prompt = f"""
    당신은 대한민국 최고의 의학 전문 블로거입니다. 
    아래 데이터를 바탕으로 '항암 바이러스' 최신 임상 소식을 한글로 작성하세요.
    
    [규칙]
    1. 마크다운 기호(**, ## 등)를 절대 사용하지 마세요.
    2. 전문 용어는 쉽게 풀어서 설명하고 번역투를 없애세요.
    3. 제목은 [제목] 처럼 대괄호를 사용하세요.
    
    [데이터]
    {context}
    """

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )
    
    # 텍스트 정제 (별표 제거 등)
    raw_content = chat_completion.choices[0].message.content
    clean_content = raw_content.replace('*', '')

    # HTML 구조화 및 하단 필수 문구 추가
    html_post = f"""
    <div style="font-family: 'Nanum Gothic', sans-serif; line-height: 1.8;">
        {clean_content.replace('\n', '<br>')}
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 40px 0;">
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; text-align: center;">
            <p><strong>🔎 실시간 임상 정보 더 알아보기</strong></p>
            <a href="https://clinicaltrials.gov/search?term=Oncolytic%20Virus" target="_blank" style="color: #0056b3;">ClinicalTrials.gov 결과 바로가기</a>
        </div>
        
        <div style="margin-top: 30px; font-size: 12px; color: #888; text-align: center;">
            <p>🚨 <strong>의학적 면책 조항 (Disclaimer)</strong><br>
            본 정보는 참고용이며 전문의의 진단을 대체할 수 없습니다. 정확한 진단 및 치료를 위해서는 반드시 의사와 상담하시기 바랍니다.</p>
        </div>
    </div>
    """
    return html_post

# ==========================================
# 3. Blogger API 관련 함수
# ==========================================
SCOPES = ['https://www.googleapis.com/auth/blogger']

def get_blogger_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 💡 파일 대신 Secrets의 텍스트 데이터를 사용합니다
            client_secrets_data = json.loads(st.secrets["GOOGLE_CLIENT_SECRETS"])
            flow = InstalledAppFlow.from_client_config(client_secrets_data, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            
    return build('blogger', 'v3', credentials=creds)

def post_to_blogspot(title, content):
    service = get_blogger_service()
    body = {"kind": "blogger#post", "title": title, "content": content}
    posts = service.posts().insert(blogId=BLOG_ID, body=body).execute()
    return posts.get('url')

# ==========================================
# 4. 메인 UI (Streamlit)
# ==========================================
st.set_page_config(page_title="항암 바이러스 리포터", layout="wide")
st.title("🏥 항암 바이러스 임상 데이터 분석기")

# ⭐ [중요] 세션 상태 초기화: 앱이 처음 실행될 때 빈 칸을 미리 만들어둡니다.
if "generated_html" not in st.session_state:
    st.session_state.generated_html = ""
    
# [데이터 로드 부분] 
# 형님이 기존에 쓰시던 데이터 로딩 코드(CSV 읽기 등)가 있다면 여기에 넣어주세요.
# 예시: df = pd.read_csv('your_data.csv')

uploaded_file = st.file_uploader("📥 분석할 임상 데이터(CSV) 파일을 업로드하세요", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("✅ 데이터를 성공적으로 불러왔습니다!")
    st.dataframe(df.head()) # 데이터가 잘 들어왔는지 상단 5줄만 확인
else:
    st.info("파일을 업로드하면 분석을 시작할 수 있습니다.")
    st.stop() # 파일이 없으면 아래 코드를 실행하지 않고 멈춤

if st.button("🔍 최신 데이터 분석 및 블로그 초안 생성"):
    with st.spinner('AI가 데이터를 분석하여 블로그 글을 작성 중입니다...'):
        try:
            # 1. 생성 함수 호출
            result_html = generate_blog_post_groq(df)
            st.session_state.generated_html = result_html
            st.success("포스팅 초안이 완성되었습니다!")
        except Exception as e:
            st.error(f"오류 발생: {e}")

# 미리보기 및 전송
if st.session_state.generated_html:
    st.markdown("---")
    st.subheader("📝 포스팅 미리보기")
    st.components.v1.html(st.session_state.generated_html, height=500, scrolling=True)
    
    if st.button("🚀 블로그스팟으로 즉시 전송"):
        try:
            with st.spinner("블로그에 전송 중..."):
                # 제목은 날짜를 넣어주면 좋습니다.
                from datetime import datetime
                today = datetime.now().strftime("%Y-%m-%d")
                url = post_to_blogspot(f"[{today}] 4세대 항암제 최신 임상 정보 리포트", st.session_state.generated_html)
                st.success(f"포스팅 성공! 주소: {url}")
        except Exception as e:
            st.error(f"전송 중 실패: {e}")
