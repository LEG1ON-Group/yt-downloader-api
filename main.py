from flask import Flask, request, jsonify, send_from_directory
import uuid
import os
import shutil
from yt_dlp import YoutubeDL

app = Flask(__name__)

BASE_FOLDER = os.path.join(os.getcwd(), "static", "videos")
os.makedirs(BASE_FOLDER, exist_ok=True)


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    unique_id = uuid.uuid4().hex
    temp_folder = os.path.join(BASE_FOLDER, unique_id)
    os.makedirs(temp_folder, exist_ok=True)
    output_template = os.path.join(temp_folder, "%(title).70s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "cookiefile": "cookies.txt",
        "noplaylist": True,
        "quiet": True,
        "external_downloader": "aria2c",
        "external_downloader_args": ["-x", "16", "-k", "1M"],
        "ffmpeg_location": "/usr/bin/ffmpeg",  # change if it's in a different location
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([url])
    except Exception as e:
        shutil.rmtree(temp_folder, ignore_errors=True)
        return jsonify({"error": str(e)}), 500

    try:
        # Get the first file from the folder
        downloaded_files = [f for f in os.listdir(temp_folder) if f.endswith(".mp4")]
        if not downloaded_files:
            return jsonify({"error": "Download failed"}), 500
        final_filename = downloaded_files[0]
        return jsonify({"file": f"{unique_id}/{final_filename}"})
    except Exception as e:
        shutil.rmtree(temp_folder, ignore_errors=True)
        return jsonify({"error": str(e)}), 500


@app.route("/file/<path:filename>")
def get_file(filename):
    try:
        return send_from_directory(BASE_FOLDER, filename, as_attachment=True)
    except Exception:
        return jsonify({"error": "File not found"}), 404


@app.route("/", methods=["GET"])
def index():
    return "🚀 YouTube Downloader API (Max Speed Mode) is running!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
