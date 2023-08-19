import os
import db_util
import time
import random
import httplib2
from selenium import webdriver
from tiktok_uploader.upload import upload_video
from moviepy.editor import VideoFileClip
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from flask import Flask, request, jsonify

app = Flask(__name__)

# These constants are defined in the Google's script and should be retained:
httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

# Your previous SCOPES variable was missing, so we'll redefine it here:
SCOPES = [YOUTUBE_UPLOAD_SCOPE]

# API service name and version were missing as well:
API_SERVICE_NAME = YOUTUBE_API_SERVICE_NAME
API_VERSION = YOUTUBE_API_VERSION

CLIENT_SECRETS_FILE = "client_secret.json"
SERVICE_ACCOUNT_FILE = "service_account_shortgpt.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    # credentials = flow.run_local_server(port=0)
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if "id" in response:
                print("Video id '%s' was successfully uploaded." % response["id"])
            else:
                raise Exception(
                    "The upload failed with an unexpected response: %s" % response
                )
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (
                    e.resp.status,
                    e.content,
                )
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                raise Exception("No longer attempting to retry.")
            max_sleep = 2**retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)


def upload_to_youtube(
    video_path: str,
    video_name: str,
    short: bool,
    video_description: str,
    tags: list,
    categoryId="22",
    privacy="public",
):
    if privacy not in VALID_PRIVACY_STATUSES:
        raise ValueError(
            f"Invalid privacy status. Valid options are: {VALID_PRIVACY_STATUSES}"
        )

    if short:
        if "#Shorts" not in tags:
            tags.append("#Shorts")
        duration = check_video_duration(video_path)
        if duration > 60:
            raise ValueError("Shorts videos must be less than 60 seconds")

    youtube = get_authenticated_service()

    body = dict(
        snippet=dict(
            title=video_name,
            description=video_description,
            tags=tags,
            categoryId=categoryId,
        ),
        status=dict(privacyStatus=privacy),
    )

    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True),
    )

    resumable_upload(insert_request)


def check_video_duration(video_path: str):
    with VideoFileClip(video_path) as clip:
        duration = clip.duration
    return duration


@app.route("/share-youtube", methods=["POST"])
def share():
    video_name = request.json.get("video_name")

    if not video_name:
        return jsonify({"error": "video_name is required"}), 400

    video_path, video_description = db_util.read_video_from_db(video_name)

    if not video_path:
        return jsonify({"error": "Video not found in DB"}), 404

    # You need to implement a function to actually upload the video to YouTube using the YouTube API
    upload_to_youtube(
        video_path=video_path,
        video_name=video_name,
        video_description=video_description,
        short=False,
        tags=[],
    )

    return jsonify({"message": "Video uploaded successfully"})


@app.route("/share-all-youtube", methods=["POST"])
def share_all():
    videos = db_util.read_contents_to_upload()

    for video in videos:
        video_name = video[0]
        video_path = db_util.read_video_from_db(video_name)
        upload_to_youtube(video_path, video_name)

    return jsonify({"message": "All videos uploaded successfully"})


@app.route("/share-tiktok", methods=["POST"])
def share_tiktok():
    video_name = request.json.get("video_name")

    if not video_name:
        return jsonify({"error": "video_name is required"}), 400

    video_path, video_description = db_util.read_video_from_db(video_name)

    if not video_path:
        return jsonify({"error": "Video not found in DB"}), 404

    # Create Chrome options
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--disable-software-rasterizer")
    # options.add_argument("window-size=1920x1080")

    # Create remote driver
    driver = webdriver.Remote(
        command_executor="http://selenium-chrome:4444/wd/hub", options=options
    )

    # Upload video to TikTok
    upload_video(
        filename=video_path,
        description=video_description,
        cookies="cookies.txt",
        headless=False,
        browser_agent=driver,
    )

    return jsonify({"message": "Video uploaded successfully"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8885, debug=True)
