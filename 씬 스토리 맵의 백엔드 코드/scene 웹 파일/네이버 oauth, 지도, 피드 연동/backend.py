# Flask 웹 프레임워크, 요청 및 JSON 응답, 템플릿 렌더링을 위한 함수 임포트
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
# CORS(Cross-Origin Resource Sharing)를 허용하기 위한 모듈
from flask_cors import CORS
# 고유 ID 생성을 위한 uuid 모듈
import uuid
# 디렉토리 및 파일 작업을 위한 os 모듈
import os
import pymysql  # MySQL 데이터베이스와의 연결을 위한 pymysql 모듈 불러오기
import requests  # HTTP 요청을 보내기 위한 requests 모듈 불러오기
from urllib.parse import urlencode  # URL 인코딩을 위한 urlencode 함수 불러오기
import mysql.connector  # MySQL 데이터베이스 접속을 위한 또 다른 라이브러리 (메인 DB 연결용)

# Flask 앱 생성
app = Flask(__name__)
app.secret_key = os.urandom(24)  # 세션 보호를 위한 랜덤한 비밀키 설정

# 네이버 앱 등록 후 받은 정보 입력
NAVER_CLIENT_ID = 'E9J2BHv7nU9IlUjaOHF3'  # 네이버 클라이언트 ID
NAVER_CLIENT_SECRET = 'm3QABNs2um'  # 네이버 클라이언트 시크릿
NAVER_REDIRECT_URI = 'http://localhost:5000/naver_callback'  # 네이버 OAuth 콜백 URI

# 모든 도메인에 대해 CORS 허용 설정
CORS(app)

# 피드별로 이미지 폴더를 저장할 상위 디렉토리 이름 설정
UPLOAD_FOLDER = 'feed_folders'
# 해당 폴더가 존재하지 않으면 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MySQL 데이터베이스 연결 설정
conn = mysql.connector.connect(
    host="localhost",       # MySQL 호스트명 (로컬호스트)
    user="root",            # MySQL 사용자명
    password="frziu2357*",  # MySQL 비밀번호
    database="feeds"        # 사용할 데이터베이스 이름
)
# 전역 커서 생성 (CRUD 실행에 사용)
cursor1 = conn.cursor()

db = pymysql.connect(  # pymysql을 사용해 MySQL에 연결
    host="localhost",  # MySQL 호스트 주소
    user="root",  # MySQL 사용자명
    password="frziu2357*",  # MySQL 비밀번호

    database="user",  # 사용할 데이터베이스 이름
    charset='utf8mb4',  # 문자 인코딩 설정
    cursorclass=pymysql.cursors.DictCursor  # 결과를 딕셔너리 형식으로 반환
)
cursor2 = db.cursor()  # 데이터베이스 커서 객체 생성

# 루트 URL('/') 접속 시 Home.html 템플릿을 반환
@app.route("/")
def index():
    return render_template("Home.html")  # templates 폴더 내의 HTML 파일 렌더링

# 홈 화면 - 네이버 로그인 링크 생성
@app.route('/register')  # 기본 라우트, 홈 페이지
def login():
    state = str(uuid.uuid4())  # CSRF 방지를 위한 상태 값 생성
    session['oauth_state'] = state  # 세션에 상태 값을 저장
    naver_auth_url = (  # 네이버 인증 URL 생성
        
        "https://nid.naver.com/oauth2.0/authorize?" +
        urlencode({  # URL 인코딩을 위한 파라미터 설정
            'response_type': 'code',  # 응답 타입은 code
            'client_id': NAVER_CLIENT_ID,  # 네이버 클라이언트 ID
            'redirect_uri': NAVER_REDIRECT_URI,  # 리다이렉트 URI
            'state': state  # 생성된 상태 값
        })
    )
    return render_template('register_login.html', naver_auth_url=naver_auth_url)  # 생성된 네이버 인증 URL을 템플릿에 전달

# 네이버 콜백 처리
@app.route('/naver_callback')  # 네이버 로그인 후 리디렉션될 콜백 URL
def naver_callback():
    code = request.args.get('code')  # URL에서 전달된 코드 파라미터를 가져옴
    state = request.args.get('state')  # URL에서 전달된 상태 값을 가져옴

    if state != session.get('oauth_state'):  # CSRF 공격 방지를 위한 상태 값 검증
        return "잘못된 접근입니다. (CSRF)", 400  # 상태 값이 다르면 에러 반환

    # 액세스 토큰 요청
    token_url = 'https://nid.naver.com/oauth2.0/token'  # 네이버 액세스 토큰 요청 URL
    token_params = {  
        # 액세스 토큰 요청 파라미터
        'grant_type': 'authorization_code',  # grant_type은 authorization_code
        'client_id': NAVER_CLIENT_ID,  # 네이버 클라이언트 ID
        'client_secret': NAVER_CLIENT_SECRET,  # 네이버 클라이언트 시크릿
        'code': code,  # 사용자로부터 받은 코드
        'state': state  # 상태 값
    }
    token_res = requests.get(token_url, params=token_params)  # 액세스 토큰을 요청
    token_data = token_res.json()  # JSON 형식으로 응답을 파싱

    access_token = token_data.get('access_token')  # 액세스 토큰 추출
    if not access_token:  # 액세스 토큰이 없으면 에러 반환
        return "토큰 발급 실패", 400

    # 사용자 정보 요청
    headers = {'Authorization': f'Bearer {access_token}'}  # Authorization 헤더에 액세스 토큰 추가
    profile_res = requests.get('https://openapi.naver.com/v1/nid/me', headers=headers)  # 네이버 사용자 정보 요청
    profile_data = profile_res.json()  # JSON 형식으로 응답을 파싱

    if profile_data['resultcode'] != '00':  # 사용자 정보 조회 실패 시 에러 반환
        return "사용자 정보 조회 실패", 400

    user_info = profile_data['response']  # 사용자 정보
    naver_id = user_info['id']  # 네이버 사용자 ID
    nickname = user_info.get('nickname', '네이버사용자')  # 네이버 닉네임 (없으면 기본값 설정)

    # DB에 사용자 존재 확인
    cursor2.execute("SELECT * FROM users WHERE user_id = %s", (naver_id,))  # 사용자 ID로 DB에서 조회
    user = cursor2.fetchone()  # 사용자 정보 가져오기

    if not user:  # 사용자가 없으면 새로 등록
        user_uuid = str(uuid.uuid4())  # 새로운 UUID 생성
        cursor2.execute(
            "INSERT INTO users (id, user_id, nickname) VALUES (%s, %s, %s)",  # DB에 사용자 정보 삽입
            (user_uuid, naver_id, nickname)
        )
        db.commit()  # DB 커밋
        session['user_id'] = user_uuid  # 세션에 사용자 ID 저장
    else:
        session['user_id'] = user['id']  # 이미 존재하는 사용자라면 세션에 사용자 ID 저장
    return redirect(url_for('profile'))  # 프로필 페이지로 리디렉션

# 로그인 후 프로필 페이지
@app.route('/profile')  # 프로필 페이지 라우트
def profile():
    user_id = session.get('user_id')  # 세션에서 사용자 ID 가져오기
    if not user_id:  # 사용자 ID가 없으면 로그인 화면으로 리디렉션
        return redirect(url_for('register_login'))

    cursor2.execute("SELECT * FROM users WHERE id = %s", (user_id,))  # DB에서 사용자 정보 조회
    user = cursor2.fetchone()  # 사용자 정보 가져오기

    if not user:  # 사용자를 찾을 수 없으면 에러 반환
        return "사용자 정보를 찾을 수 없습니다.", 404

    return render_template('profile.html', user=user)  # 프로필 페이지에 사용자 정보 전달하여 렌더링

# 프로필 사진 업로드
@app.route('/upload_profile_pic', methods=['POST'])  # 프로필 사진 업로드 처리
def upload_profile_pic():
    if 'profile_pic' not in request.files:  # 파일이 전송되지 않았을 경우 에러 처리
        return "No file part", 400

    file = request.files['profile_pic']  # 업로드된 파일 가져오기
    if file.filename == '':  # 파일명이 비어있을 경우 에러 처리
        return "No selected file", 400

    # static/uploads 폴더가 없으면 생성
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')  # 업로드 폴더 경로
    if not os.path.exists(upload_folder):  # 폴더가 없으면 생성
        os.makedirs(upload_folder)

    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]  # 고유한 파일명 생성
    upload_path = os.path.join(upload_folder, filename)  # 파일 저장 경로

    file.save(upload_path)  # 파일 저장

    # 프로필 사진 파일명을 DB에 저장
    user_id = session.get('user_id')  # 세션에서 사용자 ID 가져오기
    cursor2.execute("UPDATE users SET profile_picture = %s WHERE id = %s", (filename, user_id))  # DB에서 프로필 사진 업데이트
    db.commit()  # DB 커밋
    return redirect(url_for('profile'))  # 프로필 페이지로 리디렉션

# 자기소개 업데이트
@app.route('/update_intro', methods=['POST'])  # 자기소개 수정 처리
def update_intro():
    intro_text = request.form['intro_text']  # 폼에서 자기소개 텍스트 가져오기
    user_id = session.get('user_id')  # 세션에서 사용자 ID 가져오기
    
    cursor2.execute("UPDATE users SET introduction = %s WHERE id = %s", (intro_text, user_id))  # DB에서 자기소개 업데이트
    db.commit()  # DB 커밋
    return redirect(url_for('profile'))  # 프로필 페이지로 리디렉션





# 계정 삭제 라우트
@app.route('/delete_account', methods=['POST'])
def delete_account():
    user_id = session.get('user_id')  # 세션에서 사용자 고유 UUID 가져오기
    if not user_id:
        return redirect(url_for('register_login'))  # 로그인 상태 아니면 홈으로

    # DB에서 해당 사용자 정보 삭제
    cursor2.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()  # 변경사항 저장

    session.clear()  # 세션 초기화 (로그아웃 처리)
    return redirect(url_for('register_login'))  # 홈 페이지로 이동

# 로그아웃
@app.route('/logout')  # 로그아웃 라우트
def logout():
    session.clear()  # 세션 데이터 삭제
    return redirect(url_for('register_login'))  # 홈 페이지로 리디렉션

# 피드 추가 요청을 처리하는 API 엔드포인트
@app.route("/add_feed", methods=["POST"])
def add_feed():
    # 클라이언트에서 전송된 JSON 데이터를 파싱
    data = request.json
    # 위도, 경도, 피드 설명 텍스트 추출
    lat = data.get("lat")
    lng = data.get("lng")
    intro = data.get("feed_introduction", "")

    try:
        # UUID를 이용해 고유 피드 ID 생성
        feed_id = str(uuid.uuid4())
        # feed_id 이름의 개별 폴더 생성 경로 지정
        folder_name = os.path.join(UPLOAD_FOLDER, feed_id)
        # 해당 폴더가 존재하지 않으면 생성
        os.makedirs(folder_name, exist_ok=True)

        # 절대 경로를 상대 경로로 변환하여 DB에 저장
        relative_path = os.path.relpath(folder_name, start=os.getcwd())

        # 피드 정보를 feed 테이블에 INSERT
        cursor1.execute("""
            INSERT INTO feed (feed_id, latitude, longitude, feed_introduction, feed_pictures)
            VALUES (%s, %s, %s, %s, %s)
        """, (feed_id, lat, lng, intro, relative_path))
        # 변경사항을 DB에 커밋
        conn.commit()

        # 저장 성공 메시지를 JSON으로 반환
        return jsonify({"success": True, "feed_id": feed_id}),200  # 성공 응답 코드 200
    except Exception as e:
        # 예외 발생 시 에러 메시지 출력 및 실패 응답 반환
        print("❌ DB 저장 오류:", e)
        return jsonify({"success": False, "message": str(e)}),500  # 실패 응답 코드 500

# 클라이언트가 기존 피드 목록을 요청할 때 사용하는 GET API
@app.route('/get_feeds', methods=['GET'])
def get_feeds():
    # 결과를 딕셔너리 형태로 받기 위해 cursor 설정
    cursor1 = conn.cursor(dictionary=True)
    # 피드 테이블에서 위도, 경도, 설명을 선택하여 조회
    cursor1.execute("SELECT latitude AS lat, longitude AS lng, feed_introduction FROM feed")
    # 모든 결과를 리스트 형태로 저장
    feeds = cursor1.fetchall()
    # JSON 형식으로 응답 반환
    return jsonify(success=True, feeds=feeds)  # ✅ success 필드를 명시적으로 포함

# 이 파일이 직접 실행될 경우 개발 서버 실행
if __name__ == "__main__":
    app.run(debug=True)  # 디버그 모드로 실행 (변경 시 자동 리로드 등 편의 기능 제공)