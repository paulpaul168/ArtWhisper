import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
import os
import pandas as pd
from sklearn.model_selection import train_test_split
import numpy as np

# Print out the contents of the image directory
image_dir = '../crawler/belvedere_images'
print(f"Contents of {image_dir}:")
for root, dirs, files in os.walk(image_dir):
    level = root.replace(image_dir, '').count(os.sep)
    indent = ' ' * 4 * (level)
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 4 * (level + 1)
    for f in files:
        print(f"{subindent}{f}")

# Create a dataframe with image filenames
image_files = [f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
df = pd.DataFrame({
    'filename': image_files,
    'class': ['image'] * len(image_files)  # We're not doing classification, so use a dummy class
})

# Split the data into train and validation
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

# Set up data generators
train_datagen = ImageDataGenerator(
    preprocessing_function=tf.keras.applications.efficientnet.preprocess_input,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    validation_split=0.2
)

# Define batch size
BATCH_SIZE = 32

train_generator = train_datagen.flow_from_dataframe(
    dataframe=train_df,
    directory=image_dir,
    x_col='filename',
    y_col='class',
    target_size=(224, 224),
    batch_size=BATCH_SIZE,
    class_mode='input'  # This will return the images as both x and y
)

validation_generator = train_datagen.flow_from_dataframe(
    dataframe=val_df,
    directory=image_dir,
    x_col='filename',
    y_col='class',
    target_size=(224, 224),
    batch_size=BATCH_SIZE,
    class_mode='input'
)

# Load pre-trained EfficientNetB0 without top layers
base_model = EfficientNetB0(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# Freeze the base model layers
base_model.trainable = False

# Add custom layers for feature extraction
model = tf.keras.Sequential([
    base_model,
    GlobalAveragePooling2D(),
    Dense(256, activation='relu'),
    Dropout(0.5),
    Dense(128, activation=None, name="embedding")  # 128-dimensional embedding
])

# Triplet loss function
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

# Compile the model
model.compile(optimizer='adam', loss=triplet_loss)

# Custom data generator for triplets
def triplet_generator(generator):
    while True:
        batch_x, _ = next(generator)
        anchor = batch_x
        positive = np.roll(batch_x, 1, axis=0)
        negative = np.roll(batch_x, -1, axis=0)
        yield tf.concat([anchor, positive, negative], axis=0), np.zeros((BATCH_SIZE,))  # Dummy labels

# Create triplet generators
train_triplet_gen = triplet_generator(train_generator)
val_triplet_gen = triplet_generator(validation_generator)

# Train the model
history = model.fit(
    train_triplet_gen,
    steps_per_epoch=len(train_generator),
    validation_data=val_triplet_gen,
    validation_steps=len(validation_generator),
    epochs=50,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(factor=0.2, patience=5)
    ]
)

# Fine-tune the model
base_model.trainable = True
for layer in base_model.layers[:-20]:
    layer.trainable = False

model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5), loss=triplet_loss)

history_fine_tune = model.fit(
    train_triplet_gen,
    steps_per_epoch=len(train_generator),
    validation_data=val_triplet_gen,
    validation_steps=len(validation_generator),
    epochs=30,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(factor=0.2, patience=5)
    ]
)

# Save the embedding model
model.save('art_feature_extractor.h5')