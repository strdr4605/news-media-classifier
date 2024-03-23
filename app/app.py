import requests
import json
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    return render_template("data.html")

@app.route('/news', methods=['POST'])
def news():
    news = list(request.json)

    return [get_score(x) for x in news]

def get_score(url: str) -> float:
    metadata = get_metadata(url)
    news_title = metadata["Title"]
    clickbait_scores = get_clickbait_score(news_title)
    return get_clickbaitness(clickbait_scores)

def get_metadata(url: str):
    metadata_request = {
        'content': url,
        'language': 'EMPTY'
    }
    metadata_response = requests.post('http://localhost:8990/rest/process', json=metadata_request)
    return json.loads(metadata_response.text)

def get_clickbait_score(title: str):
    click_bait_request = {
        'content': title,
        'language': 'ron'
    }
    clickbait_response = requests.post('http://localhost:8994/rest/process', json=click_bait_request)
    return json.loads(clickbait_response.text)

def get_clickbaitness(scores) -> float:
    for score in scores["categories"]:
        if score["label"] == "clickbait":
            return 1 - score["score"]
        if score["label"] == "not clickbait":
            return score["score"]
