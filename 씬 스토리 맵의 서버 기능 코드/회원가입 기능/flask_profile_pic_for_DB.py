# 필요한 라이브러리들을 불러오기
from flask import Flask, request, redirect, url_for, render_template, session
from werkzeug.utils import secure_filename  # 파일 이름을 안전하게 다루기 위한 모듈
import os  # 파일 경로 등을 다루기 위한 표준 모듈
import uuid  # 고유한 ID를 만들기 위한 모듈
import pymysql  # MySQL 데이터베이스에 접속하기 위한 라이브러리 (for 일부 작업)
from werkzeug.security import generate_password_hash, check_password_hash  # 비밀번호 해싱과 검증을 위한 모듈
import mysql.connector  # MySQL 데이터베이스 접속을 위한 또 다른 라이브러리 (메인 DB 연결용)

# Flask 앱 객체 생성
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션에 필요한 비밀키 설정

# 프로필 사진 저장 폴더 설정
UPLOAD_FOLDER = 'static\\profile_pics'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Flask 설정에 저장

# MySQL 데이터베이스 연결 설정
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="frziu2357*",
    database="userdb"
)
# 데이터베이스 커서 생성 (dictionary=True 옵션: 결과를 딕셔너리 형태로 반환)
cursor = db.cursor(dictionary=True)

# 기본 페이지 ('/') : 회원가입 및 로그인 페이지 렌더링
@app.route('/')
def index():
    return render_template('register_and_login.html')

# 회원가입 처리 라우트
@app.route('/register', methods=['POST'])
def register():
    # 폼으로부터 입력된 데이터 가져오기
    user_id = request.form['user_id']
    password = request.form['password']
    nickname = request.form['nickname']

    # 비밀번호를 해싱하여 저장
    hashed_pw = generate_password_hash(password)
    # 사용자 고유 UUID 생성
    user_uuid = str(uuid.uuid4())

    try:
        # users 테이블에 새 사용자 정보 삽입
        cursor.execute(
            "INSERT INTO users (id, user_id, password, nickname) VALUES (%s, %s, %s, %s)",
            (user_uuid, user_id, hashed_pw, nickname)
        )
        db.commit()  # 변경사항 저장
        return redirect(url_for('login'))  # 회원가입 성공 후 로그인 페이지로 이동
    except mysql.connector.IntegrityError:
        # 이미 존재하는 아이디일 경우 예외 처리
        return "이미 존재하는 아이디입니다."

# 로그인 처리 라우트
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 폼에서 입력된 아이디와 비밀번호 가져오기
        user_id = request.form['user_id']
        password = request.form['password']

        # 입력된 아이디로 사용자 정보 조회
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            stored_password_hash = user['password']
            # 저장된 해시 비밀번호와 입력 비밀번호 비교
            if check_password_hash(stored_password_hash, password):
                # 비밀번호 일치 시 세션에 사용자 ID 저장
                session['user_id'] = user['id']
                return redirect(url_for('profile'))  # 프로필 페이지로 이동
            else:
                return "❌ 비밀번호가 틀렸습니다."
        else:
            return "❌ 아이디가 존재하지 않습니다."
    return render_template('login.html')  # GET 요청 시 로그인 페이지 렌더링

# 별도로 DB 연결을 새로 생성하는 함수 (파일 업로드 등에서 사용)
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='frziu2357*',
        db='userdb',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# 프로필 사진 업로드 처리 라우트
@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'user_id' not in session:
        return redirect('/login')  # 로그인하지 않은 경우 로그인 페이지로 이동

    file = request.files['profile_pic']  # 업로드된 파일 가져오기
    if file and file.filename != '':  # 파일이 정상적으로 존재하는지 확인
        filename = secure_filename(file.filename)  # 파일명을 안전하게 변환
        ext = os.path.splitext(filename)[1]  # 파일 확장자 추출
        unique_name = str(uuid.uuid4()) + ext  # 고유한 파일명 생성
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)  # 저장할 전체 경로 설정
        file.save(save_path)  # 서버에 파일 저장
        profile_img_web_path = f"profile_pics/{unique_name}"  # 웹에서 접근할 경로 설정

        # 새로 만든 DB 연결 사용
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 해당 사용자의 profile_img_url 업데이트
            sql = "UPDATE users SET profile_img_url = %s WHERE id = %s"
            cursor.execute(sql, (save_path, session['user_id']))
            conn.commit()  # 변경사항 저장
        conn.close()  # DB 연결 종료

    return redirect(url_for('profile'))  # 파일 업로드 후 프로필 페이지로 이동

# 프로필 페이지 라우트
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')  # 로그인하지 않은 경우 로그인 페이지로 이동

    # 새로 만든 DB 연결 사용
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # 현재 로그인한 사용자의 닉네임과 프로필 이미지 경로 가져오기
        sql = "SELECT nickname, profile_img_url FROM users WHERE id = %s"
        cursor.execute(sql, (session['user_id'],))
        user = cursor.fetchone()
    conn.close()

    if user['profile_img_url']:
        # 저장된 경로에서 'static/' 제거하고 슬래시를 일관되게 수정
        profile_img_url = user['profile_img_url'].replace('static/', '').replace('\\', '/')
    else:
        # 프로필 사진이 없는 경우 기본 이미지 사용
        profile_img_url = 'static\\profile_pics\\a7a4c0ca-ed78-4d12-91e7-7c7cb5b87d14.jpg'

    # 프로필 템플릿 렌더링 (닉네임과 프로필 이미지 경로 전달)
    return render_template('profile.html', nickname=user['nickname'], profile_img_url=profile_img_url)

# 앱 실행 (디버그 모드로 실행하여 수정사항 즉시 반영)
if __name__ == '__main__':
    app.run(debug=True)
