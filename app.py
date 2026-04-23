import streamlit as st
import os
import pickle
import pandas as pd
from groq import Groq
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# 1. 초기 설정 및 API 키 (형님의 기존 환경 변수 설정 유지)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
BLOG_ID = "형님의_실제_블로그_ID" # 여기에 블로그 ID를 꼭 넣어주세요!

# 2. Blogger API 인증 함수
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
            # 주의: Streamlit Cloud에서는 로컬 서버 방식이 안 될 수 있음
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('blogger', 'v3', credentials=creds)

def post_to_blogspot(title, content):
    service = get_blogger_service()
    body = {"kind": "blogger#post", "title": title, "content": content}
    posts = service.posts().insert(blogId=BLOG_ID, body=body).execute()
    return posts.get('url')

# 3. 메인 UI 및 로직
st.title("🏥 항암 바이러스 임상 데이터 분석기")

# 세션 상태 초기화 (생성된 글을 저장해두기 위함)
if "generated_html" not in st.session_state:
    st.session_state.generated_html = ""

# [데이터 분석 및 글 생성 버튼] - 형님의 기존 로직
if st.button("🔍 최신 데이터 분석 및 블로그 초안 생성"):
    # (여기에 형님의 데이터 분석 및 Groq 호출 로직이 들어갑니다)
    # 임시 결과물 예시 (실제로는 함수 호출 결과가 들어가야 함)
    result_html = "<h3>AI가 생성한 포스팅 내용...</h3>" 
    st.session_state.generated_html = result_html
    st.write("초안이 생성되었습니다. 아래 버튼을 눌러 블로그로 전송하세요!")

# 4. 블로그 전송 버튼 (초안이 있을 때만 노출)
if st.session_state.generated_html:
    st.markdown("---")
    st.subheader("📝 생성된 포스팅 미리보기")
    st.components.v1.html(st.session_state.generated_html, height=400, scrolling=True)
    
    if st.button("🚀 블로그스팟으로 즉시 전송"):
        try:
            with st.spinner("블로그에 글을 올리는 중입니다..."):
                url = post_to_blogspot("4세대 항암제 최신 임상 정보", st.session_state.generated_html)
                st.success(f"포스팅 성공! 주소: {url}")
        except Exception as e:
            st.error(f"전송 실패: {e}")
