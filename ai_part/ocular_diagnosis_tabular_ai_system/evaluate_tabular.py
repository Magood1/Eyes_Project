# FILE: evaluate_tabular.py

import os
import logging
import argparse
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, recall_score
from src.utils import load_config, setup_logging
from src.tabular_data_handler import TabularDataHandler
from src.tabular_model_builder import TabularModelBuilder

def calculate_specificity(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculates the specificity for a binary classification problem."""
    tn, fp, _, _ = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return tn / (tn + fp) if (tn + fp) > 0 else 0.0

def evaluate(config_path: str, weights_path: str):
    """
    Main evaluation workflow. Loads the test data and a trained model,
    then generates and saves a comprehensive set of performance reports,
    including medical-grade metrics like sensitivity and specificity.
    """
    setup_logging()
    config = load_config(config_path)
    
    # 1. Load Test Data
    data_handler = TabularDataHandler(config)
    _, _, (X_test, y_test) = data_handler.get_data_splits()
    if X_test.shape[0] == 0:
        logging.error("Test dataset is empty. Aborting evaluation.")
        return

    # 2. Rebuild Model and Load Weights
    logging.info("Rebuilding model and loading weights for evaluation...")
    builder = TabularModelBuilder(config)
    model = builder.build(input_shape=(X_test.shape[1],))
    model.load_weights(weights_path)
    
    # 3. Perform Predictions
    logging.info("Performing predictions on the test set...")
    y_pred_probs = model.predict(X_test)
    y_pred_binary = (y_pred_probs > 0.5).astype(int)
    
    # 4. Generate and Save Reports
    target_names = config['data']['target_columns']
    output_dir = os.path.dirname(weights_path)
    
    # --- Standard Classification Report ---
    base_report = classification_report(y_test, y_pred_binary, target_names=target_names, zero_division=0)
    
    # --- Medical-Grade Metrics Report ---
    medical_metrics_report = "\n\n--- Detailed Medical Metrics ---\n"
    medical_metrics_report += f"{'Disease':<15} | {'Sensitivity (Recall)':<25} | {'Specificity':<15}\n"
    medical_metrics_report += "-" * 65 + "\n"
    
    for i, name in enumerate(target_names):
        sensitivity = recall_score(y_test[:, i], y_pred_binary[:, i], zero_division=0)
        specificity = calculate_specificity(y_test[:, i], y_pred_binary[:, i])
        medical_metrics_report += f"{name:<15} | {sensitivity:<25.4f} | {specificity:<15.4f}\n"

    # --- ROC AUC Scores ---
    try:
        auc_macro = roc_auc_score(y_test, y_pred_probs, average='macro')
        auc_weighted = roc_auc_score(y_test, y_pred_probs, average='weighted')
        auc_report = f"\n--- ROC AUC Scores ---\n"
        auc_report += f"Macro Average: {auc_macro:.4f}\n"
        auc_report += f"Weighted Average: {auc_weighted:.4f}\n"
    except ValueError as e:
        auc_report = f"\n--- ROC AUC Scores ---\nCould not compute ROC AUC: {e}\n"

    # --- Combine and Save Full Report ---
    full_report = f"--- General Classification Report ---\n{base_report}{medical_metrics_report}{auc_report}"
    print(full_report)
    
    report_path = os.path.join(output_dir, "evaluation_full_report.txt")
    with open(report_path, 'w') as f:
        f.write(full_report)
    logging.info(f"Full evaluation report saved to: {report_path}")

    # 5. Generate and Save Confusion Matrices for Each Class
    logging.info("Generating confusion matrices for each disease class...")
    for i, name in enumerate(target_names):
        cm = confusion_matrix(y_test[:, i], y_pred_binary[:, i], labels=[0, 1])
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Negative', 'Positive'], yticklabels=['Negative', 'Positive'])
        plt.title(f"Confusion Matrix for: {name}")
        plt.ylabel('Actual Label')
        plt.xlabel('Predicted Label')
        cm_path = os.path.join(output_dir, f"confusion_matrix_{name}.png")
        plt.savefig(cm_path)
        plt.close() # Close the figure to free up memory

    logging.info(f"All evaluation artifacts have been saved to: {output_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate a trained tabular model with detailed medical metrics.")
    parser.add_argument("--config", required=True, help="Path to the tabular training configuration file.")
    parser.add_argument("--weights", required=True, help="Path to the trained .h5 model weights file.")
    args = parser.parse_args()
    evaluate(args.config, args.weights)