# 🌿 **Flora – Smart Farming Companion**

### *AI-powered Plant Disease Detection & Crop Recommendation System*

---

## 🚀 Overview

Flora is an intelligent agriculture assistant designed to support farmers, students, and researchers through two main AI systems:

* **Plant Disease Detection** using a deep learning model (EfficientNet-B0)
* **Crop Recommendation** based on soil nutrients and climate conditions
* **Interactive UI** deployed on HuggingFace Spaces & Vercel
* **Full data and experiment tracking** using DagsHub & MLflow

🔍 *AI for Agriculture — fast, accurate, and accessible.*

---

## 🌐 Live Demo (Frontend)

👉 **Vercel:** [https://flora-81nw.vercel.app/home](https://flora-81nw.vercel.app/home)

---

## 🤖 HuggingFace Spaces

* 🌱 **Plant Disease Detection:**
  [https://huggingface.co/spaces/Mai-22/plant-disease-detection](https://huggingface.co/spaces/Mai-22/plant-disease-detection)

* 🌾 **Crop Recommendation:**
  [https://huggingface.co/spaces/Mai-22/Crop-Recommendation-deployment](https://huggingface.co/spaces/Mai-22/Crop-Recommendation-deployment)

---

## 📊 Experiment Tracking (MLflow – DagsHub)

🔗 [https://dagshub.com/maimohamed201526/plant-disease-project](https://dagshub.com/maimohamed201526/plant-disease-project)

---

## 🗄️ Database (Supabase)

🔗 [https://supabase.com/dashboard/project/onnbpuqxtmdddbksfgrt](https://supabase.com/dashboard/project/onnbpuqxtmdddbksfgrt)

---

# ✨ Features

### 🌿 **Plant Disease Detection**

* EfficientNet-B0 trained on the PlantVillage dataset
* 38 disease classes
* Real-time image classification
* Confidence scoring

### 🌾 **Crop Recommendation**

* Predicts best crops using soil N, P, K
* Uses temperature, humidity, pH, rainfall
* ML-based recommendation engine

### 📦 **Containerized Deployment**

* Docker-based HuggingFace Space

### 🧠 **Versioning & Experiment Tracking**

* Managed through MLflow & DagsHub

---

# 🖼️ System Architecture *(Placeholder)*

```
User → Frontend (Vercel) → API → Model Inference (HuggingFace Spaces)
                         → Supabase (User Data)
                         → DagsHub (Model Artifacts + Experiments)
```

---

# 📁 Project Structure

```
📦 flora/
 ┣ 📜 app.py
 ┣ 📜 score.py
 ┣ 📜 requirements.txt
 ┣ 📜 Dockerfile
 ┣ 📜 categories.json
 ┣ 📜 best_efficientnet_b0.pth
 ┗ 📜 README.md
```

---

# 📥 Installation (Local Setup)

```bash
git clone <your-repo-link>
cd flora
pip install -r requirements.txt
python app.py
```

---

# ⚡ API Endpoints

## 🔍 1. Plant Disease Detection

**POST** `/predict_disease`

### Request Body

```json
{
  "image": "<uploaded leaf image>"
}
```

### Response (Placeholder)

```json
{
  "prediction": "CLASS_NAME",
  "confidence": "0.95"
}
```

---

## 🌾 2. Crop Recommendation

**POST** `/recommend_crop`

### Request Body

```json
{
  "N": 0,
  "P": 0,
  "K": 0,
  "temperature": 0,
  "humidity": 0,
  "ph": 0,
  "rainfall": 0
}
```

### Response (Placeholder)

```json
{
  "recommended_crop": "CROP_NAME"
}
```

---

# 🤖 Model Performance (Placeholders)

## 🌿 Plant Disease Model

| Model           | Accuracy | Precision | Recall | F1 Score | Notes      |
| --------------- | -------- | --------- | ------ | -------- | ---------- |
| EfficientNet-B0 | XX%      | XX        | XX     | XX       | Best model |
| ResNet50        | XX%      | XX        | XX     | XX       | Baseline   |

---

## 🌾 Crop Recommendation Model

| Model         | Accuracy | Macro F1 | Weighted F1 | Notes      |
| ------------- | -------- | -------- | ----------- | ---------- |
| Random Forest | XX%      | XX       | XX          | Baseline   |
| XGBoost       | XX%      | XX       | XX          | Best model |

---

# 🎥 Demo Video

🎬 *Placeholder — Add video link here*

---

# 🧪 Datasets

### 🌿 Plant Disease Dataset

* PlantVillage
* ~50,000 images
* 38 classes

### 🌾 Crop Recommendation Dataset

* 2,200+ rows
* 22 crops

---

# 🛠️ Tech Stack

**Frontend:** Vercel (React)
**Backend:** FastAPI / Python
**ML:** PyTorch, Scikit-Learn
**Deployment:** HuggingFace Spaces
**Database:** Supabase
**Tracking:** MLflow + DagsHub

---

# 📦 Deployment

### HuggingFace

Uses Dockerfile, requirements, app.py, and model weights.

### Vercel

Frontend deployment and user interface.

---

# 👩‍💻 Developer

**Mai – Data Scientist & ML Engineer** 🌿

---

# 🌟 Future Work

* Mobile App version
* Fertilizer Recommendation System
* Soil image classification
* YOLO-based leaf localization

---

*End of README* 🌿
