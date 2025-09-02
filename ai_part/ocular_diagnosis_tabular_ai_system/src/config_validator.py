# FILE: src/config_validator.py

import logging
from pydantic import BaseModel, FilePath, DirectoryPath, Field, model_validator
from typing import Dict, Any

class VisionModelsConfig(BaseModel):
    """Schema for validating vision model paths."""
    multi_class: FilePath
    expert_models: Dict[str, FilePath]

class DataInputConfig(BaseModel):
    """Schema for validating data input paths."""
    csv_path: FilePath
    images_dir: DirectoryPath

class DataOutputConfig(BaseModel):
    """Schema for validating data output settings."""
    format: str
    features_path: str
    split_seed: int
    test_split: float = Field(..., gt=0, lt=1)
    val_split: float = Field(..., gt=0, lt=1)

    @model_validator(mode='after')
    def check_splits_sum(self) -> 'DataOutputConfig':
        """Ensures that test and validation splits do not exceed 100%."""
        if self.test_split + self.val_split >= 1.0:
            raise ValueError("The sum of test_split and val_split must be less than 1.0")
        return self

class FusionConfig(BaseModel):
    """Schema for validating the fusion strategy settings."""
    strategy: str
    params: Dict[str, Any] = {}

class FeatureGenerationConfig(BaseModel):
    """
    The main schema for the entire feature generation configuration file.
    It composes all the sub-schemas to validate the full structure.
    """
    environment: Dict[str, Any]
    vision_models: VisionModelsConfig
    data: DataInputConfig
    output: DataOutputConfig
    fusion: FusionConfig

def validate_feature_generation_config(config_dict: Dict[str, Any]):
    """
    Validates the feature generation configuration dictionary against the defined schema.

    Args:
        config_dict (Dict): The configuration loaded from the YAML file.

    Raises:
        pydantic.ValidationError: If the configuration is invalid.
    """
    try:
        logging.info("Validating feature generation configuration schema...")
        FeatureGenerationConfig.model_validate(config_dict)
        logging.info("Configuration schema is valid.")
    except Exception as e:
        logging.error(f"Configuration validation failed: {e}", exc_info=True)
        raise