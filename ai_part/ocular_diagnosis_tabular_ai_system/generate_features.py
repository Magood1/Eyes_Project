# FILE: generate_features.py

import os
import logging
import argparse
import pandas as pd
import numpy as np
import uuid
import cv2
from sklearn.model_selection import train_test_split
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# --- استيراد الوحدات الأساسية للمشروع ---
from src.utils import load_config, setup_logging, setup_environment
from src.config_validator import validate_feature_generation_config
from backend_logic.ai_pipeline.models.classifier import EyesModel, Diagnoser
from backend_logic.ai_pipeline.models.preprocessing import (
    CataractPreprocessing, DiabetesPreprocessing, GlaucomaPreprocessing,
    HypertensionPreprocessing, PathologicalMyopiaPreprocessing, AgeIssuesPreprocessing,
    MULTICLASSPreprocessing
)
from backend_logic.ai_pipeline.feature_extractor import create_fused_feature_vector

def preprocess_image(image_path: str, size: int) -> np.ndarray | None:
    """Loads and preprocesses a single image from a file path."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            logging.warning(f"Could not read image: {image_path}")
            return None
        # The backend logic expects BGR images, so we don't convert to RGB here.
        return img
    except Exception as e:
        logging.error(f"Error loading image {image_path}: {e}")
        return None

def main(config_path: str):
    """
    The main workflow for generating tabular features. It validates the config,
    loads all vision models, processes patient data in batches for performance,
    generates fused features, and saves the final dataset.
    """
    setup_logging()
    config = load_config(config_path)
    
    try:
        validate_feature_generation_config(config)
    except Exception:
        logging.error("Exiting due to invalid configuration.")
        return

    setup_environment(config['environment'])

    # --- 1. Setup Models as per Backend Logic ---
    logging.info("Setting up all vision models...")
    multi_class_model = EyesModel(
        model_path=config['vision_models']['multi_class'],
        strategy=MULTICLASSPreprocessing()
    )
    
    diagnoser = Diagnoser()
    strategies = [
        CataractPreprocessing(), DiabetesPreprocessing(), GlaucomaPreprocessing(),
        HypertensionPreprocessing(), PathologicalMyopiaPreprocessing(), AgeIssuesPreprocessing()
    ]
    expert_model_order = ['cataract', 'diabetes', 'glaucoma', 'hypertension', 'myopia', 'amd']
    
    for i, name in enumerate(expert_model_order):
        model_path = config['vision_models']['expert_models'].get(name)
        if not model_path:
            raise ValueError(f"Expert model path for '{name}' is missing in config.")
        diagnoser.add_model(EyesModel(model_path=model_path, strategy=strategies[i]))
        
    # --- 2. Process Data and Generate Features in Batches ---
    logging.info(f"Loading metadata from: {config['data']['csv_path']}")
    df = pd.read_excel(config['data']['csv_path'])
    df.columns = df.columns.str.strip()
    
    batch_size = 32
    all_feature_rows = []

    for i in tqdm(range(0, len(df), batch_size), desc="Generating features in batches"):
        batch_df = df.iloc[i:i + batch_size]
        
        left_images, right_images, valid_indices = [], [], []
        for idx, row in batch_df.iterrows():
            left_img = preprocess_image(os.path.join(config['data']['images_dir'], row['Left-Fundus']), config['data']['image_size'])
            right_img = preprocess_image(os.path.join(config['data']['images_dir'], row['Right-Fundus']), config['data']['image_size'])
            if left_img is not None and right_img is not None:
                left_images.append(left_img)
                right_images.append(right_img)
                valid_indices.append(idx)

        if not valid_indices:
            continue

        # --- Perform Batch Predictions ---
        with ThreadPoolExecutor() as executor:
            # Multi-class predictions
            mc_left_futures = [executor.submit(multi_class_model.predict_single, img) for img in left_images]
            mc_right_futures = [executor.submit(multi_class_model.predict_single, img) for img in right_images]
            
            # Expert predictions
            expert_futures = [executor.submit(diagnoser.predict, left, right) for left, right in zip(left_images, right_images)]

            mc_probs_left = [f.result()[0] for f in mc_left_futures]
            mc_probs_right = [f.result()[0] for f in mc_right_futures]
            expert_results_batch = [f.result() for f in expert_futures]

        # --- Fuse Features for each item in the batch ---
        for j, original_index in enumerate(valid_indices):
            row = df.loc[original_index]
            demographics = {'age': row['Patient Age'], 'gender': 1 if row['Patient Sex'] == 'Male' else 0}
            
            expert_probs_left = np.array([res[0][0] for res in expert_results_batch[j]])
            expert_probs_right = np.array([res[1][0] for res in expert_results_batch[j]])

            feature_vector = create_fused_feature_vector(
                mc_probs_left[j], mc_probs_right[j],
                expert_probs_left, expert_probs_right,
                demographics['age'], demographics['gender']
            )
            
            feature_row = {f'feature_{k}': val for k, val in enumerate(feature_vector)}
            feature_row['uuid'] = uuid.uuid4()
            for col in ['N', 'D', 'G', 'C', 'A', 'H', 'M', 'O']:
                feature_row[col] = row[col]
            all_feature_rows.append(feature_row)

    # --- 3. Save Features after Splitting ---
    if not all_feature_rows:
        logging.error("No features were generated. Please check image paths and model configurations.")
        return
        
    features_df = pd.DataFrame(all_feature_rows)
    
    logging.info("Splitting feature set into train, validation, and test sets...")
    train_val_df, test_df = train_test_split(features_df, test_size=config['output']['test_split'], random_state=config['output']['split_seed'])
    val_rel_size = config['output']['val_split'] / (1.0 - config['output']['test_split'])
    train_df, val_df = train_test_split(train_val_df, test_size=val_rel_size, random_state=config['output']['split_seed'])
    
    train_df.loc[:, 'split'] = 'train'
    val_df.loc[:, 'split'] = 'val'
    test_df.loc[:, 'split'] = 'test'
    
    final_df = pd.concat([train_df, val_df, test_df]).reset_index(drop=True)
    
    output_path = config['output']['features_path']
    logging.info(f"Saving {len(final_df)} feature vectors to: {output_path}")
    if config['output']['format'] == 'parquet':
        final_df.to_parquet(output_path, index=False)
    else:
        final_df.to_csv(output_path, index=False)
        
    logging.info("Feature generation process completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate tabular features from vision models.")
    parser.add_argument("--config", required=True, help="Path to the feature generation configuration file.")
    args = parser.parse_args()
    main(args.config)