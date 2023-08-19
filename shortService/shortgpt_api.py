import os
import pprint
from flask import Flask, jsonify, request
from db_util import store_video_in_db
from shortGPT.engine.content_video_engine import ContentVideoEngine
from shortGPT.engine.facts_short_engine import FactsShortEngine
from shortGPT.engine.custom_short_engine import CustomShortEngine
from shortGPT.engine.content_short_engine import ContentShortEngine
from shortGPT.audio.eleven_voice_module import ElevenLabsVoiceModule
from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.config.asset_db import AssetDatabase, AssetType
from shortGPT.config.languages import Language
from shortGPT.gpt.gpt_chat_video import generateScript
from shortGPT.config.api_db import ApiKeyManager, ApiProvider


# ... [all your other imports]

app = Flask(__name__)


@app.route("/generate-custom-short-video", methods=["POST"])
def generate_short_video():
    """Endpoint to generate a short video

    Request parameters:
        video_name (str) [required]: name of the video
        video_url (str) [optional]: url of the remote video to add
        music_url (str) [optional]: url of the remote music to add

        video_script (str) [required]: description of the video
        num_images (int) [required]: number of images to add to the video
        prepromt_text (str) [required]: text to add to the description
        watermark (str) [optional]: url of the remote image to add as watermark
        store_in_db (bool) [required]: whether to store the video in the database


    Returns:
        str: path to the generated video
    """

    print("Generating a short video...")
    print("Request: ", request.json)
    # API KEYS
    ApiKeyManager.set_api_key(ApiProvider.OPENAI, os.environ.get("OPENAI_API_KEY"))
    ApiKeyManager.set_api_key(
        ApiProvider.ELEVEN_LABS, os.environ.get("ELEVEN_LABS_API_KEY")
    )

    # REQUEST BODY
    video_name = request.json["video_name"] + "_" + "background_video"
    video_url = request.json["video_url"] if "video_url" in request.json else ""

    music_url = request.json["music_url"] if "music_url" in request.json else video_url
    music_name = (
        request.json["music_name"]
        if "music_name" in request.json
        else request.json["video_name"] + "_" + "background_music"
    )

    video_script = request.json["video_script"]
    num_images = request.json["num_images"] if "num_images" in request.json else 0
    prepromt_text = (
        request.json["prepromt_text"] if "prepromt_text" in request.json else ""
    )
    watermark = request.json["watermark"] if "watermark" in request.json else None

    # ADD ASSETS TO DATABASE
    if video_url != "":
        print("Adding video and music to database...")
        assets = AssetDatabase()
        AssetDatabase.add_remote_asset(
            name=video_name, asset_type=AssetType.BACKGROUND_VIDEO, url=video_url
        )
        AssetDatabase.add_remote_asset(
            name=music_name, asset_type=AssetType.BACKGROUND_MUSIC, url=music_url
        )
        # print(AssetDatabase.get_df())
    else:
        print("No video url provided, using default video and music")
        AssetDatabase.sync_local_assets()

    # GENERATE VOICEOVER SCRIPT
    prepromt_text = (
        "Write me a youtube shorts video script based on the following description that can fill a 30 seconds video: "
        if prepromt_text == ""
        else prepromt_text
    )
    script = prepromt_text + video_script
    print("OpenAI Prompt: ", script)
    voiceover_script = generateScript(script, Language.ENGLISH.value)
    print("Voiceover Script: ")
    pprint.pprint(voiceover_script)
    voice_module = EdgeTTSVoiceModule(voiceName="en-US-AriaNeural")

    # Configure Content Engine
    content_engine = CustomShortEngine(
        voiceModule=voice_module,
        voiceover_script=voiceover_script,
        background_video_name=video_name,
        background_music_name=music_name,
        watermark=watermark,
        num_images=num_images,  # If you don't want images in your video, put 0 or None
        language=Language.ENGLISH,
    )

    # Generate Content
    for step_num, step_logs in content_engine.makeContent():
        print(f" {step_logs}")

    video_output_path = content_engine.get_video_output_path()
    print("Short generated successfully!")
    print("Video Output Path: ", video_output_path)

    # Store video in database
    if "store_in_db" in request.json:
        if request.json["store_in_db"]:
            print("Storing video in database...")
            video_description_path = video_output_path.replace(".mp4", ".txt")
            video_title, video_description = parse_youtube_text_file(
                video_description_path
            )
            store_video_in_db(
                video_output_path=video_output_path,
                video_description=video_description,
                video_title=video_title,
            )

    return jsonify({"video_output_path": video_output_path})


def parse_youtube_text_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    title_start = content.find("---Youtube title---") + len("---Youtube title---")
    title_end = content.find("---Youtube description---")
    description_start = title_end + len("---Youtube description---")

    youtube_title = content[title_start:title_end].strip()
    youtube_description = content[description_start:].strip()

    return youtube_title, youtube_description


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True, threaded=False)
