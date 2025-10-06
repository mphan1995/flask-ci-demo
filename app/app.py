
from flask import Flask, render_template, jsonify
import json
from pathlib import Path

app = Flask(__name__)

def load_products():
    data_path = Path(__file__).parent / "data" / "products.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def home():
    products = load_products()
    # pick top 6 for landing
    return render_template("index.html", products=products[:6])

@app.route("/api/products")
def api_products():
    return jsonify(load_products())

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
