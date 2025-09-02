# FILE: src/trainer.py
import os
import logging
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, TensorBoard, CSVLogger

class ModelTrainer:
    def __init__(self, model_builder: 'ModelBuilder', config: dict):
        self.model_builder = model_builder
        self.model = model_builder.build()
        self.config = config
        self.run_dir = os.path.join(config['artifacts']['output_dir'], config['artifacts']['run_name'])
        os.makedirs(self.run_dir, exist_ok=True)

    def _get_callbacks(self, stage_name: str):
        stage_dir = os.path.join(self.run_dir, stage_name)
        return [
            ModelCheckpoint(filepath=os.path.join(stage_dir, "best_model.keras"), monitor='val_accuracy', save_best_only=True, mode='max'),
            EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
            TensorBoard(log_dir=os.path.join(stage_dir, "logs")),
            CSVLogger(os.path.join(stage_dir, "epoch_log.csv"))
        ]

    def _compile_model(self, lr: float):
        optimizer_name = self.config['training']['optimizer'].lower()
        if optimizer_name == 'adam': optimizer = tf.keras.optimizers.Adam(learning_rate=lr)
        else: optimizer = tf.keras.optimizers.SGD(learning_rate=lr, momentum=0.9)
        self.model.compile(optimizer=optimizer, loss=self.config['training']['loss_function'], metrics=self.config['training']['metrics'])

    def train(self, train_ds: tf.data.Dataset, val_ds: tf.data.Dataset):
        strategy_conf = self.config['training_strategy']
        if strategy_conf['stage_1']['enabled']:
            logging.info("\n" + "="*50 + "\n--- بدء المرحلة الأولى: تدريب المصنف ---\n" + "="*50)
            self.model_builder.set_base_model_trainable(False)
            self._compile_model(lr=strategy_conf['stage_1']['base_lr'])
            self.model.fit(train_ds, validation_data=val_ds, epochs=strategy_conf['stage_1']['epochs'], callbacks=self._get_callbacks("stage_1"))

        if strategy_conf['stage_2']['enabled']:
            logging.info("\n" + "="*50 + "\n--- بدء المرحلة الثانية: الضبط الدقيق ---\n" + "="*50)
            self.model_builder.set_base_model_trainable(True, strategy_conf['stage_2']['unfreeze_layers'])
            stage2_lr = strategy_conf['stage_1']['base_lr'] * strategy_conf['stage_2']['lr_multiplier']
            self._compile_model(lr=stage2_lr)
            initial_epoch = strategy_conf['stage_1']['epochs'] if strategy_conf['stage_1']['enabled'] else 0
            self.model.fit(train_ds, validation_data=val_ds, epochs=initial_epoch + strategy_conf['stage_2']['epochs'], initial_epoch=initial_epoch, callbacks=self._get_callbacks("stage_2"))
        
        model_path = os.path.join(self.run_dir, "final_model.keras")
        self.model.save(model_path)
        logging.info(f"تم حفظ النموذج المدرب النهائي في: {model_path}")