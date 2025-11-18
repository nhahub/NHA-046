import json
import logging
import os
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from torchvision import transforms, models
import torch.nn as nn
import io

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PlantDiseaseModel:
    def __init__(self):
        self.model = None
        self.device = None
        self.categories = None
        self.transform = None

    def init(self):
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")
            
            # Load categories
            with open('categories.json', 'r') as f:
                self.categories = json.load(f)
            
            logger.info("🔍 Categories order in score.py:")
            for i, cat in enumerate(self.categories):
                logger.info(f"   {i}: {cat}")
            
            # Define transforms
            self.transform = transforms.Compose([
                transforms.Resize((128, 128)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                     std=[0.229, 0.224, 0.225])
            ])
            
            # Load model
            self.model = self._load_model()
            
            logger.info("Model initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in model initialization: {str(e)}")
            return False

    def _load_model(self):
        try:
            model_path = "best_efficientnet_b0.pth"
            logger.info(f"Loading model from: {model_path}")
            
            model = models.efficientnet_b0(weights=None)
            num_features = model.classifier[1].in_features
            model.classifier = nn.Sequential(
                nn.Dropout(p=0.6),
                nn.Linear(num_features, len(self.categories))
            )

            state_dict = torch.load(model_path, map_location=self.device)
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval()
            
            logger.info("EfficientNet-B0 model loaded successfully")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def preprocess_image(self, image_data):
        try:
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                image = Image.open(image_data)
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            image_tensor = self.transform(image).unsqueeze(0)
            return image_tensor.to(self.device)
            
        except Exception as e:
            logger.error(f"Error in image preprocessing: {str(e)}")
            raise

    def run(self, image_data):
        try:
            input_tensor = self.preprocess_image(image_data)
            
            self.model.eval()
            with torch.no_grad():
                output = self.model(input_tensor)           # logits
                probs = F.softmax(output, dim=1)            # softmax → probabilities
                
                prediction_idx = probs.argmax(dim=1).item()
                prediction_class = self.categories[prediction_idx]
                confidence = float(probs[0][prediction_idx].item())

                if "healthy" in prediction_class.lower():
                    status = "healthy"
                else:
                    status = "diseased"

                logger.info(f"Status: {status}")
                logger.info(f"Prediction class: {prediction_class}")
                logger.info(f"Confidence: {confidence:.4f}")

                # Final output
                result = {
                    "status": status,
                    "confidence": round(confidence, 4)
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            return {"error": str(e)}


# Global model instance
model = PlantDiseaseModel()

def init():
    return model.init()

def run(raw_data):
    try:
        return model.run(raw_data)
    except Exception as e:
        logger.error(f"Error in run function: {str(e)}")
        return {"error": str(e)}
