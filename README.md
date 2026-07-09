# RetinaScan AI — Eye Disease Detection System

An AI-powered web application that detects retinal diseases from fundus images using deep learning, with visual explainability so users can see *why* the model made its prediction.

## What It Does

RetinaScan AI classifies retinal fundus images into 6 disease categories using a fine-tuned **EfficientNetB0** convolutional neural network. Alongside the prediction, it generates a **Grad-CAM heatmap** overlay that highlights the regions of the retina the model focused on, making the diagnosis interpretable rather than a black box.

## Technologies Used

- **Python 3.11**
- **TensorFlow / Keras** — model training and inference (EfficientNetB0 transfer learning)
- **Flask** — backend web server and REST routes
- **OpenCV** — image preprocessing
- **Grad-CAM** — model explainability / heatmap visualization
- **HTML/CSS/JavaScript** — frontend templates

## Features

- Upload a retinal fundus image and get an instant disease classification
- 6-class detection across common retinal conditions
- Grad-CAM heatmap overlay showing the model's attention regions
- Simple, navigable web interface (home, prediction, results pages)
- ~73.5% validation accuracy on the held-out test set

## Model & Dataset

- **Architecture:** EfficientNetB0 (transfer learning, fine-tuned on retinal fundus images)
- **Dataset:** [Eye Disease Dataset by kondwani (Kaggle)](https://www.kaggle.com/datasets/kondwani/eye-disease-dataset)
- **Validation Accuracy:** ~73.5%

> ⚠️ The dataset is not included in this repo due to size. Download it directly from the Kaggle link above and place it in a `dataset/` folder before retraining.

> ⚠️ If `best_eye_model.keras` exceeds GitHub's file size limit, it's hosted externally — see the download link below.

**Trained model download:** `[add your Google Drive / Hugging Face link here]`

## Project Structure

```
RetinaScan-AI/
│── app.py                 # Main Flask application
│── requirements.txt       # Python dependencies
│── README.md
│── .gitignore
│── models/
│   └── best_eye_model.keras
│── static/                # CSS, JS, images
│── templates/             # HTML pages
│── utils/                 # Preprocessing, Grad-CAM helper functions
│── screenshots/
│   ├── home.png
│   ├── prediction.png
│   └── gradcam.png
```

## How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/<ShaunD12522>/RetinaScan-AI.git
cd RetinaScan-AI

# 2. Create and activate a virtual environment (Python 3.11 recommended)
python3.11 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the trained model
# Place best_eye_model.keras inside the models/ folder
# (download link above)

# 5. Run the app
python app.py
```

Then open `http://localhost:5000` in your browser.

## Screenshots

| Home Page | Prediction | Grad-CAM Explainability |
|---|---|---|
| ![Home](screenshots/home.png) | ![Prediction](screenshots/prediction.png) | ![Grad-CAM](screenshots/gradcam.png) |

## Future Improvements

- Expand dataset for higher class balance and accuracy
- Add batch prediction support
- Deploy to a cloud platform (AWS/GCP) with a public inference endpoint
- Add authentication for clinical-style usage

## Author

**Shaun D**
BCA Graduate, St. Francis College, Koramangala, Bangalore
AWS & IBM Cloud Certified | Cloud Computing Enthusiast
