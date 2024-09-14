import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import numpy as np
import os
import json

# Load the trained feature extractor
model = load_model('art_feature_extractor.h5')

def get_embedding(img_path):
    img = load_img(img_path, target_size=(224, 224))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    return model.predict(img_array).flatten().tolist()

# Generate embeddings for all images
embeddings = {}
image_dir = '../crawler/belvedere_images'
for img_name in os.listdir(image_dir):
    if img_name.endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(image_dir, img_name)
        embeddings[img_name] = get_embedding(img_path)

# Save embeddings to a JSON file
with open('art_embeddings.json', 'w') as f:
    json.dump(embeddings, f)

print(f"Embeddings generated for {len(embeddings)} images and saved to art_embeddings.json")