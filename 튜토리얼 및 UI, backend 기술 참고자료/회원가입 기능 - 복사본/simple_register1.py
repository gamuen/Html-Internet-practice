from flask import Flask, request, redirect, render_template

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    # 여기서 폼 데이터를 처리합니다.
    # HTML 폼에서 전달된 데이터 가져오기
    user_id = request.form['user_id']
    password = request.form['password']
    nickname = request.form['nickname']

    # 여기에 DB 저장, 중복 체크, 비밀번호 암호화 등을 구현 가능

    print(f"아이디: {user_id}, 비밀번호: {password}, 닉네임: {nickname}")

    # 예: 회원가입 후 로그인 페이지로 이동
    return redirect('/login')