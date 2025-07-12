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
from decimal import Decimal

# Set up logger
logger = logging.getLogger(__name__)

def log(msg: str):
    """
    Logs a given message to the console and to the logger.

    This function takes a string message as input, prints it to the console
    output, and also logs it using the logger. It provides dual logging functionality.

    :param msg: The message that needs to be logged.
    :type msg: str
    :return: None
    """
    print(msg)
    logger.info(msg)


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def build_contract_analysis_prompt(slith: str, observation: Dict[str, Any]) -> str:
    """
    Builds a detailed prompt for a world-class smart contract security auditor.

    The function generates a specific text template aimed at aiding auditors in identifying
    vulnerabilities within smart contracts that deal with user funds or business logic. The
    resulting prompt instructs the auditor to focus only on relevant contract types and disregard
    standard utility contracts. It also provides required criteria for analysis, including types
    of vulnerabilities to detect and the format for reporting the analysis.

    :param slith: The slither analysis results to include in the prompt.
    :type slith: str
    :param observation: The context for the contracts as a dictionary, which includes
        details required for the analysis.
    :type observation: Dict[str, Any]
    :return: A formatted string containing the instructions and details
        for the smart contract analysis task.
    :rtype: str
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

The slither analyze : {slith} 

Contracts context (JSON):
{json.dumps(observation, indent=2, cls=DecimalEncoder)}

Response format:
1. Contract Analysis: ...
2. Vulnerability Assessment: ...  
3. Exploitation Requirements: ...
---
"""
    return txt


def build_attack_code_prompt(observation: Dict[str, Any], analysis_result: str) -> str:
    """
    Generate a prompt for creating a Solidity exploit based on the given security analysis and
    target contract details. The prompt instructs developers on generating an executable Solidity
    attack code while adhering to specific constraints and formatting.

    :param observation: Data containing information about the target contract, including its
        address and Solidity compiler version.
    :type observation: Dict[str, Any]
    :param analysis_result: The security analysis result highlighting vulnerabilities in the target
        contract.
    :type analysis_result: str
    :return: A prompt string instructing the creation of an executable Solidity exploit based
        on the given analysis and target contract details.
    :rtype: str
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
    Parses the provided response from an LLM (Large Language Model) analysis and extracts
    specific sections: Contract Analysis, Vulnerability Assessment, and Exploitation
    Requirements. This function organizes the content into three separate categories
    for further analysis or processing.

    :param llm_response: A string containing the response from the LLM, which is expected
        to include sections titled 'Contract Analysis', 'Vulnerability Assessment', and
        'Exploitation Requirements'.
    :return: A tuple containing three strings:
        - The extracted 'Contract Analysis' section
        - The extracted 'Vulnerability Assessment' section
        - The extracted 'Exploitation Requirements' section
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
    Parses a response for attack code and extracts the contained Solidity code or any code-like content.
    If a Solidity code block is found within a Markdown-style block or as a code snippet with "pragma solidity",
    it is extracted and assigned the type "solidity". Otherwise, attempts are made to extract other
    code-like content. Handles cases where code may not strictly follow formatting conventions.

    :param llm_response: The response text to parse. Typically expected to contain code, either formatted as Markdown
        code blocks or recognizable Solidity code.
    :type llm_response: str
    :return: A tuple where the first element is the extracted code (or an empty string if no valid code is found),
        and the second element is the type of the code, defaulting to "solidity".
    :rtype: Tuple[str, str]
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
    Query the GPT-4 model to generate a response for a given prompt and measure the
    time taken to produce the response. The function sends a prompt to OpenAI's GPT-4
    language model with a specified temperature to control the randomness of the output.
    It handles possible exceptions during the request and logs error information if
    the request fails.

    :param prompt: The input prompt to send to the GPT-4 model.
    :type prompt: str
    :param temperature: A float value controlling the randomness of the model's output.
        Higher values make output more random, lower values make it more deterministic.
    :type temperature: float, optional
    :return: A tuple containing the model's response as a string and the time taken
        to generate the response in seconds.
    :rtype: Tuple[str, float]
    """
    t0 = time.time()

    # Log the API call
    logger.info(f"Querying OpenAI GPT-4 API with temperature={temperature}, max_tokens=1800")
    # Log a truncated version of the prompt to avoid excessive logging
    logger.debug(f"Prompt (truncated): {prompt[:200]}...")

    try:
        logger.info("Sending request to OpenAI API...")
        response = openai.chat.completions.create(
            model="gpt-4.1-mini",  # Using GPT-4.1-mini model
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
    Queries the Codestral Ollama API to generate a response based on a given prompt,
    model, and temperature. The method sends an HTTP POST request to the specified
    API endpoint and measures the time taken to process the request.

    :param prompt: The input string used as a basis for generating the response.
    :type prompt: str
    :param model: The name of the model to use for generating the response. Defaults to "codestral".
    :type model: str, optional
    :param temperature: A float value representing the randomness of generated responses.
        Lower values result in more deterministic responses. Defaults to 0.2.
    :type temperature: float, optional

    :return: A tuple containing the API's response as a string and the duration of
        the request in seconds.
    :rtype: Tuple[str, float]
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
    Query the appropriate policy model based on the step value against
    a predefined threshold. This function determines whether to use a large
    model (e.g., GPT-4) or a local model (e.g., Codestral) for the query,
    logs the mode used, and then performs the model request.

    :param prompt: The input text or query string to be processed by the model.
    :type prompt: str
    :param step: The current step or benchmark value to assess against the
        big_model_threshold.
    :type step: int
    :param big_model_threshold: The threshold value used to decide whether
        to use the large model or the local model. Defaults to 1000.
    :type big_model_threshold: int
    :return: A tuple containing the model's response as a string and an
        associated confidence score as a float.
    :rtype: Tuple[str, float]
    """
    if step < big_model_threshold:
        log("[MODE] Utilisation du gros modèle (GPT-4)")
        return query_gpt4(prompt)
    else:
        log("[MODE] Utilisation du modèle local (Codestral)")
        return query_codestral_ollama(prompt)


def analyze_contracts(slith: str, observation: Dict[str, Any], step: int = 0) -> Dict[str, Any]:
    """
    Analyzes smart contracts using a language model to provide detailed insights on potential vulnerabilities,
    contract functionality, and exploitation requirements. The function constructs a prompt from the observation,
    queries a pre-trained policy language model for an analysis, and parses the response to return relevant details.

    :param slith: The slither analysis results to include in the prompt.
    :type slith: str
    :param observation:
        The input data required for the smart contract analysis.
        The dictionary should include human-readable information related to the target contracts.
    :param step:
        The current step or iteration of the analysis process. Default is 0.

    :return:
        A dictionary containing the following keys:
            - 'analysis_prompt': The constructed prompt sent to the language model.
            - 'analysis_raw_response': The raw result received from the model.
            - 'contract_analysis': Parsed insights into the contract's functionalities and properties.
            - 'vulnerability_assessment': Evaluation of potential weaknesses in the contract.
            - 'exploitation_requirements': Necessary conditions or steps for exploiting identified vulnerabilities.
            - 'analysis_duration': The elapsed time for querying and receiving the model's response.
    """
    # Build analysis prompt
    prompt = build_contract_analysis_prompt(slith, observation)

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
    Generates and returns a dictionary containing attack code and related details based on the
    provided observation, analysis results, and optional step input. The function constructs an
    analysis summary, prepares a prompt to request code from a language model, and parses the
    response to extract the resulting attack code and its type.

    :param observation: A dictionary containing observation data necessary for generating
        the attack prompt.
    :type observation: Dict[str, Any]
    :param analysis_result: A dictionary holding the results of contract analysis, which
        includes contract vulnerabilities and exploitation assessments.
    :type analysis_result: Dict[str, Any]
    :param step: An integer indicating the step number in the sequence of operations,
        defaulting to 0 if not provided.
    :type step: int
    :return: A dictionary containing the attack code prompt, raw response from the
        model, extracted code, code type, and the duration it took to generate the attack.
    :rtype: Dict[str, Any]
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


def generate_complete_attack_strategy(slith: str, observation: Dict[str, Any], step: int = 0) -> Dict[str, Any]:
    """
    Generates a complete attack strategy based on the analyzed contract vulnerabilities and the
    generated attack code. This process involves two primary steps: analyzing the contracts provided
    in the observation for vulnerabilities and then generating corresponding attack code. The function
    returns a dictionary containing analysis results, attack code details, and additional legacy fields
    as required by existing pipelines.

    :param slith: The slither analysis results to include in the prompt.
    :type slith: str
    :param observation: A dictionary containing the current state of the contracts or systems undergoing
        analysis. This serves as the input context for vulnerability detection and attack strategy
        generation.
    :type observation: Dict[str, Any]
    :param step: Indicates the current step in the pipeline process. Defaults to 0 if not explicitly
        provided, representing the start of the attack strategy generation workflow.
    :type step: int
    :return: A dictionary containing:
        - `analysis`: Results obtained from analyzing contract vulnerabilities.
        - `attack`: Results of the generated attack code.
        - `prompt`: The prompt used during contract analysis for legacy support.
        - `raw_response`: The raw response provided during contract analysis.
        - `reasoning`: Detailed reasoning extracted from contract analysis.
        - `summary`: A high-level assessment of the identified vulnerabilities.
        - `code`: Code generated as part of the attack strategy.
        - `code_type`: Type of the generated attack code.
        - `duration`: Total duration (in time) spent during analysis and attack code generation.
    :rtype: Dict[str, Any]
    """
    logger.info("Starting complete attack strategy generation")
    logger.info(f"Contract name: {observation['contracts'][0]['contract_name'] if observation['contracts'] else 'Unknown'}")
    logger.info(f"Using step number: {step} for model selection")

    # Step 1: Analyze contracts
    log("🔍 Step 1: Analyzing contracts for vulnerabilities...")
    analysis_start_time = time.time()
    analysis_result = analyze_contracts(slith, observation, step)
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
