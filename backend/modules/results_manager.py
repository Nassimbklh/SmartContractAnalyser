"""
Results Management Module
Handles saving and managing attack results and training data
"""

import json
import time
import subprocess
from typing import Dict, Any
from .attack_generator import DecimalEncoder


def log(msg: str):
    """
    Logs a message to the standard output.

    This function outputs a given message string directly to the standard
    output using the `print` function. No additional formatting or
    modifications are applied to the message.

    :param msg: The message to be logged.
    :type msg: str
    :return: None
    """
    print(msg)


def count_lines(filename: str) -> int:
    """
    Counts the number of lines in a given file.

    This function attempts to open a file in read mode and counts the number of
    lines within the file. If the file does not exist, it returns 0.

    :param filename: The path to the file whose lines are to be counted.
    :type filename: str
    :return: The number of lines in the file. Returns 0 if the file does not exist.
    :rtype: int
    """
    try:
        with open(filename, "r") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0


def save_record_to_buffer(record: Dict[str, Any], buffer_file: str = "rlaif_buffer.jsonl"):
    """
    Save a given record to a specified buffer file in JSON Lines format.

    This function appends a dictionary record to a buffer file in the JSON Lines format, allowing
    you to store structured data incrementally. The buffer file is opened in append mode to ensure
    that new records do not overwrite existing ones.

    :param record: The record to be saved. This should be a dictionary containing the data to be
        written to the buffer file.
    :type record: Dict[str, Any]
    :param buffer_file: The file path of the buffer file where the record will be appended. The
        default value for this parameter is "rlaif_buffer.jsonl".
    :type buffer_file: str
    :return: None
    """
    with open(buffer_file, "a") as f:
        f.write(json.dumps(record, cls=DecimalEncoder) + "\n")


def build_instruction_sample(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a structured instruction sample from the given record by formatting the input
    prompt and concatenating reasoning, summary, and exploit code into an output string.
    An optional reward score is also included from the record if available.

    :param record: A dictionary containing the instruction data. It must include keys
        'attack_prompt', 'llm_reasoning', 'llm_summary', and 'llm_code'. Optionally,
        it may contain 'reward_score'.
    :type record: Dict[str, Any]
    :return: A dictionary containing the formatted input prompt, the concatenated output
        string, and the reward score extracted from the input record (or set to 0 if not
        present).
    :rtype: Dict[str, Any]
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
    This function saves a single sample dictionary into a JSON Lines (.jsonl) formatted file. Each invocation appends
    the sample to the specified file, enabling accumulation of data across multiple calls. The function ensures the
    sample is serialized to a string format before writing it into the file.

    :param sample: A dictionary containing the data to be saved. The data must be serializable into JSON format.
    :type sample: Dict[str, Any]
    :param sft_file: The path to the target file where the sample should be appended. If not provided, the default
        filename "finetune_dataset.jsonl" is used.
    :type sft_file: str
    :return: None
    """
    with open(sft_file, "a") as f:
        f.write(json.dumps(sample) + "\n")


def launch_ollama_finetune(sft_file: str, base_model: str = "codestral", new_model: str = "codestral-rlhf-finetuned"):
    """
    Initiates the Ollama fine-tuning process by executing the appropriate
    subprocess call with the specified parameters. This function builds a command
    to create a new fine-tuned model using the specified SFT file and base model.

    :param sft_file: Path to the SFT file used for training the new model.
    :type sft_file: str
    :param base_model: Name of the base model to fine-tune. Defaults to "codestral".
    :type base_model: str
    :param new_model: Name of the new fine-tuned model to be created. Defaults to
        "codestral-rlhf-finetuned".
    :type new_model: str
    :return: None
    :rtype: NoneType
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
    Creates a detailed episode record that encapsulates various components of
    an episode such as observations, funding results, attack strategies, attack
    results, and evaluation outcomes. This record tracks all important steps
    along with timing and feedback details, and structures them into a
    single dictionary for further processing or storage.

    :param observation: A dictionary containing the initial state or scenario
        description used in the episode.
    :type observation: Dict[str, Any]
    :param funding_results: A list of funding-related outcomes or decisions
        generated in the context of the episode.
    :type funding_results: list
    :param attack_strategy: A dictionary describing the attack strategy details
        including the generated prompt, raw response, reasoning, summary, code,
        code type, and execution duration.
    :type attack_strategy: Dict[str, Any]
    :param attack_result: A dictionary holding information about the results of
        the attack executed within the episode.
    :type attack_result: Dict[str, Any]
    :param evaluation: A dictionary containing the evaluation outcomes,
        including raw reward outputs, score values, and comments or observations.
    :type evaluation: Dict[str, Any]

    :return: A structured dictionary representing the complete episode record,
        including a timestamp, details of the attack, evaluations, and other
        key components from the execution.
    :rtype: Dict[str, Any]
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
    Process a sample that has been identified as a "good sample" and adds it to
    the SFT dataset. The function also triggers a fine-tuning process when the
    number of samples in the dataset reaches a specified batch size.

    :param record: A dictionary containing data for the good sample to be processed.
    :type record: Dict[str, Any]
    :param sft_trigger_batch: The batch size threshold that determines when the
        fine-tuning process should be triggered. Defaults to 100.
    :type sft_trigger_batch: int
    :return: None
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
    Saves episode results by creating a record, saving it to the buffer,
    logging the outcome, and processing good samples for further fine-tuning
    if specific conditions are met.

    :param observation: Observation data representing the system or environment's
        status and behavior.
    :type observation: Dict[str, Any]
    :param funding_results: List of funding-related outcomes for the episode.
    :type funding_results: list
    :param attack_strategy: Strategy details used to execute an attack.
    :type attack_strategy: Dict[str, Any]
    :param attack_result: Results derived from applying the attack strategy.
    :type attack_result: Dict[str, Any]
    :param evaluation: Metrics used to evaluate the episode, including rewards
        and scores.
    :type evaluation: Dict[str, Any]
    :param buffer_file: File path for storing episode records in a JSONL format.
        Defaults to "rlaif_buffer.jsonl".
    :type buffer_file: str, optional
    :param sft_trigger_batch: Number of samples required to trigger supervised
        fine-tuning. Defaults to 100.
    :type sft_trigger_batch: int, optional
    :return: A record representing the processed results of the episode.
    :rtype: Dict[str, Any]
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
