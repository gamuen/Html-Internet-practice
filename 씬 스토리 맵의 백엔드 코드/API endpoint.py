from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL 연결 설정
db_config = {
    "host": "localhost",
    "user": "your_username",
    "password": "your_password",
    "database": "scene_storymap"
}

def get_db_connection():
    return mysql.connector.connect(**db_config)
    
#  위 코드의 설명

# Flask를 사용하여 웹 애플리케이션 app 을 생성.
# MySQL에 연결하기 위해 mysql.connector를 사용.
# db_config에서 MySQL 접속 정보를 설정.
# get_db_connection() 함수: 데이터베이스(MySQL)에 연결하는 함수.
# 필요할 때마다 새로운 연결을 생성.
# 이후 API 엔드포인트에서 이 함수를 사용하여 DB와 통신.

@app.route('/feed', methods=['POST'])
def create_feed():
    """ 새 피드 생성 """
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    # 사용자 조회
    cursor.execute("SELECT id FROM users WHERE naver_id = %s", (data['naver_id'],))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    user_id = user[0]

    # 피드 삽입
    cursor.execute("INSERT INTO feeds (user_id, text) VALUES (%s, %s)", (user_id, data['text']))
    feed_id = cursor.lastrowid

    # 위치 삽입
    cursor.execute("INSERT INTO locations (feed_id, latitude, longitude) VALUES (%s, %s, %s)",
                   (feed_id, data['latitude'], data['longitude']))
    conn.commit()

    cursor.close()
    conn.close()
    return jsonify({"message": "Feed created", "feed_id": feed_id}), 201
    
#  위 코드의 설명
# 클라이언트에서 JSON 데이터 받기

# 요청을 POST /feed로 받으면, JSON 데이터(data)를 추출.
# JSON 데이터에는 naver_id, text, latitude, longitude가 포함됨.
# 사용자가 MySQL DB에 존재하는지 확인

# naver_id를 이용해 users 테이블에서 사용자 id를 찾음.
# return jsonify({"error": "User not found"}), 404: 
# 사용자가 없으면, 404 Not Found 응답을 반환함.
# 새로운 피드(feeds 테이블) 저장함.

# INSERT INTO feeds (user_id, text) 쿼리를 실행해 새 피드를 추가함.
# cursor.lastrowid를 사용하여 새로 생성된 feed_id 가져오기.
# 위치(locations 테이블) 저장함.

# 해당 feed_id를 기반으로 위도/경도를 locations 테이블에 저장함.
# 데이터베이스 반영 (commit()) 후 연결 종료함.

# conn.commit()으로 변경 사항을 DB에 반영했음.
# cursor.close(), conn.close()로 연결을 닫았음.
# return jsonify : 응답을 반환함.

# { "message": "Feed created", "feed_id": feed_id } JSON을 반환.

@app.route('/feeds', methods=['GET'])
def get_feeds():
    """ 지도 축척별 피드 가져오기 """
    latitude = float(request.args.get('latitude'))
    longitude = float(request.args.get('longitude'))
    zoom_level = int(request.args.get('zoom'))  # 지도 줌 레벨

    cluster_size = {
        14: 0.5, 13: 1, 12: 2, 11: 3, 10: 5,
        9: 7, 8: 10, 7: 20, 6: 30, 5: 40, 4: 50, 3: 60, 2: 80, 1: 100
    }[zoom_level]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT feeds.id AS feed_id, feeds.text, locations.latitude, locations.longitude
    FROM feeds
    JOIN locations ON feeds.id = locations.feed_id
    WHERE latitude BETWEEN %s AND %s
      AND longitude BETWEEN %s AND %s
    """
    cursor.execute(query, (latitude - cluster_size, latitude + cluster_size, longitude - cluster_size, longitude + cluster_size))

    result = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
    
#  위 코드의 기능 설명

# 클라이언트에서 URL 파라미터 가져오기 중입니다.

# latitude, longitude: 현재 지도의 중심 좌표임.
# zoom_level: 지도 확대/축소 단계임.
# 줌 레벨별 클러스터링 적용함.

# zoom_level에 따라 피드 조회 범위 조정함 (cluster_size).
# ex) zoom_level=14이면 0.5km 반경, zoom_level=1이면 100km 반경.
# 해당 범위 내의 피드를 검색했음.

# 주어진 latitude, longitude 기준으로 locations 테이블에서 범위 내 데이터를 검색했음.
# 쿼리 실행 후 결과 반환함.

# cursor.fetchall()을 통해 데이터를 리스트로 가져옴.
# dictionary=True로 설정하여 JSON 형식으로 변환 후 반환함.
