# FILE: ocular_diagnosis_tabular/src/utils.py

import os
import sys
import yaml
import logging
import random
import numpy as np
import tensorflow as tf
from typing import Any, Dict

def _merge_configs(base: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
    """يدمج قواميس الإعدادات بشكل متكرر."""
    for key, value in custom.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = _merge_configs(base[key], value)
        else:
            base[key] = value
    return base

def load_config(config_path: str) -> Dict[str, Any]:
    """
    تحميل ملف تكوين YAML، مع دعم وراثة الإعدادات من ملف أساسي.
    """
    try:
        with open(config_path, 'r') as f:
            custom_config = yaml.safe_load(f)
        
        if 'imports' in custom_config and 'path' in custom_config['imports']:
            base_path = custom_config['imports']['path']
            base_config = load_config(base_path)
            return _merge_configs(base_config, custom_config)
        
        return custom_config
    except FileNotFoundError:
        logging.error(f"ملف التكوين لم يتم العثور عليه: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"خطأ في تحليل ملف YAML '{config_path}': {e}")
        sys.exit(1)

def setup_logging():
    """إعداد نظام التسجيل الأساسي."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s", stream=sys.stdout)

def setup_environment(config: dict):
    """إعداد بيئة TensorFlow لضمان قابلية إعادة الإنتاج."""
    seed = config.get('seed', 42)
    os.environ['PYTHONHASHSEED'] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    logging.info(f"تم تعيين البذور العشوائية إلى {seed}.")