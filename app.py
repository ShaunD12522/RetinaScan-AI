from flask import Flask, request, jsonify, render_template
import numpy as np
import cv2
import json
import base64
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.efficientnet import preprocess_input
import os

app = Flask(__name__)
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH   = os.path.join(BASE_DIR, 'best_eye_model_v2.keras')
INDICES_PATH = os.path.join(BASE_DIR, 'class_indices_v2.json')

print("Loading model... please wait...")
model = load_model(MODEL_PATH)
print("Model loaded successfully!")

with open(INDICES_PATH, 'r') as f:
    class_indices = json.load(f)

idx_to_folder = {v: k for k, v in class_indices.items()}

DISPLAY_NAMES = {
    'ageDegeneration': 'Age-related Macular Degeneration',
    'cataract':        'Cataract',
    'glaucoma':        'Glaucoma',
    'hypertension':    'Hypertensive Retinopathy',
    'myopia':          'Myopia',
    'normal':          'Normal (Healthy Eye)'
}

DISEASE_INFO = {
    'ageDegeneration': "Affects the macula leading to loss of central vision. Most common in people over 50.",
    'cataract':        "Clouding of the eye's natural lens causing blurry vision. Highly treatable with surgery.",
    'glaucoma':        "Damage to the optic nerve often caused by elevated eye pressure. Can lead to blindness if untreated.",
    'hypertension':    "Retinal changes caused by high blood pressure including vessel narrowing and hemorrhages.",
    'myopia':          "Nearsightedness — distant objects appear blurry due to the eyeball being longer than normal.",
    'normal':          "No disease detected. The retina appears healthy with no visible signs of pathology. Regular check-ups are still recommended."
}

SEVERITY = {
    'ageDegeneration': 'High',
    'cataract':        'Moderate',
    'glaucoma':        'High',
    'hypertension':    'Moderate',
    'myopia':          'Low',
    'normal':          'None'
}


def make_gradcam_heatmap(img_tensor, model, last_conv_layer='top_conv'):
    grad_model = tf.keras.models.Model(
        inputs=model.inputs,
        outputs=[model.get_layer(last_conv_layer).output, model.output]
    )
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_tensor)
        top_class = tf.argmax(predictions[0])
        loss = predictions[:, top_class]

    grads         = tape.gradient(loss, conv_outputs)
    pooled_grads  = tf.reduce_mean(grads, axis=(0, 1, 2))
    heatmap       = conv_outputs[0] @ pooled_grads[..., tf.newaxis]
    heatmap       = tf.squeeze(heatmap).numpy()
    heatmap       = np.maximum(heatmap, 0)
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()
    return heatmap


def overlay_gradcam(original_img, heatmap):
    heatmap_resized = cv2.resize(heatmap, (224, 224))
    heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap_resized), cv2.COLORMAP_JET)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
    return cv2.addWeighted(original_img.astype(np.uint8), 0.55, heatmap_colored, 0.45, 0)


def img_to_base64(img_array):
    _, buffer = cv2.imencode('.png', cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))
    return base64.b64encode(buffer).decode('utf-8')


def is_valid_fundus_image(img_rgb):
    h, w = img_rgb.shape[:2]

    # Check 1: Aspect ratio - fundus images are roughly square/circular
    aspect_ratio = w / h
    if aspect_ratio < 0.75 or aspect_ratio > 1.35:
        return False, "Image dimensions don't match a fundus photo"

    # Check 2: Circular dark border (fundus cameras produce a black mask around the circle)
    # This is the most reliable signal - it holds regardless of color grading
    # (some fundus images are blue/green-toned, e.g. red-free imaging modes)
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    corners = [gray[0, 0], gray[0, -1], gray[-1, 0], gray[-1, -1]]
    dark_corners = sum(1 for c in corners if c < 40)
    if dark_corners < 2:
        return False, "No fundus border pattern detected"

    # Check 3: Reject obviously non-medical color profiles (e.g. bright green
    # nature photos, mostly-white documents/screenshots). This is intentionally
    # loose - fundus images can be red/orange OR blue/cyan toned.
    mean_r = np.mean(img_rgb[:, :, 0])
    mean_g = np.mean(img_rgb[:, :, 1])
    mean_b = np.mean(img_rgb[:, :, 2])
    if mean_g > mean_r and mean_g > mean_b and mean_g > 100:
        return False, "Color profile doesn't match a retinal image"

    return True, "Valid"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file       = request.files['image']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img        = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    img        = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Reject non-fundus images before running inference
    is_valid, reason = is_valid_fundus_image(img)
    if not is_valid:
        return jsonify({
            'error': 'not_eye_image',
            'message': "This doesn't look like a retinal fundus image. Please upload a proper eye scan."
        }), 400

    img_resized     = cv2.resize(img, (224, 224))
    img_preprocessed= preprocess_input(img_resized.astype(np.float32).copy())
    img_tensor      = np.expand_dims(img_preprocessed, axis=0)

    preds          = model.predict(img_tensor, verbose=0)[0]
    top_idx        = int(np.argmax(preds))
    top_folder     = idx_to_folder[top_idx]
    top_name       = DISPLAY_NAMES[top_folder]
    top_confidence = float(preds[top_idx]) * 100

    all_probs = []
    for idx, prob in enumerate(preds):
        folder = idx_to_folder[idx]
        all_probs.append({
            'name': DISPLAY_NAMES[folder],
            'prob': round(float(prob) * 100, 1)
        })
    all_probs.sort(key=lambda x: x['prob'], reverse=True)

    try:
        heatmap     = make_gradcam_heatmap(img_tensor, model)
        gradcam_img = overlay_gradcam(img_resized, heatmap)
        gradcam_b64 = img_to_base64(gradcam_img)
    except Exception as e:
        print(f"Grad-CAM error: {e}")
        gradcam_b64 = img_to_base64(img_resized)

    return jsonify({
        'prediction': top_name,
        'confidence': round(top_confidence, 1),
        'info':       DISEASE_INFO[top_folder],
        'severity':   SEVERITY[top_folder],
        'is_normal':  top_folder == 'normal',
        'all_probs':  all_probs,
        'gradcam':    gradcam_b64,
        'original':   img_to_base64(img_resized)
    })


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
