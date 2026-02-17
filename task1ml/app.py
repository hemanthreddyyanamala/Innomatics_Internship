"""
Simple Flask app for sentiment analysis (Flipkart reviews)

Usage:
 - Place your trained `model.pkl` (or `model.joblib`) in the same folder as this file.
 - If your model is not a pipeline, optionally place a `vectorizer.pkl` / `tfidf.pkl` next to it.
 - Install dependencies: pip install flask joblib scikit-learn
 - Run: python app.py

Endpoints:
 - GET  /       -> HTML form to enter review text
 - POST /       -> Form submission returns prediction page
 - POST /api/predict -> JSON API: {"text": "..."} returns prediction and score

The loader is robust and tries joblib/pickle and attempts to detect whether the model
already includes preprocessing (Pipeline). If not, it will try to use a `vectorizer` file
if present.
"""

import os
import sys
import logging
from typing import Any, Dict, List

from flask import Flask, request, jsonify, render_template_string

# try both joblib and pickle
try:
    import joblib
except Exception:
    joblib = None
import pickle

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_FILENAMES = ["model.pkl", "model.joblib", "best_model.pkl"]

model = None

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Flipkart Review Sentiment</title>
    <style>body{font-family:Arial,Helvetica,sans-serif; margin:40px;} .result{margin-top:20px;padding:10px;border-radius:6px;} .pos{background:#e6ffed;border:1px solid #b7f0c8;} .neg{background:#ffecec;border:1px solid #f0b7b7;}</style>
  </head>
  <body>
    <h1>Flipkart Review Sentiment</h1>
    <form method="post" action="/">
      <textarea name="text" rows="6" cols="80" placeholder="Enter review text here..."></textarea><br>
      <button type="submit">Predict</button>
    </form>
    {% if prediction is defined %}
    <div class="result {{'pos' if label=='positive' else 'neg'}}">
      <strong>Prediction:</strong> {{ label }} <br>
      <strong>Score:</strong> {{ score }}
      <p><em>Input:</em> {{ text }}</p>
    </div>
    {% endif %}
  </body>
</html>
"""


def try_load_file(filenames: List[str]) -> Any:
    """Try to load a model-like object from a list of filenames."""
    for fn in filenames:
        if os.path.exists(fn):
            logger.info(f"Loading from {fn}")
            try:
                if joblib and fn.endswith((".joblib", ".pkl")):
                    return joblib.load(fn)
            except Exception as e:
                logger.warning(f"joblib load failed for {fn}: {e}")
            try:
                with open(fn, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"pickle load failed for {fn}: {e}")
    return None


def load_artifacts():
    global model
    model = try_load_file(MODEL_FILENAMES)
    if model is None:
        logger.warning("No model file found. Please place `model.pkl` next to app.py")
    else:
        logger.info(f"Model loaded: {type(model)}")

    # Model is expected to be a sklearn Pipeline that handles raw text input.
    if hasattr(model, "named_steps"):
        logger.info("Detected sklearn Pipeline. It will handle raw text input.")
    else:
        logger.warning("Loaded model does not appear to be a Pipeline. Ensure it accepts raw text strings or wrap preprocessing in a Pipeline.")


def predict_texts(texts: List[str]) -> List[Dict[str, Any]]:
    if model is None:
        raise RuntimeError("Model not loaded. Put model.pkl next to app.py and restart the app.")

    # Prepare input
    X = texts
    # Model pipeline should handle any required preprocessing of raw text strings.

    # Predict
    try:
        preds = model.predict(X)
    except Exception as ex:
        logger.exception("Model prediction failed: %s", ex)
        raise

    results = []
    probs = None
    if hasattr(model, "predict_proba"):
        try:
            probs = model.predict_proba(X)
        except Exception:
            probs = None
    for i, p in enumerate(preds):
        label = p
        score = None
        if probs is not None:
            # Choose highest probability and, if possible, pick probability for positive class
            try:
                # if classes_ includes a recognizable positive label
                classes = getattr(model, "classes_", None)
                if classes is not None:
                    pos_idx = None
                    for candidate in ["positive", "pos", "1", 1, "Positive"]:
                        if candidate in classes:
                            pos_idx = list(classes).index(candidate)
                            break
                    if pos_idx is None:
                        # fallback: choose the class that is likely positive by looking at label type
                        pos_idx = 1 if probs.shape[1] > 1 else 0
                    score = float(probs[i, pos_idx])
                else:
                    score = float(probs[i].max())
            except Exception:
                score = float(probs[i].max())
        results.append({"label": str(label), "score": score})
    return results


@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    label = None
    score = None
    text = None
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            try:
                res = predict_texts([text])[0]
                label = res["label"]
                score = res["score"]
            except Exception as ex:
                label = f"Error: {ex}"
                score = None

    return render_template_string(HTML_TEMPLATE, prediction=prediction, label=label, score=score, text=text)


@app.route("/api/predict", methods=["POST"])
def api_predict():
    payload = request.get_json(force=True, silent=True)
    if payload is None:
        return jsonify({"error": "Invalid JSON payload"}), 400
    text = payload.get("text")
    if text is None:
        return jsonify({"error": "Provide 'text' field in JSON."}), 400
    single = False
    if isinstance(text, str):
        texts = [text]
        single = True
    elif isinstance(text, list):
        texts = text
    else:
        return jsonify({"error": "'text' must be a string or a list of strings"}), 400

    try:
        out = predict_texts(texts)
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

    return jsonify({"predictions": out} if not single else out[0])


if __name__ == "__main__":
    load_artifacts()
    # Helpful note: If you restart frequently while developing, run with debug=True
    app.run(host="0.0.0.0", port=5000, debug=True)
