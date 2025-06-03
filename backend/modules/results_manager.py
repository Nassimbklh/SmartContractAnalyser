"""
Results Management Module
Handles saving and managing attack results and training data
"""

import json
import time
import subprocess
from typing import Dict, Any


def log(msg: str):
    """Simple logging function"""
    print(msg)


def count_lines(filename: str) -> int:
    """
    Count lines in a file

    Args:
        filename: Path to file

    Returns:
        Number of lines in file
    """
    try:
        with open(filename, "r") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0


def save_record_to_buffer(record: Dict[str, Any], buffer_file: str = "rlaif_buffer.jsonl"):
    """
    Save attack record to buffer file

    Args:
        record: Attack record data
        buffer_file: Path to buffer file
    """
    with open(buffer_file, "a") as f:
        f.write(json.dumps(record) + "\n")


def build_instruction_sample(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build instruction sample for supervised fine-tuning

    Args:
        record: Attack record

    Returns:
        Formatted instruction sample
    """
    prompt = record["attack_prompt"].strip()
    output = (
        f"Chain of thought:\n{record['llm_reasoning']}\n"
        f"Summary:\n{record['llm_summary']}\n"
        f"Exploit code:\n{record['llm_code']}\n"
    )

    return {
        "input": prompt,
        "output": output,
        "reward_score": record.get("reward_score", 0)
    }


def save_instruction_sample(sample: Dict[str, Any], sft_file: str = "finetune_dataset.jsonl"):
    """
    Save instruction sample to fine-tuning dataset

    Args:
        sample: Instruction sample
        sft_file: Path to fine-tuning dataset file
    """
    with open(sft_file, "a") as f:
        f.write(json.dumps(sample) + "\n")


def launch_ollama_finetune(sft_file: str, base_model: str = "codestral", new_model: str = "codestral-rlhf-finetuned"):
    """
    Launch Ollama fine-tuning process

    Args:
        sft_file: Path to fine-tuning dataset
        base_model: Base model name
        new_model: New model name after fine-tuning
    """
    cmd = [
        "ollama", "create", new_model,
        "--from", base_model,
        "--data", sft_file
    ]

    log(f"Lancement du fine-tuning Ollama: {' '.join(cmd)}")
    subprocess.run(cmd)


def create_episode_record(
        observation: Dict[str, Any],
        funding_results: list,
        attack_strategy: Dict[str, Any],
        attack_result: Dict[str, Any],
        evaluation: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create complete episode record

    Args:
        observation: Contract observation data
        funding_results: Contract funding results
        attack_strategy: Generated attack strategy
        attack_result: Attack execution results
        evaluation: Attack evaluation results

    Returns:
        Complete episode record
    """
    return {
        "timestamp": time.time(),
        "observation": observation,
        "funding_results": funding_results,
        "attack_prompt": attack_strategy["prompt"],
        "llm_raw_output": attack_strategy["raw_response"],
        "llm_reasoning": attack_strategy["reasoning"],
        "llm_summary": attack_strategy["summary"],
        "llm_code": attack_strategy["code"],
        "llm_code_type": attack_strategy["code_type"],
        "attack_result": attack_result,
        "reward_model_output": evaluation["reward_raw_output"],
        "reward_score": evaluation["reward_score"],
        "reward_comment": evaluation["reward_comment"],
        "duration_sec": attack_strategy["duration"]
    }


def process_good_sample(record: Dict[str, Any], sft_trigger_batch: int = 100):
    """
    Process a good attack sample for fine-tuning

    Args:
        record: Attack record
        sft_trigger_batch: Number of samples to trigger fine-tuning
    """
    log("🔄 Bon sample détecté ! Ajout au dataset SFT.")

    # Build and save instruction sample
    sample = build_instruction_sample(record)
    save_instruction_sample(sample)

    # Check if we should trigger fine-tuning
    num_samples = count_lines("finetune_dataset.jsonl")
    if num_samples > 0 and num_samples % sft_trigger_batch == 0:
        log(f"🚀 Déclenchement du fine-tuning (chaque {sft_trigger_batch} bons samples)")
        launch_ollama_finetune("finetune_dataset.jsonl")


def save_episode_results(
        observation: Dict[str, Any],
        funding_results: list,
        attack_strategy: Dict[str, Any],
        attack_result: Dict[str, Any],
        evaluation: Dict[str, Any],
        buffer_file: str = "rlaif_buffer.jsonl",
        sft_trigger_batch: int = 100
) -> Dict[str, Any]:
    """
    Save complete episode results and handle fine-tuning triggers

    Args:
        observation: Contract observation data
        funding_results: Contract funding results
        attack_strategy: Generated attack strategy
        attack_result: Attack execution results
        evaluation: Attack evaluation results
        buffer_file: Path to buffer file
        sft_trigger_batch: Number of samples to trigger fine-tuning

    Returns:
        Complete episode record
    """
    # Create complete record
    record = create_episode_record(
        observation, funding_results, attack_strategy, attack_result, evaluation
    )

    # Save to buffer
    save_record_to_buffer(record, buffer_file=buffer_file)

    # Log results
    log(f"✅ Episode saved. Reward: {evaluation['reward_score']}/10. Success: {attack_result.get('success', False)}")

    # Process good samples for fine-tuning
    if evaluation["reward_score"] >= 8 and attack_result.get("success", False):
        process_good_sample(record, sft_trigger_batch)

    return record