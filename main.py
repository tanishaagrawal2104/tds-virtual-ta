from flask import Flask, request, jsonify
from answer_generator import generate_answer
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # So frontends/test tools can call your API

@app.route("/api/", methods=["POST"])
def api():
    data = request.get_json()
    question = data.get("question", "")
    
    if not question.strip():
        return jsonify({"error": "Missing 'question' field"}), 400

    try:
        response = generate_answer(question)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
