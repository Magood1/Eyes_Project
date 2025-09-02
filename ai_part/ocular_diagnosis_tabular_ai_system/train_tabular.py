# FILE: train_tabular.py

import argparse
import logging
from src.utils import load_config, setup_logging, setup_environment
from src.tabular_data_handler import TabularDataHandler
from src.tabular_model_builder import TabularModelBuilder
from src.tabular_trainer import TabularTrainer

def main(config_path: str):
    setup_logging()
    config = load_config(config_path)
    setup_environment(config['environment'])
    
    data_handler = TabularDataHandler(config)
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = data_handler.get_data_splits()
    
    builder = TabularModelBuilder(config)
    model = builder.build(input_shape=(X_train.shape[1],))
    
    trainer = TabularTrainer(model, config)
    trainer.train((X_train, y_train), (X_val, y_val))
    
    logging.info("تقييم نهائي على مجموعة الاختبار...")
    results = trainer.model.evaluate(X_test, y_test, return_dict=True, verbose=0)
    logging.info(f"النتائج النهائية -> {results}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a tabular diagnosis model.")
    parser.add_argument("--config", required=True, help="Path to tabular training config.")
    args = parser.parse_args()
    main(args.config)