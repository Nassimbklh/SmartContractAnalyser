"""
Attack Evaluation Module
Handles evaluation of attack effectiveness using reward models
"""

import json
import re
from typing import Dict, Any, Tuple
import openai
from ..utils import openai_utils


def log(msg: str):
    """Simple logging function"""
    print(msg)


def reward_prompt(observation: Dict[str, Any], llm_response: str, attack_result: Dict[str, Any]) -> str:
    """
    Build reward evaluation prompt

    Args:
        observation: Contract observation data
        llm_response: LLM attack response
        attack_result: Attack execution results

    Returns:
        Formatted reward prompt
    """
    prompt = f"""
You are an advanced smart contract auditor. Evaluate the following attack attempt.

CONTEXT:
- Contracts and states (truncated): {json.dumps(observation, indent=2)[:2000]}
- LLM (Codestral) response: {llm_response[:1000]}
- Attack result: {json.dumps(attack_result)}

Please rate the effectiveness and relevance of this attack on a scale from 0 (useless) to 10 (critical exploit), and justify your rating.
Format: SCORE: <number> | COMMENT: <reasoning>
"""
    return prompt


def parse_reward_output(reward_output: str) -> Tuple[float, str]:
    """
    Parse reward model output to extract score and comment

    Args:
        reward_output: Raw reward model output

    Returns:
        Tuple of (score, comment)
    """
    score = 0.0
    comment = ""

    try:
        # Extract score
        score_match = re.search(r'SCORE\s*:\s*([\d.]+)', reward_output, re.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))

        # Extract comment
        comment_match = re.search(r'COMMENT\s*:\s*(.*)', reward_output, re.IGNORECASE)
        if comment_match:
            comment = comment_match.group(1).strip()

    except Exception as e:
        log(f"Error parsing reward output: {e}")

    return score, comment


def query_gpt4_reward(prompt: str, model: str = "gpt-4", temperature: float = 0) -> str:
    """
    Query GPT-4 for reward evaluation

    Args:
        prompt: Evaluation prompt
        model: GPT-4 model variant
        temperature: Sampling temperature

    Returns:
        Reward evaluation response
    """
    try:
        response = openai.chat.completions.create(
            model=model,  # Using standard GPT-4 model
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=250,
            stop=None,
        )
        return response.choices[0].message.content

    except Exception as e:
        log(f"Error querying reward model: {e}")
        return f"ERROR: {e}"


def evaluate_attack(observation: Dict[str, Any], llm_response: str, attack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate attack effectiveness using reward model

    Args:
        observation: Contract observation data
        llm_response: LLM attack response
        attack_result: Attack execution results

    Returns:
        Evaluation results
    """
    # Build reward prompt
    reward_prompt_text = reward_prompt(observation, llm_response, attack_result)

    # Query reward model
    reward_raw = query_gpt4_reward(reward_prompt_text)

    # Parse reward output
    reward_score, reward_comment = parse_reward_output(reward_raw)

    return {
        "reward_prompt": reward_prompt_text,
        "reward_raw_output": reward_raw,
        "reward_score": reward_score,
        "reward_comment": reward_comment
    }
