from flask import Flask, request, redirect, url_for, render_template, session, jsonify
from werkzeug.utils import secure_filename  # 파일 이름을 안전하게 다루기 위한 모듈
import os, uuid  # 파일 경로 등을 다루기 위한 표준 모듈, 고유한 ID를 만들기 위한 모듈

import pymysql  # MySQL 데이터베이스에 접속하기 위한 라이브러리 (for 일부 작업)

from werkzeug.security import generate_password_hash, check_password_hash  # 비밀번호 해싱과 검증을 위한 모듈
import mysql.connector  # MySQL 데이터베이스 접속을 위한 또 다른 라이브러리 (메인 DB 연결용)
# CORS(Cross-Origin Resource Sharing)를 허용하기 위한 모듈
from flask_cors import CORS
import requests  # HTTP 요청을 보내기 위한 requests 모듈 불러오기
from urllib.parse import urlencode  # URL 인코딩을 위한 urlencode 함수 불러오기


# Flask 앱 객체 생성
app = Flask(__name__)
app.secret_key = '235701'  # 세션에 필요한 비밀키 설정

# 프로필, 배경화면 사진 저장 폴더 설정
UPLOAD_FOLDER = 'static\\profile_pics'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Flask 설정에 저장
app.config['UPLOAD_FOLDER_BG'] = 'static/background_pics'

# 피드별로 이미지 폴더를 저장할 상위 디렉토리 이름 설정
UPLOAD_FOLDER2 = 'feed_folders'
# 해당 폴더가 존재하지 않으면 생성
os.makedirs(UPLOAD_FOLDER2, exist_ok=True)

# MySQL 데이터베이스 연결 설정
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="frziu2357*",
    database="userdb"
)
# 데이터베이스 커서 생성 (dictionary=True 옵션: 결과를 딕셔너리 형태로 반환)
cursor2 = db.cursor(dictionary=True)

conn = mysql.connector.connect(
    host="localhost",       # MySQL 호스트명 (로컬호스트)
    user="root",            # MySQL 사용자명
    password="frziu2357*",  # MySQL 비밀번호
    database="feeds"        # 사용할 데이터베이스 이름
)
# 전역 커서 생성 (CRUD 실행에 사용)
cursor1 = conn.cursor()

# 기본 페이지 ('/') : 회원가입 및 로그인 페이지 렌더링
@app.route('/register_and_login')
def index1():
    return render_template('register_and_login.html')

@app.route("/")
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor2.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor2.fetchone()

        if user:
            profile_img_url = user['profile_img_url']  # DB 컬럼명에 따라 다를 수 있음
            return render_template('Home.html', profile_img_url=profile_img_url)
    
    # 로그인 안 한 경우
    return render_template('Home.html', profile_img_url='static/profile_pics/df51a3cc-cab8-4a35-9eb7-f1495e5afe20.jpg')  # templates 폴더 내의 HTML 파일 렌더링

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
        cursor2.execute(
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
        cursor2.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor2.fetchone()

        if user:
            stored_password_hash = user['password']
            # 저장된 해시 비밀번호와 입력 비밀번호 비교
            if check_password_hash(stored_password_hash, password):
                # 비밀번호 일치 시 세션에 사용자 ID 저장
                session['user_id'] = user['id']
                return redirect(url_for('index'))  # 프로필 페이지로 이동
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


@app.route('/upload_background', methods=['POST'])
def upload_background():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    file = request.files.get('background_pic')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER_BG'], filename)
        file.save(filepath)

        background_url = '/' + filepath.replace('\\', '/')

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE users SET background_pic_url = %s WHERE id = %s"
                cursor.execute(sql, (background_url, session['user_id']))
            conn.commit()
        finally:
            conn.close()

    return redirect(url_for('profile'))

# 프로필 사진 업로드 처리 라우트
@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'user_id' not in session:
        return redirect('/login')  # 로그인하지 않은 경우 로그인 페이지로 이동

    file = request.files['profile_pic']
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1]
        unique_name = str(uuid.uuid4()) + ext

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(save_path)

        # 웹에서 접근 가능한 static/ 하위 경로를 DB에 저장
        profile_img_url = f"profile_pics/{unique_name}"

        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "UPDATE users SET profile_img_url = %s WHERE id = %s"
            cursor.execute(sql, (profile_img_url, session['user_id']))
        conn.commit()
        conn.close()

    return redirect(url_for('profile'))

# 프로필 소개 문구를 업데이트할 때 호출되는 라우트 설정 (POST 메서드만 허용)
@app.route('/update_intro', methods=['POST'])
def update_intro():
    # 세션에 'user_id'가 없으면(로그인하지 않은 경우) 로그인 페이지로 리디렉션
    if 'user_id' not in session:
        return redirect('/login')

    # 클라이언트(브라우저)에서 전송한 폼 데이터 중 'intro_text' 필드를 가져옴
    intro_text = request.form['intro_text']

    # 데이터베이스 연결 생성
    conn = get_db_connection()

    # 데이터베이스 커서를 열고 SQL 쿼리를 실행
    with conn.cursor() as cursor:
        # 현재 로그인한 사용자의 'intro_text' 컬럼을 새로 입력받은 값으로 업데이트하는 SQL 쿼리 작성
        sql = "UPDATE users SET intro_text = %s WHERE id = %s"
        # SQL 쿼리를 실행하면서, intro_text와 user_id 값을 전달하여 안전하게 업데이트
        cursor.execute(sql, (intro_text, session['user_id']))
        # 변경사항을 데이터베이스에 확정(commit)하여 저장
        conn.commit()

    # 커서 작업이 끝났으므로 데이터베이스 연결 종료
    conn.close()

    # 프로필 페이지로 리디렉션하여 업데이트된 소개 문구를 확인할 수 있도록 함
    return redirect(url_for('profile'))

# 프로필 페이지에 접근할 때 호출되는 라우트 설정
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT nickname, profile_img_url, background_pic_url, intro_text 
                FROM users 
                WHERE id = %s
            """
            cursor.execute(sql, (session['user_id'],))
            user = cursor.fetchone()
    finally:
        conn.close()

    if not user:
        return "사용자 정보를 찾을 수 없습니다.", 404

    # 프로필 이미지 처리
    if user['profile_img_url']:
        profile_img_filename = user['profile_img_url'].replace('\\', '/') if user['profile_img_url'] else 'profile_pics\df51a3cc-cab8-4a35-9eb7-f1495e5afe20.jpg'
    else:
        profile_img_filename = 'profile_pics/df51a3cc-cab8-4a35-9eb7-f1495e5afe20.jpg'

    # 배경 이미지 처리
    if user['background_pic_url']:
        background_img_filename = user['background_pic_url'].replace('static/', '').replace('\\', '/')
    else:
        background_img_filename = 'background_pics/df51a3cc-cab8-4a35-9eb7-f1495e5afe20.jpg'

    intro_text = user['intro_text'] if user['intro_text'] else ''

    return render_template(
        'profile.html',
        nickname=user['nickname'],
        profile_img_url=url_for('static', filename=profile_img_filename),
        background_pic_url=url_for('static', filename=background_img_filename),
        intro_text=intro_text
    )

@app.route('/delete_account', methods=['POST'])
def delete_account():
    user_id = session.get('id')  # 세션에서 사용자 고유 UUID 가져오기
    if not user_id:
        return redirect(url_for('Home'))  # 로그인 상태 아니면 홈으로

    # DB에서 해당 사용자 정보 삭제
    cursor2.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()  # 변경사항 저장

    session.clear()  # 세션 초기화 (로그아웃 처리)
    return redirect(url_for('Home'))  # 홈 페이지로 이동


# 로그아웃
@app.route('/logout')  # 로그아웃 라우트
def logout():
    session.clear()  # 세션 데이터 삭제
    return redirect(url_for('Home'))  # 홈 페이지로 리디렉션


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

# making_feed.html을 반환하는 라우트
@app.route("/feed_modal_form")
def feed_modal_form():
    return render_template("making_feed.html")

# 사진 업로드 포함 전체 피드 저장
@app.route("/add_feed_full", methods=["POST"])
def add_feed_full():
    try:
        lat = request.form.get("lat")
        lng = request.form.get("lng")
        intro = request.form.get("feed_introduction", "")
        images = request.files.getlist("feed_images")

        print("📌 수신된 lat:", lat)
        print("📌 수신된 lng:", lng)
        print("📌 수신된 intro:", intro)
        print("📌 수신된 이미지 수:", len(images))

        feed_id = str(uuid.uuid4())
        folder_path = os.path.join(UPLOAD_FOLDER2, feed_id)
        os.makedirs(folder_path, exist_ok=True)

        image_urls = []

        for img in images:
            filename = secure_filename(img.filename)
            img_path = os.path.join(folder_path, filename)
            img.save(img_path)
            image_urls.append(os.path.relpath(img_path, start=os.getcwd()))

        relative_folder_path = os.path.relpath(folder_path, start=os.getcwd())
        print("📂 저장 경로:", relative_folder_path)

        cursor1.execute("""
            INSERT INTO feed (feed_id, latitude, longitude, feed_introduction, feed_pictures)
            VALUES (%s, %s, %s, %s, %s)
        """, (feed_id, lat, lng, intro, relative_folder_path))
        conn.commit()

        return jsonify({"success": True, "feed_id": feed_id, "image_urls": image_urls}), 200
    except Exception as e:
        print("❌ DB 저장 오류:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/update_feed_full', methods=['POST'])
def update_feed_full():
    feed_id = request.form['feed_id']
    new_intro = request.form['feed_introduction']
    pictures = request.files.getlist('feed_images')

    try:
        cursor1.execute("UPDATE feed SET feed_introduction = %s WHERE feed_id = %s", (new_intro, feed_id))
        conn.commit()

        # 기존 폴더에 이미지 추가 저장
        upload_folder = os.path.join('static', 'feed_folders', feed_id)
        os.makedirs(upload_folder, exist_ok=True)
        image_urls = []

        for picture in pictures:
            filename = str(uuid.uuid4()) + os.path.splitext(picture.filename)[-1]
            path = os.path.join(upload_folder, filename)
            picture.save(path)
            image_urls.append(f"/{path}")

        return jsonify({'success': True, 'image_urls': image_urls})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/get_feed_data')
def get_feed_data():
    feed_id = request.args.get('feed_id')
    cursor1.execute("SELECT feed_introduction FROM feed WHERE feed_id = %s", (feed_id,))
    row = cursor1.fetchone()
    if row:
        return jsonify({'success': True, 'feed_introduction': row[0]})
    else:
        return jsonify({'success': False, 'message': 'Feed not found'})
    
@app.route('/get_feed_data_by_coords')
def get_feed_data_by_coords():
    lat = request.args.get('lat')
    lng = request.args.get('lng')

    cursor1.execute("""
        SELECT feed_id, feed_introduction
        FROM feed
        WHERE latitude = %s AND longitude = %s
        LIMIT 1
    """, (lat, lng))
    row = cursor1.fetchone()

    if row:
        return jsonify({
            'success': True,
            'feed': {
                'feed_id': row[0],
                'feed_introduction': row[1]
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Feed not found'})
    

# 앱 실행 (디버그 모드로 실행하여 수정사항 즉시 반영)
if __name__ == '__main__':
    app.run(debug=True)