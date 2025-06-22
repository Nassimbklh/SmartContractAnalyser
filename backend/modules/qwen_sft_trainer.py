import json
import logging
import os
import torch
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from transformers import BitsAndBytesConfig

@dataclass
class QwenTrainingConfig:
    """Configuration for QwenCoderV2 SFT training with LoRA"""
    model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    learning_rate: float = 2e-5
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    max_length: int = 4096
    warmup_steps: int = 100
    logging_steps: int = 10
    save_steps: int = 500
    output_dir: str = "qwen_fine_tuned"
    use_weights: bool = True
    weight_scaling: str = "sqrt"  # "linear", "sqrt", or "exponential"
    fp16: bool = True
    gradient_checkpointing: bool = True
    dataloader_num_workers: int = 4
    remove_unused_columns: bool = False
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "loss"
    greater_is_better: bool = False
    # LoRA specific configuration
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    lora_target_modules: List[str] = None
    lora_bias: str = "none"  # "none", "all", or "lora_only"
    # Quantization configuration
    use_4bit_quantization: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    use_nested_quant: bool = False

class QwenDataset(Dataset):
    """Custom dataset for QwenCoderV2 training with weighted samples"""
    
    def __init__(self, data: List[Dict[str, Any]], tokenizer, max_length: int = 4096):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # Format the conversation for QwenCoderV2
        conversation = f"<|im_start|>user\n{item['instruction']}<|im_end|>\n<|im_start|>assistant\n{item['output']}<|im_end|>"
        
        # Tokenize
        encoding = self.tokenizer(
            conversation,
            truncation=True,
            padding=False,
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        input_ids = encoding["input_ids"].squeeze()
        attention_mask = encoding["attention_mask"].squeeze()
        
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": input_ids.clone(),
            "weight": item.get("weight", 1.0)
        }

class WeightedTrainer(Trainer):
    """Custom trainer that handles weighted loss for training samples"""
    
    def compute_loss(self, model, inputs, return_outputs=False):
        """
        Compute weighted loss for training samples
        """
        labels = inputs.get("labels")
        weights = inputs.get("weight", torch.ones(labels.shape[0]))
        
        # Forward pass
        outputs = model(**{k: v for k, v in inputs.items() if k not in ["weight"]})
        
        if labels is not None:
            # Calculate loss
            shift_logits = outputs.logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            loss_fct = torch.nn.CrossEntropyLoss(reduction='none')
            loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
            
            # Reshape loss and apply weights
            loss = loss.view(shift_labels.shape)
            loss = loss.mean(dim=1)  # Average over sequence length
            
            # Apply sample weights
            if isinstance(weights, (int, float)):
                weights = torch.tensor([weights] * loss.shape[0])
            elif not isinstance(weights, torch.Tensor):
                weights = torch.tensor(weights)
            
            weights = weights.to(loss.device)
            weighted_loss = (loss * weights).mean()
            
            return (weighted_loss, outputs) if return_outputs else weighted_loss
        
        return (outputs.loss, outputs) if return_outputs else outputs.loss

class QwenSFTDataProcessor:
    """Handles loading and preprocessing of JSONL training data for QwenCoderV2"""
    
    def __init__(self, config: QwenTrainingConfig):
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the data processor"""
        logger = logging.getLogger('QwenSFTDataProcessor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def load_jsonl_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load training data from JSONL file"""
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        item = json.loads(line.strip())
                        if self._validate_data_item(item, line_num):
                            data.append(item)
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Invalid JSON on line {line_num}: {e}")
                        continue
            
            self.logger.info(f"Loaded {len(data)} training examples from {file_path}")
            return data
        
        except FileNotFoundError:
            self.logger.error(f"Training file not found: {file_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading training data: {e}")
            raise
    
    def _validate_data_item(self, item: Dict[str, Any], line_num: int) -> bool:
        """Validate a single training data item"""
        required_fields = ['instruction', 'output']
        
        for field in required_fields:
            if field not in item or not isinstance(item[field], str):
                self.logger.warning(
                    f"Line {line_num}: Missing or invalid '{field}' field"
                )
                return False
        
        if 'weight' in item and not isinstance(item['weight'], (int, float)):
            self.logger.warning(
                f"Line {line_num}: Invalid weight value, using default weight 1.0"
            )
            item['weight'] = 1.0
        elif 'weight' not in item:
            item['weight'] = 1.0
        
        return True
    
    def process_weights(self, data: List[Dict[str, Any]]) -> np.ndarray:
        """Process and normalize weights based on scaling method"""
        weights = np.array([item.get('weight', 1.0) for item in data])
        
        if not self.config.use_weights:
            return np.ones_like(weights)
        
        # Apply scaling
        if self.config.weight_scaling == "sqrt":
            processed_weights = np.sqrt(weights)
        elif self.config.weight_scaling == "exponential":
            processed_weights = np.exp(weights / weights.max())
        else:  # linear
            processed_weights = weights
        
        # Normalize
        processed_weights = processed_weights / processed_weights.sum() * len(processed_weights)
        
        self.logger.info(f"Applied {self.config.weight_scaling} weight scaling")
        self.logger.info(f"Weight stats - Min: {weights.min():.2f}, Max: {weights.max():.2f}, Mean: {weights.mean():.2f}")
        
        return processed_weights

class QwenSFTTrainer:
    """Main trainer class for QwenCoderV2 Supervised Fine-Tuning"""
    
    def __init__(self, config: QwenTrainingConfig):
        self.config = config
        self.data_processor = QwenSFTDataProcessor(config)
        self.logger = self._setup_logger()
        self.tokenizer = None
        self.model = None
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the trainer"""
        logger = logging.getLogger('QwenSFTTrainer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def setup_model_and_tokenizer(self):
        """Initialize QwenCoderV2 model and tokenizer with LoRA and quantization"""
        self.logger.info(f"Loading model and tokenizer: {self.config.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name,
            trust_remote_code=True,
            padding_side="right"
        )
        
        # Add pad token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Configure quantization if enabled (skip on Apple Silicon due to compatibility issues)
        quantization_config = None
        device_supports_bnb = torch.cuda.is_available() or not torch.backends.mps.is_available()
        
        if self.config.use_4bit_quantization and device_supports_bnb:
            self.logger.info("Using 4-bit quantization for memory efficiency...")
            try:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=getattr(torch, self.config.bnb_4bit_compute_dtype),
                    bnb_4bit_use_double_quant=self.config.use_nested_quant,
                    bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
                )
            except Exception as e:
                self.logger.warning(f"4-bit quantization not available: {e}")
                self.logger.info("Falling back to standard loading with memory optimizations...")
                quantization_config = None
        elif self.config.use_4bit_quantization:
            self.logger.warning("4-bit quantization not supported on Apple Silicon, using memory optimizations instead...")
        
        # Load base model
        model_kwargs = {
            "torch_dtype": torch.float16 if self.config.fp16 else torch.float32,
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }
        
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
            model_kwargs["device_map"] = "auto"
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            **model_kwargs
        )
        
        # Prepare model for k-bit training if quantization is used
        if quantization_config:
            self.model = prepare_model_for_kbit_training(self.model)
        
        # Apply LoRA if enabled
        if self.config.use_lora:
            self.logger.info("Applying LoRA configuration...")
            
            # Set default target modules for Qwen models if not specified
            if self.config.lora_target_modules is None:
                self.config.lora_target_modules = [
                    "q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"
                ]
            
            # Create LoRA configuration
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=self.config.lora_r,
                lora_alpha=self.config.lora_alpha,
                lora_dropout=self.config.lora_dropout,
                target_modules=self.config.lora_target_modules,
                bias=self.config.lora_bias,
                inference_mode=False
            )
            
            # Apply LoRA to the model
            self.model = get_peft_model(self.model, lora_config)
            
            # Print trainable parameters
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            all_params = sum(p.numel() for p in self.model.parameters())
            
            self.logger.info(f"LoRA applied successfully")
            self.logger.info(f"Trainable parameters: {trainable_params:,} ({100 * trainable_params / all_params:.2f}%)")
            self.logger.info(f"Total parameters: {all_params:,}")
        
        # Enable gradient checkpointing if specified
        if self.config.gradient_checkpointing:
            self.model.gradient_checkpointing_enable()
        
        self.logger.info("Model and tokenizer loaded successfully")
    
    def prepare_datasets(self, train_file: str, val_file: Optional[str] = None):
        """Prepare training and validation datasets"""
        # Load training data
        train_data = self.data_processor.load_jsonl_data(train_file)
        train_dataset = QwenDataset(train_data, self.tokenizer, self.config.max_length)
        
        # Process weights for weighted sampling
        weights = self.data_processor.process_weights(train_data)
        
        # Create weighted sampler if using weights
        train_sampler = None
        if self.config.use_weights:
            train_sampler = WeightedRandomSampler(
                weights=weights,
                num_samples=len(train_data),
                replacement=True
            )
        
        # Load validation data if provided
        val_dataset = None
        if val_file and os.path.exists(val_file):
            val_data = self.data_processor.load_jsonl_data(val_file)
            val_dataset = QwenDataset(val_data, self.tokenizer, self.config.max_length)
        
        return train_dataset, val_dataset, train_sampler
    
    def train(self, train_file: str, val_file: Optional[str] = None):
        """Train the QwenCoderV2 model"""
        # Setup model and tokenizer
        self.setup_model_and_tokenizer()
        
        # Prepare datasets
        train_dataset, val_dataset, train_sampler = self.prepare_datasets(train_file, val_file)
        
        # Training arguments with memory optimizations
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.save_steps if val_dataset else None,
            eval_strategy="steps" if val_dataset else "no",
            save_strategy="steps",
            fp16=self.config.fp16,
            gradient_checkpointing=self.config.gradient_checkpointing,
            dataloader_num_workers=self.config.dataloader_num_workers,
            remove_unused_columns=self.config.remove_unused_columns,
            load_best_model_at_end=self.config.load_best_model_at_end and val_dataset is not None,
            metric_for_best_model=self.config.metric_for_best_model,
            greater_is_better=self.config.greater_is_better,
            report_to=None,  # Disable wandb/tensorboard logging
            save_total_limit=3,
            # Memory optimization settings
            max_grad_norm=1.0,
            dataloader_pin_memory=False,
            dataloader_persistent_workers=False,
            ddp_find_unused_parameters=False,
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
            pad_to_multiple_of=8 if self.config.fp16 else None,
        )
        
        # Initialize trainer
        trainer = WeightedTrainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
            processing_class=self.tokenizer,
        )
        
        # Override the data loader if using weighted sampling
        if train_sampler is not None:
            trainer._get_train_sampler = lambda: train_sampler
        
        # Start training
        self.logger.info("Starting training...")
        trainer.train()
        
        # Save the final model
        if self.config.use_lora:
            # Save LoRA adapter
            self.model.save_pretrained(self.config.output_dir)
            self.logger.info(f"LoRA adapter saved to {self.config.output_dir}")
        else:
            # Save full model
            trainer.save_model()
        
        # Save tokenizer
        self.tokenizer.save_pretrained(self.config.output_dir)
        
        self.logger.info(f"Training completed. Model saved to {self.config.output_dir}")
        
        return trainer
    
    def save_config(self, config_file: str = "qwen_training_config.json"):
        """Save training configuration"""
        config_dict = {
            'model_name': self.config.model_name,
            'learning_rate': self.config.learning_rate,
            'batch_size': self.config.batch_size,
            'gradient_accumulation_steps': self.config.gradient_accumulation_steps,
            'num_epochs': self.config.num_epochs,
            'max_length': self.config.max_length,
            'warmup_steps': self.config.warmup_steps,
            'logging_steps': self.config.logging_steps,
            'save_steps': self.config.save_steps,
            'output_dir': self.config.output_dir,
            'use_weights': self.config.use_weights,
            'weight_scaling': self.config.weight_scaling,
            'fp16': self.config.fp16,
            'gradient_checkpointing': self.config.gradient_checkpointing,
            'use_lora': self.config.use_lora,
            'lora_r': self.config.lora_r,
            'lora_alpha': self.config.lora_alpha,
            'lora_dropout': self.config.lora_dropout,
            'lora_target_modules': self.config.lora_target_modules,
            'lora_bias': self.config.lora_bias,
            'use_4bit_quantization': self.config.use_4bit_quantization,
            'bnb_4bit_compute_dtype': self.config.bnb_4bit_compute_dtype,
            'bnb_4bit_quant_type': self.config.bnb_4bit_quant_type,
            'use_nested_quant': self.config.use_nested_quant
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        self.logger.info(f"Configuration saved to {config_file}")

def main():
    """Example usage of the QwenCoderV2 SFT trainer"""
    # Create training configuration
    config = QwenTrainingConfig(
        model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
        num_epochs=3,
        batch_size=2,  # Smaller batch size for 7B model
        gradient_accumulation_steps=8,
        learning_rate=2e-4,  # Higher learning rate for LoRA
        use_weights=True,
        weight_scaling="sqrt",
        fp16=True,
        gradient_checkpointing=True,
        output_dir="qwen_fine_tuned_model",
        use_lora=True,
        lora_r=16,
        lora_alpha=32,
        lora_dropout=0.1
    )
    
    # Initialize trainer
    trainer = QwenSFTTrainer(config)
    
    # Save configuration
    trainer.save_config()
    
    # Start training
    training_file = "fine_tune_data(1).jsonl"
    trainer.train(training_file)

if __name__ == "__main__":
    main()