import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Blogger API 권한 범위
SCOPES = ['https://www.googleapis.com/auth/blogger']

def get_blogger_service():
    creds = None
    # 이전에 인증한 토큰이 있는지 확인
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # 인증 정보가 없거나 만료된 경우 재인증
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('blogger', 'v3', credentials=creds)

def post_to_blogspot(blog_id, title, content):
    service = get_blogger_service()
    body = {
        "kind": "blogger#post",
        "title": title,
        "content": content
    }
    # 블로그에 포스팅 게시
    posts = service.posts().insert(blogId=5643916484082800286, body=body).execute()
    return posts.get('url')

# --- Streamlit UI 에 버튼 추가 ---
if st.button("🚀 블로그스팟으로 즉시 전송"):
    with st.spinner('자동 포스팅 중...'):
        try:
            # 블로그 ID는 블로그 설정 주소창에서 확인할 수 있습니다.
            blog_id = "형님의_블로그_ID" 
            post_url = post_to_blogspot(blog_id, "4세대 항암제 최신 임상 정리", blog_html_content)
            st.success(f"포스팅 성공! 링크: {post_url}")
            
            # (옵션) 형님의 'AI_Chef_Contents' 시트처럼 포스팅 상태를 기록하면 관리하기 좋습니다.
        except Exception as e:
            st.error(f"포스팅 실패: {e}")
