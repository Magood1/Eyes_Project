# FILE: src/tabular_model_builder.py

from tensorflow.keras import layers, models, regularizers

def _resnet_block(x, units, l2_reg, dropout_rate):
    shortcut = x
    x = layers.Dense(units, kernel_regularizer=regularizers.l2(l2_reg))(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    x = layers.Dropout(dropout_rate)(x)
    x = layers.Dense(units, kernel_regularizer=regularizers.l2(l2_reg))(x)
    x = layers.BatchNormalization()(x)
    if shortcut.shape[-1] != units:
        shortcut = layers.Dense(units, kernel_regularizer=regularizers.l2(l2_reg))(shortcut)
    x = layers.Add()([x, shortcut])
    x = layers.ReLU()(x)
    return x

class TabularModelBuilder:
    def __init__(self, config: dict):
        self.config = config['model']
        self.num_classes = len(config['data']['target_columns'])

    def build(self, input_shape):
        if self.config['type'] == "TabularResNet":
            params = self.config.get('params', {})
            inputs = layers.Input(shape=input_shape)
            x = layers.BatchNormalization()(inputs)
            x = layers.Dense(params.get('initial_units', 128), activation='relu')(x)
            x = layers.Dropout(params.get('dropout_rate', 0.3))(x)
            for _ in range(params.get('num_blocks', 3)):
                x = _resnet_block(x, params.get('initial_units', 128), params.get('l2_reg', 1e-4), params.get('dropout_rate', 0.3))
            x = layers.Dense(params.get('final_units', 64), activation='relu')(x)
            outputs = layers.Dense(self.num_classes, activation='sigmoid')(x)
            return models.Model(inputs=inputs, outputs=outputs)
        # يمكن إضافة دعم لنماذج أخرى هنا
        raise ValueError(f"نوع النموذج '{self.config['type']}' غير مدعوم.")