# FILE: preprocess_to_tfrecord.py

import os
import logging
import argparse
import cv2
import numpy as np
import tensorflow as tf
from tqdm import tqdm
from src.utils import load_config, setup_logging, validate_config
from src.preprocessing_strategies import get_strategy
from src.data_handler import DataHandler # استيراد لاستخدام وظائف استخراج المسارات

def _bytes_feature(value):
    if isinstance(value, type(tf.constant(0))): value = value.numpy()
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

def serialize_example(image_np: np.ndarray, label: int) -> str:
    # ترميز الصورة كـ PNG (بدون فقدان) للحفاظ على جودة المعالجة
    is_success, buffer = cv2.imencode(".png", cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR))
    if not is_success: raise RuntimeError("فشل ترميز الصورة إلى PNG.")
    
    feature = {
        'image_raw': _bytes_feature(buffer.tobytes()),
        'label': _int64_feature(label),
    }
    example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
    return example_proto.SerializeToString()

def main(config_path: str):
    setup_logging()
    config = load_config(config_path)
    validate_config(config)
    
    data_handler = DataHandler(config)
    strategy = get_strategy(config['preprocessing']['preprocessing_strategy'], config['preprocessing']['image_size'])
    
    # تحديد مجلد المخرجات بناءً على اسم التجربة
    output_dir = os.path.join("data/tfrecords", config['artifacts']['run_name'])
    os.makedirs(output_dir, exist_ok=True)

    patient_splits = data_handler._get_patient_level_splits()

    for split_name in ['train', 'val', 'test']:
        logging.info(f"بدء المعالجة لمجموعة: {split_name}")
        paths, labels = data_handler._get_paths_and_labels(patient_splits[split_name])
        
        if not paths:
            logging.warning(f"لا توجد بيانات لمجموعة '{split_name}'.")
            continue

        output_filename = os.path.join(output_dir, f"{split_name}.tfrecord")
        with tf.io.TFRecordWriter(output_filename) as writer:
            for path, label in tqdm(zip(paths, labels), total=len(paths), desc=f"Processing {split_name}"):
                try:
                    image_np = cv2.imread(path)
                    if image_np is None: continue
                    
                    processed_np = strategy.apply(image_np)
                    
                    final_label = int(label) if config['model']['type'] == 'binary' else int(np.argmax(label))
                    example = serialize_example(processed_np, final_label)
                    writer.write(example)
                except Exception as e:
                    logging.warning(f"فشل معالجة الصورة {path}: {e}")

    logging.info(f"اكتملت المعالجة. تم حفظ ملفات TFRecord في: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess images to TFRecord format.")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML.")
    args = parser.parse_args()
    main(args.config)