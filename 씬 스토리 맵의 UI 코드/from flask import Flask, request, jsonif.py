from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Google Maps API Key
GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"

# 웹 크롤링을 이용해 장소 정보 가져오기 (예: 네이버 플레이스)
def get_place_info(query):
    search_url = f"https://map.naver.com/v5/search/{query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        # 네이버 플레이스에서 특정 태그 추출하여 장소 정보 가져오기 (HTML 구조 분석 필요)
        places = []
        for item in soup.select(".search_result_item"):  # 예제, 실제 태그는 다를 수 있음
            name = item.select_one(".place_name").text
            address = item.select_one(".place_address").text
            places.append({"name": name, "address": address})
        return places
    return []

# Google Maps API를 이용해 장소 좌표 찾기
def get_place_coordinates(place_name):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place_name}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data["status"] == "OK":
        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    return None, None

# 검색 API 엔드포인트
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    places = get_place_info(query)  # 크롤링으로 장소 가져오기

    for place in places:
        lat, lng = get_place_coordinates(place["name"])
        place["lat"] = lat
        place["lng"] = lng

    return jsonify(places)

# 메인 페이지 렌더링
@app.route("/")
def index():
    return render_template("index.html", google_maps_api_key=GOOGLE_MAPS_API_KEY)

if __name__ == "__main__":
    app.run(debug=True)
