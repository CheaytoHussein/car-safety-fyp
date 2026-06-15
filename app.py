from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    print(f"[{datetime.now()}] /health was called from {request.remote_addr}")
    return {
        "status": "ok",
        "message": "API is running"
    }, 200


@app.route("/sensor-data", methods=["POST"])
def sensor_data():
    data = request.get_json(silent=True)

    print(f"[{datetime.now()}] /sensor-data was called")
    print("Received data:", data)

    return {
        "status": "received",
        "data": data
    }, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)