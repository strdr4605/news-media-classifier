import requests
import json
import sqlite3
from itertools import groupby
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM clickbait_score ORDER BY score").fetchall()
    conn.close()

    medias = [
        (key, aggregate_score(list(group)))
        for key, group in groupby(rows, lambda x: x["publisher"])
    ]

    return render_template("index.html", medias=medias)


@app.route("/submit", methods=["POST"])
def submit_form():
    links = request.form.get("links", "").split("\n")
    conn = get_db_connection()

    for article in links:
        metadata = get_metadata(article)
        news_title = metadata["Title"]
        publisher = metadata["Publisher"]
        score = get_clickbait_score(news_title)
        script = f"INSERT OR IGNORE INTO clickbait_score(publisher, article, score) VALUES('{publisher}' ,'{article}', '{score}')"
        conn.execute(script)

    conn.commit()

    rows = conn.execute("SELECT * FROM clickbait_score ORDER BY score").fetchall()

    medias = [
        (key, aggregate_score(list(group)))
        for key, group in groupby(rows, lambda x: x["publisher"])
    ]

    print(medias)

    conn.close()

    return render_template("result.html", medias=medias)


@app.route("/news", methods=["POST"])
def news():

    articles = list(request.json)

    conn = get_db_connection()

    for article in articles:
        metadata = get_metadata(article)
        news_title = metadata["Title"]
        publisher = metadata["Publisher"]
        score = get_clickbait_score(news_title)
        script = f"INSERT OR IGNORE INTO clickbait_score(publisher, article, score) VALUES('{publisher}' ,'{article}', '{score}')"
        conn.execute(script)

    conn.commit()


    conn.close()

    return "500 Ok"


def get_metadata(url: str):
    metadata_request = {"content": url, "language": "EMPTY"}
    metadata_response = requests.post(
        "https://d9bf-93-113-114-106.ngrok-free.app/rest/process",
        json=metadata_request,
    )
    return json.loads(metadata_response.text)


def get_clickbait_score(title: str) -> float:
    click_bait_request = {"content": title, "language": "ron"}
    clickbait_response = requests.post(
        "https://2017-93-113-114-106.ngrok-free.app/rest/process",
        json=click_bait_request,
    )
    scores = json.loads(clickbait_response.text)
    return get_clickbaitness(scores)


def get_clickbaitness(scores) -> float:
    for score in scores["categories"]:
        if score["label"] == "clickbait":
            return 1 - score["score"]
        if score["label"] == "not clickbait":
            return score["score"]


def aggregate_score(articles) -> float:
    total = sum([x["score"] for x in articles])
    return total * 100 / len(articles)


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    script = """
    CREATE TABLE IF NOT EXISTS clickbait_score (
        article TEXT PRIMARY KEY,
        publisher TEXT NOT NULL,
        score REAL NOT NULL
    );
    """
    conn.executescript(script)
    return conn


if __name__ == "__main__":
    app.run(debug=True)
