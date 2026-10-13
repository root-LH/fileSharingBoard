from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import os
import re
import configparser

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

CERT_FILE = config['SSL']['cert_path']
KEY_FILE = config['SSL']['key_path']
ACCESS_PASSWORD = config['SECURITY']['password']

APP_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(APP_DIR, "files")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = config['SECURITY']['secret_key']
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024

def sanitize_name(name):
    """
    Sanitizes file and folder names while preserving Unicode characters (e.g. Korean).
    Removes path separators and forbidden characters to prevent path manipulation.
    """
    if not name:
        return None
    name = os.path.basename(name.strip())
    name = re.sub(r'[\/\\:*?"<>|]', '', name).strip()
    if name in ['', '.', '..']:
        return None
    return name

def get_safe_path(base_dir, subpath=""):
    """
    Resolves and validates a safe absolute path inside base_dir.
    Prevents directory traversal (Path Traversal) attacks.
    """
    subpath = (subpath or "").strip("/\\ ")
    if not subpath:
        return base_dir
    full_path = os.path.abspath(os.path.join(base_dir, subpath))
    common = os.path.commonpath([os.path.abspath(base_dir), full_path])
    if common != os.path.abspath(base_dir):
        raise ValueError("Invalid path access")
    return full_path

@app.before_request
def check_login():
    if request.endpoint in ['login', 'static']:
        return

    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        input_password = request.form.get("password")
        if input_password == ACCESS_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return "password is incorrect.", 403
    return '''
        <form method="post">
            <h2>Please enter a password for access</h2>
            <input type="password" name="password">
            <input type="submit" value="login">
        </form>
    '''

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

@app.route("/")
def index():
    subpath = request.args.get("path", "").strip("/\\ ")
    try:
        current_dir = get_safe_path(UPLOAD_DIR, subpath)
    except ValueError:
        return redirect(url_for("index"))

    if not os.path.exists(current_dir) or not os.path.isdir(current_dir):
        return redirect(url_for("index"))

    folders = []
    file_list = []

    for name in sorted(os.listdir(current_dir)):
        if name.startswith('.'):
            continue
        path = os.path.join(current_dir, name)
        item_rel_path = os.path.join(subpath, name) if subpath else name
        item_url_path = item_rel_path.replace("\\", "/")

        if os.path.isdir(path):
            folders.append({
                "name": name,
                "path": item_url_path
            })
        elif os.path.isfile(path):
            size = os.path.getsize(path)
            file_list.append({
                "name": name,
                "path": item_url_path,
                "size": format_size(size),
                "bytes": size
            })

    # Build breadcrumb navigation (Root(files) -> Subdirectories)
    breadcrumbs = [{"name": "files", "path": ""}]
    if subpath:
        parts = [p for p in subpath.replace("\\", "/").split("/") if p]
        accum = []
        for part in parts:
            accum.append(part)
            breadcrumbs.append({"name": part, "path": "/".join(accum)})

    # Parent folder path
    parent_path = None
    if subpath:
        parts = [p for p in subpath.replace("\\", "/").split("/") if p]
        if len(parts) > 1:
            parent_path = "/".join(parts[:-1])
        else:
            parent_path = ""

    return render_template(
        "index.html",
        current_path=subpath.replace("\\", "/"),
        parent_path=parent_path,
        breadcrumbs=breadcrumbs,
        folders=folders,
        files=file_list
    )

@app.route("/create_folder", methods=["POST"])
def create_folder():
    folder_name = request.form.get("folder_name", "")
    current_path = request.form.get("current_path", "").strip("/\\ ")

    clean_name = sanitize_name(folder_name)
    if not clean_name:
        return redirect(url_for("index", path=current_path))

    try:
        target_dir = get_safe_path(UPLOAD_DIR, current_path)
        new_folder_path = os.path.join(target_dir, clean_name)
        os.makedirs(new_folder_path, exist_ok=True)
    except ValueError:
        return redirect(url_for("index"))

    return redirect(url_for("index", path=current_path))

@app.route("/upload", methods=["POST"])
def upload():
    current_path = request.form.get("current_path", "").strip("/\\ ")
    if "file" not in request.files:
        return redirect(url_for("index", path=current_path))

    f = request.files["file"]
    if f.filename == "":
        return redirect(url_for("index", path=current_path))

    filename = sanitize_name(f.filename)
    if not filename:
        return redirect(url_for("index", path=current_path))

    try:
        target_dir = get_safe_path(UPLOAD_DIR, current_path)
    except ValueError:
        return redirect(url_for("index"))

    os.makedirs(target_dir, exist_ok=True)
    save_path = os.path.join(target_dir, filename)
    f.save(save_path)
    return redirect(url_for("index", path=current_path))

@app.route("/download/<path:filepath>")
def download(filepath):
    filename = os.path.basename(filepath)
    return send_from_directory(
        UPLOAD_DIR,
        filepath,
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=443, ssl_context=(CERT_FILE, KEY_FILE))