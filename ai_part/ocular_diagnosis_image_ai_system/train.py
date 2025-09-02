# FILE: train.py

import argparse
import logging
from src.utils import load_config, setup_environment, setup_logging, validate_config
from src.data_handler import DataHandler
from src.model_builder import ModelBuilder
from src.trainer import ModelTrainer

def main(config_path: str):
    setup_logging()
    config = load_config(config_path)
    validate_config(config)
    
    setup_environment(config['environment'])
    
    data_handler = DataHandler(config)
    datasets, metadata = data_handler.get_datasets_and_metadata()
    
    class_weights = None
    if config['training'].get('use_class_weights', False):
        class_weights = data_handler.get_class_weights(metadata['train']['labels'])
    
    model_builder = ModelBuilder(config)
    
    trainer = ModelTrainer(model_builder, config)
    trainer.train(datasets, metadata, class_weights=class_weights)
    
    logging.info("تقييم نهائي على مجموعة الاختبار...")
    if metadata['test']['size'] > 0:
        results = trainer.model.evaluate(datasets['test'], return_dict=True, verbose=0)
        logging.info(f"النتائج النهائية على مجموعة الاختبار -> {results}")
    
    logging.info("اكتمل المسار بنجاح.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train an ocular disease classification model.")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML.")
    args = parser.parse_args()
    main(args.config)