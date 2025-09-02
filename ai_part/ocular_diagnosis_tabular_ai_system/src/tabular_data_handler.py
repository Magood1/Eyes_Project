# FILE: src/tabular_data_handler.py

import pandas as pd
import logging

class TabularDataHandler:
    def __init__(self, config: dict):
        self.config = config['data']
        path = self.config['features_path']
        logging.info(f"تحميل بيانات الميزات من: {path}")
        if path.endswith('.parquet'):
            self.df = pd.read_parquet(path)
        else:
            self.df = pd.read_csv(path)
    
    def get_data_splits(self):
        train_df = self.df[self.df['split'] == 'train']
        val_df = self.df[self.df['split'] == 'val']
        test_df = self.df[self.df['split'] == 'test']
        
        feature_cols = [c for c in self.df.columns if c not in self.config['target_columns'] + ['split', 'uuid']]
        
        X_train, y_train = train_df[feature_cols].values, train_df[self.config['target_columns']].values
        X_val, y_val = val_df[feature_cols].values, val_df[self.config['target_columns']].values
        X_test, y_test = test_df[feature_cols].values, test_df[self.config['target_columns']].values
        
        return (X_train, y_train), (X_val, y_val), (X_test, y_test)