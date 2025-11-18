# 🌿 **Flora – Smart Farming Companion**  

### *AI-Powered Plant Disease Detection & Crop Recommendation System for Sustainable Agriculture*

---

## 📖 Overview

**Flora** is an intelligent agricultural assistant designed to empower **farmers, home gardeners, and agricultural students** with AI-driven insights. By combining deep learning and machine learning, Flora helps users:

- 🌿 **Detect plant diseases** from leaf images in real-time
- 🌾 **Recommend optimal crops** based on soil and climate conditions
- 📊 **Track farming data** for better decision-making

Our mission is to make agriculture more **accessible, efficient, and sustainable**—especially for those with limited expertise or resources.

---

## 🌐 Live Demos

| Platform | Description | Link |
|----------|-------------|------|
| **🌱 Plant Disease Detection** | Upload a leaf image and get instant diagnosis | [Hugging Face Space](https://huggingface.co/spaces/Mai-22/plant-disease-detection) |
| **🌾 Crop Recommendation** | Input soil/climate parameters for crop suggestions | [Hugging Face Space](https://huggingface.co/spaces/Mai-22/Crop-Recommendation-deployment) |
| **🚀 Web Application** | Full-stack application with user-friendly interface | [Vercel Deployment](https://flora-81nw.vercel.app/home) |

---

## 📊 Model Performance & Experiment Tracking

All experiments, model versions, and performance metrics are tracked using **MLflow** and hosted on **DagsHub**:

🔗 **Experiment Dashboard:** [https://dagshub.com/maimohamed201526/plant-disease-project](https://dagshub.com/maimohamed201526/plant-disease-project)

---

## 🗃️ Database & Infrastructure

- **Database:** [Supabase](https://supabase.com/dashboard/project/onnbpuqxtmdddbksfgrt)
- **Model Hosting:** Hugging Face Spaces
- **Frontend Hosting:** Vercel
- **Version Control:** Git & DagsHub

---

## 🎯 Key Features

### 🔍 Plant Disease Detection
- **Model:** EfficientNet-B0 fine-tuned on PlantVillage dataset
- **Classes:** 38 plant disease categories + healthy plants
- **Real-time Inference:** < 5 seconds per image
- **Confidence Scoring:** Transparent probability estimates

### 🌾 Crop Recommendation System
- **Input Parameters:** Nitrogen (N), Phosphorus (P), Potassium (K), temperature, humidity, pH, rainfall
- **Algorithm:** Ensemble methods (Random Forest, XGBoost)
- **Output:** Top crop recommendations with suitability scores

### 🛠️ Technical Features
- **Containerized Deployment** using Docker
- **RESTful API** for easy integration
- **Responsive Web Interface**
- **Experiment Tracking** with MLflow

---

## 📈 Model Performance

### Plant Disease Detection
| Model | Accuracy | Precision | Recall | F1-Score |
|-------|----------|-----------|--------|----------|
| EfficientNet-B0 | 93.5% | 94.8% | 93.5% | 92.3% |
| ResNet-50 | 91.2% | 92.1% | 91.2% | 90.8% |

### Crop Recommendation
| Model | Accuracy | Macro F1 | Weighted F1 |
|-------|----------|----------|-------------|
| Random Forest | 99.2% | 0.992 | 0.992 |
| XGBoost | 99.1% | 0.991 | 0.991 |

---

## 📚 Dataset Information

### Plant Disease Detection
- **Source:** [PlantVillage Dataset on Kaggle](https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset)
- **Size:** ~50,000 images
- **Classes:** 38 categories (14 crop species, multiple diseases + healthy)
- **Split:** 70% train, 15% validation, 15% test

### Crop Recommendation
- **Source:** [Crop Recommendation Dataset on Kaggle](https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset)
- **Size:** 2,200+ samples
- **Features:** 7 agricultural parameters
- **Crops:** 22 different crop types

---

## 🏗️ System Architecture
graph TB
    A[User] --> B[Web Interface]
    B --> C[FastAPI Backend]
    C --> D[Plant Disease Model]
    C --> E[Crop Recommendation Model]
    D --> F[(Hugging Face Spaces)]
    E --> F
    C --> G[(Supabase Database)]
    H[MLflow Tracking] --> I[(DagsHub Repository)]
