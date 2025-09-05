from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# DB 연결 정보
db = mysql.connector.connect(
    host="localhost",
    user="scene_story_map",       # ← 너의 MySQL 사용자명
    password="frziu2357*",   # ← 너의 MySQL 비밀번호
    database="userdb"
)

cursor = db.cursor(dictionary=True)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form['user_id']
    password = request.form['password']

    # 해당 아이디로 유저 정보 불러오기
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    if user:
        stored_password_hash = user['password']
        if check_password_hash(stored_password_hash, password):
            # 로그인 성공
            return render_template("profile.html", nickname=user["nickname"])
        else:
            return "❌ 비밀번호가 틀렸습니다."
    else:
        return "❌ 아이디가 존재하지 않습니다."

if __name__ == '__main__':
    app.run(debug=True)
