import os
os.environ["KERAS_BACKEND"] = "tensorflow"

import keras
from keras import layers
from custom_layers import Patches, PatchEncoder

# Create a simple model to test the custom layers
def create_test_model():
    inputs = keras.Input(shape=(224, 224, 3))
    
    # Create patches
    patches = Patches(patch_size=16)(inputs)
    
    # Encode patches
    encoded_patches = PatchEncoder(num_patches=196, projection_dim=64)(patches)
    
    # Add transformer layers
    x = encoded_patches
    for _ in range(2):
        # Multi-head attention
        attention_output = layers.MultiHeadAttention(
            num_heads=8, key_dim=64, dropout=0.1
        )(x, x)
        x = layers.LayerNormalization(epsilon=1e-6)(x + attention_output)
        
        # Feed forward
        ffn = keras.Sequential([
            layers.Dense(256, activation="gelu"),
            layers.Dropout(0.1),
            layers.Dense(64),
        ])
        ffn_output = ffn(x)
        x = layers.LayerNormalization(epsilon=1e-6)(x + ffn_output)
    
    # Global average pooling
    representation = layers.GlobalAveragePooling1D()(x)
    
    # Classification head
    outputs = layers.Dense(10, activation="softmax")(representation)
    
    model = keras.Model(inputs, outputs)
    return model

if __name__ == "__main__":
    print("Creating test model...")
    model = create_test_model()
    
    # Compile the model
    model.compile(
        optimizer=keras.optimizers.AdamW(learning_rate=0.001),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    
    print("Model created successfully!")
    print(f"Model summary:\n{model.summary()}")
    
    # Save the model
    model.save("vision_transformer_model/model/my_model.keras")
    print("Model saved successfully!")
