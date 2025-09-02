# FILE: tests/test_smoke.py
import pytest
import tensorflow as tf

from src.utils import load_config
from src.data_handler import DataHandler
from src.model_builder import ModelBuilder


@pytest.fixture
def binary_config():
    """تحميل تكوين ثنائي للاختبار."""
    return load_config("configs/binary/06_myopia.yaml")


@pytest.fixture
def multi_class_config():
    """تحميل تكوين متعدد الفئات للاختبار."""
    return load_config("configs/multi_class_config.yaml")


def test_binary_model_build(binary_config):
    """اختبار دخان: هل يمكن بناء نموذج ثنائي بالشكل الصحيح؟"""
    builder = ModelBuilder(binary_config)
    model = builder.build()

    assert isinstance(model, tf.keras.Model)
    assert model.output_shape == (None, 1)


def test_multi_class_model_build(multi_class_config):
    """اختبار دخان: هل يمكن بناء نموذج متعدد الفئات بالشكل الصحيح؟"""
    builder = ModelBuilder(multi_class_config)
    model = builder.build()

    assert isinstance(model, tf.keras.Model)
    assert model.output_shape == (None, len(multi_class_config['data']['class_names']))


# ملاحظة:
# اختبار DataHandler يتطلب وجود بيانات TFRecord،
# لذا يجب تشغيله بعد خطوة المعالجة المسبقة.
