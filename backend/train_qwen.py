#!/usr/bin/env python3
"""
QwenCoderV2 SFT Training Script

This script trains QwenCoderV2 using supervised fine-tuning (SFT) with weighted training data.
The training data should be in JSONL format with 'instruction', 'output', and 'weight' columns.

Usage:
    python train_qwen.py --config config.json
    python train_qwen.py --data fine_tune_data.jsonl --output ./models/qwen_finetuned
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from qwen_sft_trainer import QwenSFTTrainer, QwenTrainingConfig

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('training.log'),
            logging.StreamHandler()
        ]
    )

def load_config(config_path: str) -> QwenTrainingConfig:
    """Load training configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        return QwenTrainingConfig(**config_dict)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        raise
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        raise

def create_default_config() -> QwenTrainingConfig:
    """Create default training configuration with LoRA"""
    return QwenTrainingConfig(
        model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
        learning_rate=2e-4,  # Higher learning rate for LoRA
        batch_size=2,
        gradient_accumulation_steps=8,
        num_epochs=3,
        max_length=4096,
        warmup_steps=100,
        logging_steps=10,
        save_steps=500,
        output_dir="qwen_fine_tuned",
        use_weights=True,
        weight_scaling="sqrt",
        fp16=False,
        gradient_checkpointing=True,
        use_lora=True,
        lora_r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        lora_target_modules=None,  # Will be set automatically
        lora_bias="none"
    )

def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description="Train QwenCoderV2 with SFT")
    parser.add_argument("--config", type=str, help="Path to configuration JSON file")
    parser.add_argument("--data", type=str, default="fine_tune_data(1).jsonl", 
                        help="Path to training data JSONL file")
    parser.add_argument("--validation", type=str, help="Path to validation data JSONL file")
    parser.add_argument("--output", type=str, help="Output directory for the trained model")
    parser.add_argument("--model", type=str, help="Base model name/path")
    parser.add_argument("--epochs", type=int, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, help="Training batch size")
    parser.add_argument("--learning_rate", type=float, help="Learning rate")
    parser.add_argument("--use_weights", action="store_true", help="Use sample weights for training")
    parser.add_argument("--weight_scaling", type=str, choices=["linear", "sqrt", "exponential"],
                        help="Weight scaling method")
    parser.add_argument("--fp16", action="store_true", help="Use mixed precision training")
    parser.add_argument("--use_lora", action="store_true", help="Use LoRA for efficient fine-tuning")
    parser.add_argument("--lora_r", type=int, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, help="LoRA alpha parameter")
    parser.add_argument("--lora_dropout", type=float, help="LoRA dropout rate")
    parser.add_argument("--use_4bit", action="store_true", help="Use 4-bit quantization")
    parser.add_argument("--save_config", action="store_true", 
                        help="Save the configuration to a JSON file")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting QwenCoderV2 SFT training...")
    
    # Load or create configuration
    if args.config:
        config = load_config(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    else:
        config = create_default_config()
        logger.info("Using default configuration")
    
    # Override config with command line arguments
    if args.output:
        config.output_dir = args.output
    if args.model:
        config.model_name = args.model
    if args.epochs:
        config.num_epochs = args.epochs
    if args.batch_size:
        config.batch_size = args.batch_size
    if args.learning_rate:
        config.learning_rate = args.learning_rate
    if args.use_weights:
        config.use_weights = True
    if args.weight_scaling:
        config.weight_scaling = args.weight_scaling
    if args.fp16:
        config.fp16 = True
    if args.use_lora:
        config.use_lora = True
    if args.lora_r:
        config.lora_r = args.lora_r
    if args.lora_alpha:
        config.lora_alpha = args.lora_alpha
    if args.lora_dropout:
        config.lora_dropout = args.lora_dropout
    if args.use_4bit:
        config.use_4bit_quantization = True
    
    # Validate training data file
    if not os.path.exists(args.data):
        logger.error(f"Training data file not found: {args.data}")
        return 1
    
    # Create output directory
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Save configuration if requested
    if args.save_config:
        config_path = os.path.join(config.output_dir, "training_config.json")
        config_dict = {
            'model_name': config.model_name,
            'learning_rate': config.learning_rate,
            'batch_size': config.batch_size,
            'gradient_accumulation_steps': config.gradient_accumulation_steps,
            'num_epochs': config.num_epochs,
            'max_length': config.max_length,
            'warmup_steps': config.warmup_steps,
            'logging_steps': config.logging_steps,
            'save_steps': config.save_steps,
            'output_dir': config.output_dir,
            'use_weights': config.use_weights,
            'weight_scaling': config.weight_scaling,
            'fp16': config.fp16,
            'gradient_checkpointing': config.gradient_checkpointing,
            'use_lora': config.use_lora,
            'lora_r': config.lora_r,
            'lora_alpha': config.lora_alpha,
            'lora_dropout': config.lora_dropout,
            'lora_target_modules': config.lora_target_modules,
            'lora_bias': config.lora_bias
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
    
    # Print configuration
    logger.info("Training Configuration:")
    logger.info(f"  Model: {config.model_name}")
    logger.info(f"  Training data: {args.data}")
    logger.info(f"  Validation data: {args.validation or 'None'}")
    logger.info(f"  Output directory: {config.output_dir}")
    logger.info(f"  Epochs: {config.num_epochs}")
    logger.info(f"  Batch size: {config.batch_size}")
    logger.info(f"  Gradient accumulation steps: {config.gradient_accumulation_steps}")
    logger.info(f"  Learning rate: {config.learning_rate}")
    logger.info(f"  Use weights: {config.use_weights}")
    logger.info(f"  Weight scaling: {config.weight_scaling}")
    logger.info(f"  FP16: {config.fp16}")
    logger.info(f"  Gradient checkpointing: {config.gradient_checkpointing}")
    
    try:
        # Initialize trainer
        trainer = QwenSFTTrainer(config)
        
        # Start training
        trainer.train(args.data, args.validation)
        
        logger.info("Training completed successfully!")
        logger.info(f"Model saved to: {config.output_dir}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Training failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())