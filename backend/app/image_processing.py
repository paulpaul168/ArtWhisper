import cv2
import numpy as np
import os
import uuid
import tensorflow as tf
from . import crud
from typing import List, Tuple
from typing import List
from .image_module import load_or_compute_features, index_database, match_artwork, load_images_from_folder


def triplet_loss(y_true, y_pred, alpha=0.2):
    embedding_dim = 128
    anchor, positive, negative = tf.split(y_pred, num_or_size_splits=3, axis=0)
    
    # Calculate pairwise distances
    pos_dist = tf.reduce_sum(tf.square(anchor - positive), axis=1)
    neg_dist = tf.reduce_sum(tf.square(anchor - negative), axis=1)
    
    # Calculate loss
    basic_loss = pos_dist - neg_dist + alpha
    loss = tf.maximum(basic_loss, 0.0)
    return tf.reduce_mean(loss)

def extract_artworks(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 150)
    kernel = np.ones((5,5), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    image_area = image.shape[0] * image.shape[1]
    artworks = []
    
    for contour in contours[:30]:  # Check the 30 largest contours
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if len(approx) >= 4:  # Allow for more complex shapes
            area = cv2.contourArea(approx)
            
            if 0.001 * image_area < area < 0.99 * image_area:
                rect = cv2.minAreaRect(approx)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                
                # Perspective transform
                width = int(rect[1][0])
                height = int(rect[1][1])
                src_pts = box.astype("float32")
                dst_pts = np.array([[0, height-1],
                                    [0, 0],
                                    [width-1, 0],
                                    [width-1, height-1]], dtype="float32")
                M = cv2.getPerspectiveTransform(src_pts, dst_pts)
                warped = cv2.warpPerspective(image, M, (width, height))
                
                # Check aspect ratio
                aspect_ratio = min(width, height) / max(width, height)
                if aspect_ratio > 0.2:  # Allow more variation in aspect ratio
                    artworks.append((warped, box))
    
    return artworks

def order_points(pts):
    # Initialize a list of coordinates that will be ordered
    rect = np.zeros((4, 2), dtype="float32")
    
    # The top-left point will have the smallest sum
    # The bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Compute the difference between the points
    # The top-right point will have the smallest difference
    # The bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect


def process_image(image_contents: bytes) -> Tuple[List[np.ndarray], np.ndarray]:
    temp_folder = "temp_debug_images"
    os.makedirs(temp_folder, exist_ok=True)
    unique_filename = f"{uuid.uuid4()}"
    original_image_path = os.path.join(temp_folder, f"{unique_filename}_original.jpg")

    nparr = np.frombuffer(image_contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    cv2.imwrite(original_image_path, image)
    
    artworks = extract_artworks(image)
    processed_artworks = []
    
    for idx, (artwork, box) in enumerate(artworks):
        artwork_rgb = cv2.cvtColor(artwork, cv2.COLOR_BGR2RGB)
        artwork_resized = cv2.resize(artwork_rgb, (224, 224))
        processed_artworks.append(artwork_resized)
        
        # Save debug image with bounding box
        debug_image = image.copy()
        cv2.drawContours(debug_image, [box], 0, (0, 255, 0), 2)
        cv2.putText(debug_image, f"ID: {idx}", (box[0][0], box[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        debug_image_path = os.path.join(temp_folder, f"{unique_filename}_debug_{idx}.jpg")
        cv2.imwrite(debug_image_path, debug_image)
    
    return processed_artworks, image

def calculate_embeddings(image_contents: bytes) -> List[List[float]]:
    processed_artworks, _ = process_image(image_contents)
    embeddings = []
    
    for artwork in processed_artworks:
        artwork_tensor = tf.convert_to_tensor(artwork, dtype=tf.float32)
        artwork_tensor = tf.expand_dims(artwork_tensor, axis=0)
        artwork_tensor = artwork_tensor / 255.0
        embedding = model.predict(artwork_tensor)
        embeddings.append(np.array(embedding[0]).tolist())
    
    return embeddings

def find_similar_artwork(query_image: np.ndarray, database_images: List[Tuple[np.ndarray, str]], kmeans, index) -> dict:
    best_match_index = match_artwork(query_image, database_images, kmeans, index)
    
    if best_match_index is not None:
        matched_image_name = database_images[best_match_index][1]
        return {
            "artwork_id": best_match_index,
            "similar_artwork_id": matched_image_name,
            "similarity": 1.0  # We don't have a similarity score from match_artwork, so we use 1.0 for the best match
        }
    else:
        return None

def test_image_processing():
    test_image_folder = 'test_images'
    database_folder = '../crawler/belvedere_images'
    
    # Load database images
    database_images = load_images_from_folder(database_folder)
    
    if not database_images:
        print(f"No images found in the database folder: {database_folder}")
        return

    # Index the database
    kmeans, index = index_database(database_images)

    test_image_files = [f for f in os.listdir(test_image_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]

    for test_image_file in test_image_files:
        test_image_path = os.path.join(test_image_folder, test_image_file)
        print(f"\nProcessing image: {test_image_file}")

        with open(test_image_path, 'rb') as f:
            image_contents = f.read()
        
        processed_artworks, _ = process_image(image_contents)
        
        print(f"Number of artworks detected: {len(processed_artworks)}")

        for idx, artwork in enumerate(processed_artworks):
            result = find_similar_artwork(artwork, database_images, kmeans, index)

            if result:
                print(f"\nMost Similar Artwork Found for Artwork {idx}:")
                print(f"Similar Artwork ID: {result['similar_artwork_id']}")
                print(f"Similarity: {result['similarity']:.4f}")
            else:
                print(f"\nNo match found for Artwork {idx}")

if __name__ == "__main__":
    test_image_processing()