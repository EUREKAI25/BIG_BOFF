from flask import Flask, jsonify
from flask_cors import CORS
import subprocess, os
APP = Flask(__name__)
CORS(APP, resources={r"/*": {"origins": ["http://localhost:*","chrome-extension://*"]}})
SCRIPT = "/Users/nathalie/Dropbox/PROJETS/EUREKAI/INBOX_EUREKAI/auto_inventory.sh"
@APP.post("/run_inventory")
def run_inventory():
    if not os.path.exists(SCRIPT):
        return jsonify({"status":"error","output":f"Script introuvable: {SCRIPT}"}), 404
    try:
        proc = subprocess.run(["bash", SCRIPT], cwd=os.path.dirname(SCRIPT), capture_output=True, text=True, timeout=120)
        status = "ok" if proc.returncode == 0 else f"fail({proc.returncode})"
        return jsonify({"status":status, "output": (proc.stdout + '\n' + proc.stderr).strip()})
    except Exception as e:
        return jsonify({"status":"error","output":str(e)}), 500
if __name__ == "__main__":
    APP.run(host="127.0.0.1", port=5050, debug=False)
