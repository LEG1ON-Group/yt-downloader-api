from flask import Flask, request, jsonify, send_from_directory
import uuid
import os
from yt_dlp import YoutubeDL

app = Flask(__name__)

# 📁 Create folder if not exists
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "static", "videos")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    filename = f"{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(DOWNLOAD_FOLDER, filename)

    ydl_opts = {
        "outtmpl": output_path,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "cookiefile": "cookies.txt",
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return jsonify({"file": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🛣️ Static file route (for download)
@app.route("/file/<filename>")
def get_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)
