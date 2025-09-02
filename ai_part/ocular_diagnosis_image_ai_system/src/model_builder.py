# FILE: src/model_builder.py
import logging
import tensorflow as tf
from tensorflow.keras import layers, models

class ModelBuilder:
    def __init__(self, config: dict):
        self.config = config
        self.model_conf = config['model']
        self.img_size = config['preprocessing']['image_size']
        self.base_model = None

    def build(self) -> models.Model:
        input_shape = (self.img_size, self.img_size, 3)
        base_model_class = getattr(tf.keras.applications, self.model_conf['base_model'])
        self.base_model = base_model_class(weights=self.model_conf['weights'], include_top=False, input_shape=input_shape)

        inputs = layers.Input(shape=input_shape)
        x = self.base_model(inputs, training=False)
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dense(512, activation='relu')(x)
        x = layers.Dropout(0.5)(x)

        if self.model_conf['type'] == 'binary':
            outputs = layers.Dense(1, activation='sigmoid', dtype='float32')(x)
        else:
            num_classes = len(self.config['data']['class_names'])
            outputs = layers.Dense(num_classes, activation='softmax', dtype='float32')(x)
        
        model = models.Model(inputs=inputs, outputs=outputs)
        logging.info(f"تم بناء النموذج بنجاح بنوع '{self.model_conf['type']}'.")
        model.summary(line_length=110)
        return model

    def set_base_model_trainable(self, trainable: bool, unfreeze_layers: int = 0):
        if not self.base_model: raise RuntimeError("يجب بناء النموذج أولاً.")
        self.base_model.trainable = trainable
        if trainable and unfreeze_layers > 0:
            for layer in self.base_model.layers[:-unfreeze_layers]: layer.trainable = False
            for layer in self.base_model.layers[-unfreeze_layers:]: layer.trainable = True
            logging.info(f"تم فك تجميد آخر {unfreeze_layers} طبقة في النموذج الأساسي.")
        else: logging.info(f"تم {'فك تجميد' if trainable else 'تجميد'} النموذج الأساسي بالكامل.")