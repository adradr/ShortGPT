import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.service_account import Credentials
from flask import Flask, jsonify, request

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
CLIENT_SECRETS_FILE = "client_secret.json"
SERVICE_ACCOUNT_FILE = "service_account_shortgpt.json"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

app = Flask(__name__)


def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    # credentials = flow.run_local_server(port=0)
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


@app.route("/get_youtube_videos", methods=["GET"])
def get_youtube_videos_endpoint():
    query = request.args.get("query")
    max_results = request.args.get("max_results", 10)
    youtube = get_authenticated_service()

    search_response = (
        youtube.search()
        .list(q=query, type="video", part="id,snippet", maxResults=max_results)
        .execute()
    )

    video_urls = []
    for search_result in search_response.get("items", []):
        video = {
            "title": search_result["snippet"]["title"],
            "url": "https://www.youtube.com/watch?v=" + search_result["id"]["videoId"],
            "description": search_result["snippet"]["description"],
            "tags": search_result["snippet"]["tags"]
            if "tags" in search_result["snippet"]
            else [],
        }
        video_urls.append(video)

    return jsonify(video_urls)


@app.route("/get_trending_youtube_videos", methods=["GET"])
def get_trending_youtube_videos_endpoint():
    region_code = request.args.get("region_code", "US")
    max_results = request.args.get("max_results", 10)
    youtube = get_authenticated_service()

    # Use the videos().list method to retrieve trending videos
    trending_response = (
        youtube.videos()
        .list(
            part="id,snippet",
            chart="mostPopular",  # This specifies that we want trending videos
            regionCode=region_code,
            maxResults=max_results,
        )
        .execute()
    )

    video_urls = []
    for item in trending_response.get("items", []):
        video = {
            "title": item["snippet"]["title"],
            "url": "https://www.youtube.com/watch?v=" + item["id"],
            "description": item["snippet"]["description"],
            "tags": item["snippet"]["tags"] if "tags" in item["snippet"] else [],
        }
        video_urls.append(video)

    return jsonify(video_urls)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8886, debug=True)
