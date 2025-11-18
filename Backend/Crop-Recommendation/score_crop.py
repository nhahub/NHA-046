import warnings
warnings.filterwarnings('ignore')

import json
import logging
import pandas as pd
import numpy as np
import joblib

logger = logging.getLogger(__name__)

class CropRecommendationModel:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_columns = None
        
    def init(self):
        try:
            # Load model and preprocessing objects
            self.model = joblib.load('best_model_XGBoost.pkl')
            self.scaler = joblib.load('scaler.pkl')
            self.label_encoder = joblib.load('label_encoder.pkl')
            self.feature_columns = joblib.load('feature_names.pkl')
            
            logger.info("✅ Crop model initialized successfully")
            logger.info(f"✅ Model type: {type(self.model).__name__}")
            logger.info(f"✅ Feature columns: {len(self.feature_columns)}")
            logger.info(f"✅ Classes: {len(self.label_encoder.classes_)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in crop model initialization: {str(e)}")
            return False
    
    def preprocess_input(self, input_data):
        """Preprocess input data to match training format"""
        try:
            # Create engineered features 
            processed_data = {
                'temp_rain': input_data['temperature'] * input_data['rainfall'],
                'ph_rain': input_data['ph'] * input_data['rainfall'],
                'K': input_data['potassium'],
                'rainfall': input_data['rainfall'],
                'N': input_data['nitrogen'],
                'P': input_data['phosphorus'],
                'NPK_Avg_Soil_Fertility': (input_data['nitrogen'] + input_data['phosphorus'] + input_data['potassium']) / 3,
                'humidity': input_data['humidity'],
                'NP_Ratio': input_data['nitrogen'] / input_data['phosphorus'] if input_data['phosphorus'] != 0 else 0,
                'THI': (input_data['temperature'] * input_data['humidity']) / 100
            }
            
            # Create DataFrame with correct column order
            input_df = pd.DataFrame([processed_data], columns=self.feature_columns)
            
            # Scale the features
            scaled_features = self.scaler.transform(input_df)
            
            return scaled_features, processed_data
            
        except Exception as e:
            logger.error(f"Error in input preprocessing: {str(e)}")
            raise
    
    def run(self, input_data):
        try:
            # Preprocess input
            scaled_data, processed_features = self.preprocess_input(input_data)
            
            # Make prediction
            prediction_proba = self.model.predict_proba(scaled_data)[0]
            
            # Get ONLY the top recommendation
            top_index = np.argmax(prediction_proba)
            crop = self.label_encoder.inverse_transform([top_index])[0]
            confidence = float(prediction_proba[top_index])
            
            # Simple result 
            result = {
                "crop": crop,
                "confidence": confidence,
                "suitability": f"{confidence:.1%}",
                "processed_features": processed_features,
                "input_summary": {
                    "nitrogen": input_data['nitrogen'],
                    "phosphorus": input_data['phosphorus'], 
                    "potassium": input_data['potassium'],
                    "temperature": input_data['temperature'],
                    "humidity": input_data['humidity'],
                    "ph": input_data['ph'],
                    "rainfall": input_data['rainfall']
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error during crop prediction: {str(e)}")
            raise

# Initialize model instance
crop_model = CropRecommendationModel()

def init():
    return crop_model.init()

def run(input_data):
    try:
        result = crop_model.run(input_data)
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}
