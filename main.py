import json
import os
from pathlib import Path
import uuid

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

import config

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER=str(config.UPLOAD_FOLDER),
    MAX_CONTENT_LENGTH=config.MAX_CONTENT_LENGTH,
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev-only-change-me"),
)
config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
config.REELS_FOLDER.mkdir(parents=True, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "GET":
        return render_template("create.html")

    uploads = [file for file in request.files.values() if file and file.filename]
    if not uploads:
        flash("Choose at least one image before creating a reel.", "error")
        return redirect(url_for("create"))
    if any(not allowed_file(file.filename) for file in uploads):
        flash("Only PNG, JPG, JPEG, and WEBP images are supported.", "error")
        return redirect(url_for("create"))

    job_dir = config.UPLOAD_FOLDER / str(uuid.uuid4())
    job_dir.mkdir()
    saved_files = []
    for upload in uploads:
        filename = secure_filename(upload.filename)
        if not filename:
            continue
        destination = job_dir / filename
        stem, suffix, counter = destination.stem, destination.suffix, 1
        while destination.exists():
            destination = job_dir / f"{stem}-{counter}{suffix}"
            counter += 1
        upload.save(destination)
        saved_files.append(destination)
    if not saved_files:
        job_dir.rmdir()
        flash("The selected files did not have usable filenames.", "error")
        return redirect(url_for("create"))

    (job_dir / "desc.txt").write_text(request.form.get("text", "").strip(), encoding="utf-8")
    # The concat demuxer needs absolute paths; repeat the last file to retain its duration.
    escaped = [path.as_posix().replace("'", r"'\''") for path in saved_files]
    manifest = "".join(f"file '{path}'\nduration 1\n" for path in escaped) + f"file '{escaped[-1]}'\n"
    (job_dir / "input.txt").write_text(manifest, encoding="utf-8")
    (job_dir / "status.json").write_text(json.dumps({"status": "queued"}), encoding="utf-8")
    flash("Your reel is queued. Start the worker, then check the gallery shortly.", "success")
    return redirect(url_for("gallery"))


@app.route("/gallery")
def gallery():
    reels = sorted((path.name for path in config.REELS_FOLDER.glob("*.mp4")), reverse=True)
    return render_template("gallery.html", reels=reels)


@app.errorhandler(413)
def upload_too_large(_error):
    flash("Uploads are limited to 100 MB per reel.", "error")
    return redirect(url_for("create"))


if __name__ == "__main__":
    app.run(debug=True)
