from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(APP_DIR, "files")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

@app.route("/")
def index():
    file_list = []

    for name in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            file_list.append({
                "name": name,
                "size": format_size(size),
                "bytes": size
            })
    return render_template("index.html", files=file_list)

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return redirect(url_for("index"))
    
    f = request.files["file"]
    if (f.filename == ""):
        return redirect(url_for("index"))
    
    filename = os.path.basename(f.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    f.save(save_path)
    return redirect(url_for("index"))

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)