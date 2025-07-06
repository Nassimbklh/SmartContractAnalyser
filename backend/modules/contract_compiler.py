"""
Contract Compilation Module
Handles Solidity contract compilation with automatic version detection
"""

import os
import re
from typing import List, Dict, Any
from solcx import (
    compile_standard, install_solc, set_solc_version,
    get_installed_solc_versions
)

def extract_solc_version(source_code: str) -> str:
    """
    Extracts the Solidity compiler version from the provided source code string.

    The function attempts to find and return the Solidity compiler version specified
    in the pragma directive within the source code. If no version is found, it returns
    a default version (0.8.20).

    :param source_code: The Solidity source code as a string.
    :type source_code: str
    :return: The extracted Solidity compiler version or a default version if not found.
    :rtype: str
    """
    match = re.search(r'pragma\s+solidity\s+(\^?)([\d\.]+)', source_code)
    if match:
        return match.group(2)
    # Return a default version if no pragma directive is found
    return '0.8.20'

def clean_bytecode(bytecode: str) -> str:
    """
    Cleans and formats a given bytecode string by removing any substrings enclosed between
    double underscores and ensuring that the bytecode starts with "0x". This ensures
    uniformity in the representation of bytecode strings.

    :param bytecode: The input bytecode string that needs to be cleaned and formatted.
    :type bytecode: str
    :return: A formatted bytecode string starting with "0x" and without enclosed substrings
        with double underscores.
    :rtype: str
    """
    bytecode = re.sub(r'__[^_]+__+', '', bytecode)
    if not bytecode.startswith("0x"):
        bytecode = "0x" + bytecode
    return bytecode


def read_contract_file(filepath: str) -> str:
    """
    Reads the contents of a text file using multiple encodings in case of
    decoding issues. The function iterates through a predefined list of
    encodings, attempting to read the file until successful. If none of the
    encodings work, an exception is raised indicating the failure.

    :param filepath: The path to the text file to be read.
    :type filepath: str
    :return: The content of the text file as a string.
    :rtype: str
    :raises Exception: If the file cannot be read using the predefined encodings.
    """
    encodings = ['utf-8', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue

    raise Exception(f"Impossible de lire le fichier avec encodages {encodings}")


def ensure_solc_version(version: str) -> bool:
    """
    Ensures that the specified Solidity compiler version is installed on the system. If the
    specified version is not installed, it attempts to install it.

    :param version: The Solidity compiler version to ensure is installed.
    :type version: str
    :return: A boolean indicating whether the specified version of the Solidity compiler
             is successfully installed or already available.
    :rtype: bool
    """
    installed_versions = [str(v) for v in get_installed_solc_versions()]

    if version not in installed_versions:
        print(f"⏳ Installation de solc {version} ...")
        try:
            install_solc(version)
            return True
        except Exception as e:
            raise Exception(f"⚠️ Impossible d'installer solc {version}: {e}")

    return True


def compile_contracts(filepath: str) -> List[Dict[str, Any]]:
    """
    Compiles all Solidity contracts found in the given source file. This function
    reads a Solidity source file, extracts the required compiler version from the file, ensures
    that the correct `solc` version is installed, and uses it to compile the contracts. It parses
    the ABI and bytecode of the compiled contracts and returns the results.

    :param filepath: Path to the Solidity source file to be compiled.
    :type filepath: str
    :return: A list of dictionaries, each containing details of compiled contracts including
        contract name, ABI, bytecode, source code, Solidity version, and filename.
    :rtype: List[Dict[str, Any]]
    """
    try:
        # Read source code
        source_code = read_contract_file(filepath)

        # Extract and install Solidity version
        solc_version = extract_solc_version(source_code)

        if not ensure_solc_version(solc_version):
            raise Exception(f"❌ Cannot compile {filepath} - solc version not available")

        # Set Solidity version
        set_solc_version(solc_version)

        # Prepare compilation input
        file_name = os.path.basename(filepath)
        compile_input = {
            "language": "Solidity",
            "sources": {file_name: {"content": source_code}},
            "settings": {
                "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}
            }
        }

        # Compile
        print(f"🔧 Compiling {file_name} with solc {solc_version}...")
        compiled = compile_standard(compile_input)

        # Parse results
        results = []
        contracts = compiled["contracts"][file_name]

        for contract_name, contract_data in contracts.items():
            abi = contract_data["abi"]
            raw_bytecode = contract_data["evm"]["bytecode"]["object"]
            bytecode = clean_bytecode(raw_bytecode)

            # Skip contracts without bytecode (interfaces, abstracts)
            if not bytecode or bytecode == "0x":
                print(f"⏩ Skipped {contract_name} (no bytecode)")
                continue

            contract_info = {
                "filename": file_name,
                "contract_name": contract_name,
                "abi": abi,
                "bytecode": bytecode,
                "source_code": source_code,
                "solc_version": solc_version
            }

            results.append(contract_info)
            print(f"✅ {contract_name} compiled successfully")

        return results

    except Exception as e:
        raise Exception(f"❌ Compilation Error: {filepath} : {e}")


def extract_constructor_inputs(abi: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts the input parameters of a constructor from a contract's ABI (Application Binary Interface).

    This function iterates through the provided ABI definition to locate the constructor,
    if it exists, and extracts its input parameters. The constructor is a special function
    in smart contracts that is invoked only once, during contract deployment. If no constructor
    is defined in the ABI, an empty list is returned.

    :param abi: The ABI of the contract, represented as a list of dictionaries where each
        dictionary defines a function, event, or constructor of the contract.
    :type abi: List[Dict[str, Any]]

    :return: A list of dictionaries, each representing an input parameter of the constructor.
        Each dictionary contains details like `name`, `type`, and other metadata relevant
        to the constructor's input parameters.
    :rtype: List[Dict[str, Any]]
    """
    for item in abi:
        if item.get('type') == 'constructor':
            return item.get('inputs', [])
    return []


def find_setup_functions(abi: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identifies and retrieves a list of functions from the provided ABI that match
    any of the predefined setup-related keywords in their name. The function is
    useful for extracting contract setup functions from a blockchain contract's ABI.

    :param abi: The ABI (Application Binary Interface) of the contract, which is a
        list of dictionaries where each dictionary describes a function or element
        of the contract.
    :type abi: List[Dict[str, Any]]
    :return: A list of dictionaries, where each dictionary corresponds to a
        function in the ABI whose name contains any of the specified setup-related
        keywords.
    :rtype: List[Dict[str, Any]]
    """
    setup_words = ["init", "setup", "register", "mint", "whitelist", "add", "open", "start", "set"]
    return [
        f for f in abi 
        if f['type'] == 'function' and 
        any(word in f['name'].lower() for word in setup_words)
    ]


def is_exploitable_target(contract_info: Dict[str, Any]) -> bool:
    """
    Determines if a given contract is a potentially exploitable target based on specific
    naming heuristics, the presence of payable functions, or functions dealing with
    balances, funds, or jackpots. The function filters out safe utility contracts and
    focuses on identifying business logic contracts that may involve financial operations.

    :param contract_info: A dictionary containing information about a smart contract.
                          Expected keys are:
                          - 'contract_name': A string representing the name of the contract.
                          - 'abi': A list of dictionaries defining the contract's ABI
                                  (Application Binary Interface), where each dictionary
                                  represents a function definition or other ABI component.
    :return: A boolean value. Returns True if the contract is identified as a potentially
             exploitable target, otherwise False.
    """
    important_names = [
        "wallet", "bank", "dao", "crowdsale", "lottery", "fund", "proxy", 
        "casino", "exchange", "ico", "sale", "pool", "staking"
    ]
    safe_names = [
        "erc20", "standardtoken", "safemath", "ownable", "tokenbasic", 
        "erc20basic", "math", "util", "interface", "library", "recipient"
    ]

    name = contract_info["contract_name"].lower()

    # Skip safe utility contracts
    if any(n in name for n in safe_names):
        return False

    # Include important business logic contracts
    if any(n in name for n in important_names):
        return True

    # Check for payable functions
    for f in contract_info["abi"]:
        if f['type'] == 'function' and f.get('stateMutability', '') == 'payable':
            return True

    # Check for balance/fund related functions
    if any(
        "balance" in v['name'].lower() or 
        "fund" in v['name'].lower() or 
        "jackpot" in v['name'].lower() 
        for v in contract_info["abi"] 
        if v['type'] == "function"
    ):
        return True

    return False
