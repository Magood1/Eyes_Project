# FILE: src/data_handler.py

import os
import logging
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from src.preprocessing_strategies import get_strategy

class DataHandler:
    def __init__(self, config: dict):
        self.config = config
        self.data_conf = config['data']
        self.pipeline_conf = config['pipeline']
        self.prep_conf = config['preprocessing']
        self.model_type = config['model']['type']
        
        self.df = pd.read_excel(self.data_conf['csv_path'])
        self.df.columns = self.df.columns.str.strip()
        self.img_size = self.prep_conf['image_size']
        self.strategy = get_strategy(self.prep_conf['preprocessing_strategy'])

    def _get_patient_level_splits(self):
        patient_ids = self.df['Patient ID'].unique()
        test_size, val_size = self.prep_conf['test_split'], self.prep_conf['validation_split']
        train_val_ids, test_ids = train_test_split(patient_ids, test_size=test_size, random_state=42)
        relative_val_size = val_size / (1 - test_size)
        train_ids, val_ids = train_test_split(train_val_ids, test_size=relative_val_size, random_state=42)
        return {'train': train_ids, 'val': val_ids, 'test': test_ids}
        
    def _get_paths_and_labels(self, patient_ids):
        if self.model_type == 'binary':
            return self._get_binary_paths_and_labels(patient_ids)
        return self._get_multi_class_paths_and_labels(patient_ids)

    def _get_multi_class_paths_and_labels(self, patient_ids):
        split_df = self.df[self.df['Patient ID'].isin(patient_ids)]
        paths, labels = [], []
        label_df = split_df[self.data_conf['class_names']]
        for index, row in split_df.iterrows():
            for side in ['Left', 'Right']:
                filepath = os.path.join(self.data_conf['images_dir'], row[f'{side}-Fundus'])
                if os.path.exists(filepath):
                    paths.append(filepath)
                    labels.append(label_df.loc[index].values.astype('float32'))
        return paths, labels

    def _get_binary_paths_and_labels(self, patient_ids):
        task_conf = self.config['binary_task']
        logging.info(f"إنشاء مجموعة بيانات ثنائية لـ: '{task_conf['disease_name']}'")
        split_df = self.df[self.df['Patient ID'].isin(patient_ids)]
        pos_paths, neg_paths = [], []
        keywords = task_conf['positive_keywords']

        for _, row in split_df.iterrows():
            diag_text = f"{row['Left-Diagnostic Keywords']} {row['Right-Diagnostic Keywords']}"
            is_positive = any(k.lower() in diag_text.lower() for k in keywords)
            is_normal = 'normal fundus' in str(row['Left-Diagnostic Keywords']) and 'normal fundus' in str(row['Right-Diagnostic Keywords'])

            for side in ['Left', 'Right']:
                filepath = os.path.join(self.data_conf['images_dir'], row[f'{side}-Fundus'])
                if os.path.exists(filepath):
                    if is_positive: pos_paths.append(filepath)
                    elif is_normal: neg_paths.append(filepath)
        
        pos_paths, neg_paths = sorted(list(set(pos_paths))), sorted(list(set(neg_paths)))
        if self.pipeline_conf.get('balance_classes'):
            min_samples = min(len(pos_paths), len(neg_paths))
            pos_paths, neg_paths = pos_paths[:min_samples], neg_paths[:min_samples]
        
        logging.info(f"الحالات الإيجابية: {len(pos_paths)}, الحالات السلبية: {len(neg_paths)}")
        paths = pos_paths + neg_paths
        labels = [1.0] * len(pos_paths) + [0.0] * len(neg_paths)
        return paths, labels

    def _process_image(self, path, label):
        image_data = tf.io.read_file(path)
        image = tf.image.decode_jpeg(image_data, channels=3)
        
        # تطبيق استراتيجية المعالجة المسبقة
        processed_image = tf.py_function(
            func=self.strategy.apply, inp=[image], Tout=tf.float32
        )
        processed_image.set_shape([self.img_size, self.img_size, 3])
        return processed_image, label

    def get_datasets(self):
        patient_splits = self._get_patient_level_splits()
        datasets = {}
        AUTOTUNE = tf.data.AUTOTUNE
        for name in ['train', 'val', 'test']:
            paths, labels = self._get_paths_and_labels(patient_splits[name])
            if not paths:
                datasets[name] = tf.data.Dataset.from_tensor_slices(([], []))
                continue
            
            ds = tf.data.Dataset.from_tensor_slices((paths, labels))
            if name == 'train': ds = ds.shuffle(len(paths))
            
            ds = ds.map(self._process_image, num_parallel_calls=AUTOTUNE)
            if self.pipeline_conf.get('use_cache'): ds = ds.cache()
            
            ds = ds.batch(self.config['training']['batch_size'])
            if self.pipeline_conf.get('use_prefetch'): ds = ds.prefetch(AUTOTUNE)
            
            datasets[name] = ds
            logging.info(f"تم إنشاء مجموعة بيانات '{name}' مع {len(paths)} صورة.")
        return datasets['train'], datasets['val'], datasets['test']