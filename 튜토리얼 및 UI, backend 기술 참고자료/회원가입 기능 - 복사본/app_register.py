from flask import Flask, request, render_template, redirect
import mysql.connector
import uuid
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# MySQL 연결 설정
db = mysql.connector.connect(
    host="localhost",
    user="scene_story_map",
    password="frziu2357*",
    database="userdb"
)
cursor = db.cursor()

@app.route('/')
def index():
    return render_template('register_and_login.html')

@app.route('/register', methods=['POST'])
def register():
    user_id = request.form['user_id']
    password = request.form['password']
    nickname = request.form['nickname']

    hashed_pw = generate_password_hash(password)
    user_uuid = str(uuid.uuid4())

    try:
        cursor.execute(
            "INSERT INTO users (id, user_id, password, nickname) VALUES (%s, %s, %s, %s)",
            (user_uuid, user_id, hashed_pw, nickname)
        )
        db.commit()
        return f"회원가입 완료! UUID: {user_uuid}"
    except mysql.connector.IntegrityError:
        return "이미 존재하는 아이디입니다."

if __name__ == '__main__':
    app.run(debug=True)
