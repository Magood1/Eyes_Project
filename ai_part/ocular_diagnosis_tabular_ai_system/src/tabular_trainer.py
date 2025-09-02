# FILE: src/tabular_trainer.py
# (هذا الملف مشابه جدًا لـ trainer.py من المشروع السابق، مما يثبت نجاح التصميم)
import os, logging, tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau

class TabularTrainer:
    def __init__(self, model, config: dict):
        self.model = model
        self.config = config
        self.run_dir = os.path.join(config['artifacts']['output_dir'], config['artifacts']['run_name'])
        os.makedirs(self.run_dir, exist_ok=True)

    def _get_callbacks(self):
        cb_conf = self.config['training']['callbacks']
        callbacks = [
            ModelCheckpoint(
                filepath=os.path.join(self.run_dir, "best_model_weights.h5"),
                monitor=cb_conf['early_stopping']['monitor'],
                save_best_only=True,
                save_weights_only=True,
                mode=cb_conf['early_stopping']['mode']
            ),
            EarlyStopping(**cb_conf['early_stopping']),
            ReduceLROnPlateau(**cb_conf['reduce_lr'])
        ]
        return callbacks

    def _compile_model(self):
        opt_conf = self.config['training']['optimizer']
        optimizer = tf.keras.optimizers.get({'class_name': opt_conf['name'], 'config': {'learning_rate': opt_conf['learning_rate']}})
        self.model.compile(
            optimizer=optimizer,
            loss=self.config['training']['loss_function'],
            metrics=self.config['training']['metrics']
        )

    def train(self, train_data, val_data):
        self._compile_model()
        logging.info("بدء تدريب النموذج الجدولي...")
        self.model.fit(
            train_data[0], train_data[1],
            validation_data=val_data,
            epochs=self.config['training']['epochs'],
            batch_size=self.config['training']['batch_size'],
            callbacks=self._get_callbacks(),
            verbose=1
        )
        logging.info("اكتمل التدريب.")