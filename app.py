from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename
import os
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
    
    filename = secure_filename(f.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    f.save(save_path)
    return redirect(url_for("index"))

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=443, ssl_context=(CERT_FILE, KEY_FILE))