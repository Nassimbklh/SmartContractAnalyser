"""
Attack Strategy Generation Module
Handles LLM-based attack strategy generation
"""

import json
import re
import time
from typing import Dict, Any, Tuple
import openai
import requests
import logging
from ..utils import openai_utils

# Set up logger
logger = logging.getLogger(__name__)

def log(msg: str):
    """Simple logging function that uses both print and logger"""
    print(msg)
    logger.info(msg)


def build_contract_analysis_prompt(observation: Dict[str, Any]) -> str:
    """
    Build analysis prompt for LLM to analyze contracts for vulnerabilities

    Args:
        observation: Contract observation data

    Returns:
        Formatted analysis prompt
    """
    txt = f"""
You are a world-class smart contract security auditor.

**Ignore all contracts that are standard utilities (ERC20, SafeMath, Ownable, Math, Interface, Libraries, etc). Focus only on contracts that can hold ETH or user funds, or have business logic.**

Your task is to analyze the contracts and identify vulnerabilities:
- Analyze only the real targets (wallets, banks, DAOs, exchanges, casinos, crowdsales, games, proxies, funds, staking, etc.)
- Identify **any vulnerability**: reentrancy, logic bugs, permission issues, math errors, unsafe calls, backdoors, economic exploits, etc.
- Explain the vulnerability mechanism and potential impact
- If an initial setup is required for exploitation, describe the setup process
- Return the solidity version of the contracts (pragma solidity ^x.x.x)

Contracts context (JSON):
{json.dumps(observation, indent=2)}

Response format:
1. Contract Analysis: ...
2. Vulnerability Assessment: ...  
3. Exploitation Requirements: ...
---
"""
    return txt


def build_attack_code_prompt(observation: Dict[str, Any], analysis_result: str) -> str:
    """
    Build prompt for generating pure Solidity attack code

    Args:
        observation: Contract observation data
        analysis_result: Previous analysis from the auditor

    Returns:
        Formatted attack code generation prompt
    """
    txt = f"""
You are a Solidity exploit developer. Based on the security analysis, create ONLY executable Solidity attack code.

Security Analysis:
{analysis_result}

Target Contract Address: {observation['contracts'][0]['address'] if observation['contracts'] else 'TARGET_ADDRESS'}

Requirements:
- Generate ONLY complete, compilable Solidity code
- Include pragma solidity version 
- Create a contract that can be deployed and executed
- Ensure to use the same solidity version as the target contract and respect the syntax rules for this version
- Include an attack function (named 'attack', 'exploit', or 'run')
- The constructor should take the target contract address as parameter
- Focus on exploiting the identified vulnerabilities
- NO explanations, NO comments, ONLY CODE
Return format: Pure Solidity code in ```solidity code blocks.
```pragma solidity {observation['contracts'][0]['solc_version']}
"""
    return txt


def parse_analysis_response(llm_response: str) -> Tuple[str, str, str]:
    """
    Parse analysis LLM response

    Args:
        llm_response: Raw analysis LLM response

    Returns:
        Tuple of (contract_analysis, vulnerability_assessment, exploitation_requirements)
    """
    contract_analysis = ""
    vulnerability_assessment = ""
    exploitation_requirements = ""

    try:
        analysis_match = re.search(
            r'Contract Analysis.*?:([\s\S]+?)Vulnerability Assessment:',
            llm_response,
            re.IGNORECASE
        )
        vulnerability_match = re.search(
            r'Vulnerability Assessment.*?:([\s\S]+?)Exploitation Requirements:',
            llm_response,
            re.IGNORECASE
        )
        requirements_match = re.search(
            r'Exploitation Requirements.*?:([\s\S]+?)(?:---|$)',
            llm_response,
            re.IGNORECASE
        )

        if analysis_match:
            contract_analysis = analysis_match.group(1).strip()
        if vulnerability_match:
            vulnerability_assessment = vulnerability_match.group(1).strip()
        if requirements_match:
            exploitation_requirements = requirements_match.group(1).strip()

    except Exception as e:
        log(f"Error parsing analysis response: {e}")

    return contract_analysis, vulnerability_assessment, exploitation_requirements


def parse_attack_code_response(llm_response: str) -> Tuple[str, str]:
    """
    Parse attack code LLM response to extract only Solidity code

    Args:
        llm_response: Raw attack code LLM response

    Returns:
        Tuple of (code, code_type)
    """
    code = ""
    code_type = "solidity"

    try:
        # Look for Solidity code blocks
        code_match = re.search(
            r'```(?:solidity)?\n([\s\S]+?)```',
            llm_response,
            re.IGNORECASE
        )

        if code_match:
            code = code_match.group(1).strip()
            code_type = "solidity"
        else:
            # Fallback: try to extract any code-like content
            lines = llm_response.split('\n')
            code_lines = []
            in_code = False

            for line in lines:
                if 'pragma solidity' in line.lower():
                    in_code = True
                    code_lines.append(line)
                elif in_code and (line.strip().startswith('}') and not line.strip().endswith('{')):
                    code_lines.append(line)
                    if line.count('}') >= line.count('{'):
                        break
                elif in_code:
                    code_lines.append(line)

            if code_lines:
                code = '\n'.join(code_lines)

    except Exception as e:
        log(f"Error parsing attack code response: {e}")

    return code, code_type


def query_gpt4(prompt: str, temperature: float = 0.2) -> Tuple[str, float]:
    """
    Query GPT-4 model for attack generation

    Args:
        prompt: Input prompt
        temperature: Sampling temperature

    Returns:
        Tuple of (response, duration)
    """
    t0 = time.time()

    # Log the API call
    logger.info(f"Querying OpenAI GPT-4 API with temperature={temperature}, max_tokens=1800")
    # Log a truncated version of the prompt to avoid excessive logging
    logger.debug(f"Prompt (truncated): {prompt[:200]}...")

    try:
        logger.info("Sending request to OpenAI API...")
        response = openai.chat.completions.create(
            model="gpt-4",  # Using standard GPT-4 model
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1800,
            stop=None,
        )
        out = response.choices[0].message.content
        duration = time.time() - t0

        # Log the response
        logger.info(f"Received response from OpenAI API in {duration:.2f} seconds")
        logger.debug(f"Response (truncated): {out[:200]}...")

        return out, duration

    except Exception as e:
        error_msg = f"Error querying GPT-4: {e}"
        logger.error(error_msg, exc_info=True)
        log(error_msg)  # This will both print and log
        return f"ERROR: {e}", time.time() - t0


def query_codestral_ollama(prompt: str, model: str = "codestral", temperature: float = 0.2) -> Tuple[str, float]:
    """
    Query local Codestral model via Ollama

    Args:
        prompt: Input prompt
        model: Model name
        temperature: Sampling temperature

    Returns:
        Tuple of (response, duration)
    """
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False
    }

    # Log the API call
    logger.info(f"Querying Ollama API with model={model}, temperature={temperature}")
    logger.debug(f"Prompt (truncated): {prompt[:200]}...")

    t0 = time.time()
    try:
        logger.info(f"Sending request to Ollama API at {url}...")
        res = requests.post(url, json=data)
        res.raise_for_status()
        out = res.json().get('response', "")

        # Log the response
        duration = time.time() - t0
        logger.info(f"Received response from Ollama API in {duration:.2f} seconds")
        logger.debug(f"Response (truncated): {out[:200]}...")
    except Exception as e:
        error_msg = f"Error querying Ollama: {e}"
        logger.error(error_msg, exc_info=True)
        log(error_msg)  # This will both print and log
        out = f"ERROR: {e}"
        duration = time.time() - t0

    return out, duration


def query_policy_model(prompt: str, step: int, big_model_threshold: int = 1000) -> Tuple[str, float]:
    """
    Query appropriate model based on step threshold

    Args:
        prompt: Input prompt
        step: Current step number
        big_model_threshold: Threshold for switching models

    Returns:
        Tuple of (response, duration)
    """
    if step < big_model_threshold:
        log("[MODE] Utilisation du gros modèle (GPT-4)")
        return query_gpt4(prompt)
    else:
        log("[MODE] Utilisation du modèle local (Codestral)")
        return query_codestral_ollama(prompt)


def analyze_contracts(observation: Dict[str, Any], step: int = 0) -> Dict[str, Any]:
    """
    Analyze contracts for vulnerabilities using LLM

    Args:
        observation: Contract observation data
        step: Current step number for model selection

    Returns:
        Dictionary containing analysis information
    """
    # Build analysis prompt
    prompt = build_contract_analysis_prompt(observation)

    # Query LLM for analysis
    llm_response, duration = query_policy_model(prompt, step)

    # Parse analysis response
    contract_analysis, vulnerability_assessment, exploitation_requirements = parse_analysis_response(llm_response)

    return {
        "analysis_prompt": prompt,
        "analysis_raw_response": llm_response,
        "contract_analysis": contract_analysis,
        "vulnerability_assessment": vulnerability_assessment,
        "exploitation_requirements": exploitation_requirements,
        "analysis_duration": duration
    }


def generate_attack_code(observation: Dict[str, Any], analysis_result: Dict[str, Any], step: int = 0) -> Dict[str, Any]:
    """
    Generate pure Solidity attack code based on analysis

    Args:
        observation: Contract observation data
        analysis_result: Previous contract analysis
        step: Current step number for model selection

    Returns:
        Dictionary containing attack code information
    """
    # Build full analysis text for the attack prompt
    full_analysis = f"""
Contract Analysis: {analysis_result['contract_analysis']}

Vulnerability Assessment: {analysis_result['vulnerability_assessment']}

Exploitation Requirements: {analysis_result['exploitation_requirements']}
"""

    # Build attack code prompt
    prompt = build_attack_code_prompt(observation, full_analysis)

    # Query LLM for attack code
    llm_response, duration = query_policy_model(prompt, step)

    # Parse attack code response
    code, code_type = parse_attack_code_response(llm_response)

    return {
        "attack_prompt": prompt,
        "attack_raw_response": llm_response,
        "code": code,
        "code_type": code_type,
        "attack_duration": duration
    }


def generate_complete_attack_strategy(observation: Dict[str, Any], step: int = 0) -> Dict[str, Any]:
    """
    Generate complete attack strategy with two separate LLM calls

    Args:
        observation: Contract observation data
        step: Current step number for model selection

    Returns:
        Dictionary containing complete attack strategy information
    """
    logger.info("Starting complete attack strategy generation")
    logger.info(f"Contract name: {observation['contracts'][0]['contract_name'] if observation['contracts'] else 'Unknown'}")
    logger.info(f"Using step number: {step} for model selection")

    # Step 1: Analyze contracts
    log("🔍 Step 1: Analyzing contracts for vulnerabilities...")
    analysis_start_time = time.time()
    analysis_result = analyze_contracts(observation, step)
    logger.info(f"Contract analysis completed in {analysis_result['analysis_duration']:.2f} seconds")

    # Log analysis results
    if analysis_result["vulnerability_assessment"]:
        logger.info(f"Vulnerability assessment: {analysis_result['vulnerability_assessment'][:100]}...")
    else:
        logger.info("No vulnerabilities found in the contract")

    # Step 2: Generate attack code
    log("⚔️ Step 2: Generating attack code...")
    attack_result = generate_attack_code(observation, analysis_result, step)
    logger.info(f"Attack code generation completed in {attack_result['attack_duration']:.2f} seconds")

    # Log attack results
    if attack_result["code"]:
        logger.info(f"Generated attack code of type {attack_result['code_type']} with length {len(attack_result['code'])}")
    else:
        logger.info("No attack code was generated")

    # Combine results
    total_duration = analysis_result["analysis_duration"] + attack_result["attack_duration"]
    logger.info(f"Total attack strategy generation completed in {total_duration:.2f} seconds")

    result = {
        # Analysis results
        "analysis": analysis_result,

        # Attack code results
        "attack": attack_result,

        # Legacy compatibility (for existing pipeline)
        "prompt": analysis_result["analysis_prompt"],
        "raw_response": analysis_result["analysis_raw_response"],
        "reasoning": analysis_result["contract_analysis"],
        "summary": analysis_result["vulnerability_assessment"],
        "code": attack_result["code"],
        "code_type": attack_result["code_type"],
        "duration": total_duration
    }

    logger.info("Attack strategy generation completed successfully")
    return result
