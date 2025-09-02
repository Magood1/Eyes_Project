# FILE: tests/test_end_to_end.py

import pytest
import pandas as pd
import numpy as np
from src.utils import load_config
from src.tabular_data_handler import TabularDataHandler
from src.tabular_model_builder import TabularModelBuilder

@pytest.fixture
def config():
    """تحميل تكوين التدريب الجدولي."""
    return load_config("configs/2_tabular_training_config.yaml")

def test_feature_shape_consistency(config):
    """
    اختبار تكامل: التحقق من أن عدد الميزات في البيانات
    يطابق شكل الإدخال المتوقع للنموذج.
    """
    # 1. تحميل البيانات
    data_handler = TabularDataHandler(config)
    (X_train, _), _, _ = data_handler.get_data_splits()
    
    num_features_from_data = X_train.shape[1]
    
    # 2. بناء النموذج
    builder = TabularModelBuilder(config)
    model = builder.build(input_shape=(num_features_from_data,))
    
    # 3. التحقق
    expected_input_shape = model.input_shape[1]
    
    assert num_features_from_data == expected_input_shape, \
        f"عدم تطابق الأبعاد: البيانات تحتوي على {num_features_from_data} ميزة، " \
        f"بينما يتوقع النموذج {expected_input_shape} ميزة."