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
    temp_folder = os.path.join(BASE_FOLDER, "temp_" + unique_id)
    os.makedirs(temp_folder, exist_ok=True)
    output_template = os.path.join(temp_folder, "%(title).70s.%(ext)s")

    # Step 1: Extract info without downloading
    try:
        with YoutubeDL({"quiet": True, "cookiefile": "cookies.txt"}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        shutil.rmtree(temp_folder, ignore_errors=True)
        return jsonify({"error": "Failed to fetch metadata: " + str(e)}), 500

    # Step 2: Check file size of best format
    max_size_bytes = 500 * 1024 * 1024  # 500 MB
    formats = info.get("formats", [])
    best_format = None

    # Get best format under size limit
    for fmt in reversed(formats):  # start from best
        filesize = fmt.get("filesize") or fmt.get("filesize_approx")
        if filesize and filesize <= max_size_bytes and fmt.get("ext") == "mp4":
            best_format = fmt["format_id"]
            break

    # If no small-enough format found
    if not best_format:
        shutil.rmtree(temp_folder, ignore_errors=True)
        return (
            jsonify(
                {
                    "error": "Video file is too large (over 500MB) and cannot be downscaled automatically."
                }
            ),
            413,
        )

    # Step 3: Download using selected format
    ydl_opts = {
        "outtmpl": output_template,
        "format": best_format,
        "merge_output_format": "mp4",
        "cookiefile": "cookies.txt",
        "noplaylist": True,
        "quiet": True,
        "external_downloader": "aria2c",
        "external_downloader_args": ["-x", "16", "-k", "1M"],
        "ffmpeg_location": "/usr/bin/ffmpeg",
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        shutil.rmtree(temp_folder, ignore_errors=True)
        return jsonify({"error": str(e)}), 500

    try:
        downloaded_files = [f for f in os.listdir(temp_folder) if f.endswith(".mp4")]
        if not downloaded_files:
            shutil.rmtree(temp_folder, ignore_errors=True)
            return jsonify({"error": "Download failed"}), 500

        source_file = os.path.join(temp_folder, downloaded_files[0])
        final_file_path = os.path.join(BASE_FOLDER, f"{unique_id}.mp4")
        shutil.move(source_file, final_file_path)
        shutil.rmtree(temp_folder, ignore_errors=True)

        return jsonify({"file": f"{unique_id}.mp4"})
    except Exception as e:
        shutil.rmtree(temp_folder, ignore_errors=True)
        return jsonify({"error": str(e)}), 500


@app.route("/file/<filename>")
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
