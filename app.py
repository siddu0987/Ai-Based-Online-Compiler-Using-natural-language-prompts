from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = "AIzaSyCyxpgc8_2wzTymbcihSJ4pY8AOH3I9KTM"
JD_CLIENT_ID = "7705e8b4ae8b7f6f93c6467887139133"
JD_CLIENT_SECRET = "861359871cbc6dd0519a57e13288b9861d718be8a52cee27b0fe50f0be492cbb"

LANGUAGE_MAP = {
    "python": ("python3", "4"),
    "python3": ("python3", "4"),
    "java": ("java", "4"),
    "c++": ("cpp17", "0"),
    "cpp": ("cpp17", "0"),
    "cpp17": ("cpp17", "0")
}

@app.route("/", methods=["GET"])
def home():
    return "✅ AI Compiler Backend Running!"

@app.route("/generate-code", methods=["POST"])
def generate_code():
    data = request.get_json()
    prompt = data.get("prompt", "")
    user_lang = data.get("language", "").strip().lower()

    if user_lang not in LANGUAGE_MAP:
        return jsonify({"error": "❌ Unsupported language"}), 400

    lang_name = LANGUAGE_MAP[user_lang][0]

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Write a complete {lang_name} program to {prompt}. Only return the code without extra text."
                    }
                ]
            }
        ]
    }

    res = requests.post(gemini_url, headers=headers, json=payload)
    data = res.json()

    if "error" in data:
        return jsonify({
            "error": f"❌ Gemini API Error: {data['error'].get('message', 'Unknown error')}",
            "details": data
        }), 500

    try:
        code = data["candidates"][0]["content"]["parts"][0]["text"]
        code = code.replace("```", "").strip()
        return jsonify({"code": code})
    except Exception as e:
        return jsonify({
            "error": "❌ Failed to parse Gemini response",
            "exception": str(e),
            "details": data
        }), 500

@app.route("/run-code", methods=["POST"])
def run_code():
    data = request.get_json()
    code = data.get("code", "").strip()
    user_lang = data.get("language", "").strip().lower()
    stdin = data.get("stdin", "").strip()

    if user_lang not in LANGUAGE_MAP:
        return jsonify({"error": "❌ Unsupported language"}), 400

    lang, version_index = LANGUAGE_MAP[user_lang]

    payload = {
        "clientId": JD_CLIENT_ID,
        "clientSecret": JD_CLIENT_SECRET,
        "script": code,
        "language": lang,
        "versionIndex": version_index,
        "stdin": stdin
    }

    headers = {"Content-Type": "application/json"}
    res = requests.post("https://api.jdoodle.com/v1/execute", headers=headers, json=payload)

    try:
        result = res.json()
        if "output" in result:
            return jsonify({"output": result.get("output", "").strip()})
        else:
            return jsonify({
                "error": "❌ JDoodle call succeeded but no output received.",
                "details": result
            }), 200
    except Exception:
        return jsonify({
            "error": "❌ JDoodle API call failed",
            "status": res.status_code,
            "details": res.text
        }), res.status_code

if __name__ == "__main__":
    app.run(debug=True)
