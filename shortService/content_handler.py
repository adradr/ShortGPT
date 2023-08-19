from flask import Flask, jsonify
import requests
import db_utils

app = Flask(__name__)

DOWNLOAD_HANDLER_TRENDING_URL = (
    "http://download-handler:8886/get_trending_youtube_videos"
)
SHORTGPT_URL = "http://shortgpt-api:8888/generate-custom-short-video"


@app.route("/fetch-and-store-content", methods=["GET"])
def fetch_and_store_content():
    # Fetch trending videos from the downloadHandler API
    response = requests.get(
        DOWNLOAD_HANDLER_TRENDING_URL, params={"max_results": 10}
    )  # I've set a default of 10 videos
    videos = response.json()

    # Store each video in the database
    for video in videos:
        db_utils.store_content_in_db(
            content_type="video",
            content_name=video["title"],
            content_description=video["description"],
        )

    return (
        jsonify({"message": "Trending content fetched and stored successfully!"}),
        200,
    )


@app.route("/render-unprocessed", methods=["GET"])
def render_unprocessed():
    # Fetch unprocessed content from the database
    contents = db_utils.fetch_contents_to_render()

    # Send a request to shortGPT API for each content
    for content in contents:
        video_name = content[0]
        video_url = content[1]
        description = content[2]

        # Prepare the payload based on the shortGPT API documentation
        data = {
            "video_url": video_url,
            "video_name": video_name,
            "video_script": description,
            # "num_images": 0,  # This is arbitrary, adjust as needed
            # "prepromt_text": "This is a short description of ",  # Modify as required
            "store_in_db": True,  # This assumes you want to store generated videos
        }

        response = requests.post(SHORTGPT_URL, json=data)

        # Assuming shortGPT API responds with a success status and the video_output_path
        if response.status_code == 200 and "video_output_path" in response.json():
            db_utils.set_content_rendered(video_name)
            # Optionally, you can store the video_output_path in your database

    return jsonify({"message": "Content rendering triggered!"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8885)
