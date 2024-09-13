import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
import os
import json

# Load the trained model
model = load_model('art_recognition_model.h5')

# Create a new model that outputs the embedding
embedding_model = tf.keras.Model(inputs=model.input, outputs=model.layers[-2].output)

def get_embedding(img_path):
    img = load_img(img_path, target_size=(224, 224))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0  # Normalize
    return embedding_model.predict(img_array).flatten().tolist()

# Generate embeddings for all images
embeddings = {}
for img_name in os.listdir('../crawler/belvedere_images'):
    if img_name.endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join('../crawler/belvedere_images', img_name)
        embeddings[img_name] = get_embedding(img_path)

# Save embeddings to a JSON file
with open('art_embeddings.json', 'w') as f:
    json.dump(embeddings, f)