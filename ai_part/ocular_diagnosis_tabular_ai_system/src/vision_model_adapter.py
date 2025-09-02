# FILE: src/vision_model_adapter.py

import logging
import tensorflow as tf
from tensorflow.keras import layers, models

class VisionModelAdapter:
    """
    محول مسؤول عن بناء وتحميل النماذج الصورية بشكل مستقل.
    """
    @staticmethod
    def build_and_load_binary_model(weights_path: str, image_size: int = 224) -> tf.keras.Model:
        base_model = tf.keras.applications.ResNet50(weights=None, include_top=False, input_shape=(image_size, image_size, 3))
        base_model.trainable = False
        
        inputs = layers.Input(shape=(image_size, image_size, 3))
        x = base_model(inputs, training=False)
        x = layers.GlobalAveragePooling2D()(x)
        outputs = layers.Dense(1, activation='sigmoid')(x)
        
        model = models.Model(inputs=inputs, outputs=outputs)
        model.load_weights(weights_path)
        logging.info(f"تم بناء وتحميل نموذج ثنائي من: {weights_path}")
        return model

    @staticmethod
    def load_multi_class_model(model_path: str) -> tf.keras.Model:
        logging.info(f"تحميل نموذج متعدد الفئات من: {model_path}")
        return tf.keras.models.load_model(model_path)