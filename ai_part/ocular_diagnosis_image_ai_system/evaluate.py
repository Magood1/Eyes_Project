# FILE: evaluate.py
import os
import logging
import argparse
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

from src.utils import load_config, setup_logging, validate_config
from src.data_handler import DataHandler
from src.model_builder import ModelBuilder


def evaluate(config_path: str, weights_path: str = None, saved_model_path: str = None):
    setup_logging()
    config = load_config(config_path)
    validate_config(config)

    model_type = config['model']['type']

    if weights_path:
        logging.info("إعادة بناء النموذج وتحميل الأوزان...")
        model_builder = ModelBuilder(config)
        model = model_builder.build()
        model.load_weights(weights_path)

    elif saved_model_path:
        logging.info(f"تحميل النموذج الكامل من: {saved_model_path}")
        model = tf.keras.models.load_model(saved_model_path)

    else:
        raise ValueError("يجب توفير إما --weights أو --saved_model.")

    data_handler = DataHandler(config)
    _, _, test_ds = data_handler.get_datasets_and_metadata()

    if not any(True for _ in test_ds):
        logging.error("مجموعة بيانات الاختبار فارغة.")
        return

    y_pred_probs = model.predict(test_ds)

    if model_type == 'binary':
        y_pred = (y_pred_probs > 0.5).astype(int).flatten()
        y_true = np.concatenate([y.numpy() for _, y in test_ds], axis=0).flatten()
        target_names = ["Normal", config['binary_task']['disease_name']]

    else:
        y_pred = np.argmax(y_pred_probs, axis=1)
        y_true = np.concatenate([np.argmax(y, axis=1) for _, y in test_ds], axis=0)
        target_names = config['data']['class_names']

    report = classification_report(
        y_true, y_pred,
        target_names=target_names,
        zero_division=0
    )

    print("\n--- تقرير التصنيف ---\n", report)

    output_dir = os.path.dirname(weights_path or saved_model_path)
    with open(os.path.join(output_dir, "evaluation_report.txt"), 'w') as f:
        f.write(report)

    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm, annot=True, fmt='d',
        xticklabels=target_names,
        yticklabels=target_names,
        cmap='Blues'
    )
    plt.title("Confusion Matrix")
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.savefig(os.path.join(output_dir, "confusion_matrix.png"))

    logging.info(f"تم حفظ مخرجات التقييم في: {output_dir}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate a trained model.")
    parser.add_argument("--config", required=True, help="Path to config YAML.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--weights", help="Path to trained .h5 model weights.")
    group.add_argument("--saved_model", help="Path to trained SavedModel directory.")

    args = parser.parse_args()
    evaluate(args.config, args.weights, args.saved_model)
