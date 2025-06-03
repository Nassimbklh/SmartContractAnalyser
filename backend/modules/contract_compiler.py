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


def log(msg: str):
    """Simple logging function"""
    print(msg)


def extract_solc_version(source_code: str) -> str:
    """Extract Solidity version from pragma statement"""
    match = re.search(r'pragma\s+solidity\s+(\^?)([\d\.]+)', source_code)
    if match:
        return match.group(2)
    return ''


def clean_bytecode(bytecode: str) -> str:
    """Clean bytecode by removing library placeholders and adding 0x prefix"""
    bytecode = re.sub(r'__[^_]+__+', '', bytecode)
    if not bytecode.startswith("0x"):
        bytecode = "0x" + bytecode
    return bytecode


def read_contract_file(filepath: str) -> str:
    """Read contract file with multiple encoding attempts"""
    encodings = ['utf-8', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue

    raise Exception(f"Impossible de lire le fichier avec encodages {encodings}")


def ensure_solc_version(version: str) -> bool:
    """Ensure Solidity compiler version is installed"""
    installed_versions = [str(v) for v in get_installed_solc_versions()]

    if version not in installed_versions:
        log(f"⏳ Installation de solc {version} ...")
        try:
            install_solc(version)
            return True
        except Exception as e:
            log(f"⚠️ Impossible d'installer solc {version}: {e}")
            return False

    return True


def compile_and_deploy_all_contracts(filepath: str) -> List[Dict[str, Any]]:
    """
    Compile all contracts from a Solidity file

    Args:
        filepath: Path to the .sol file

    Returns:
        List of compiled contract information
    """
    try:
        # Read source code
        source_code = read_contract_file(filepath)

        # Extract and install Solidity version
        solc_version = extract_solc_version(source_code)

        if not ensure_solc_version(solc_version):
            log(f"❌ Cannot compile {filepath} - solc version not available")
            return []

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
        log(f"🔧 Compiling {file_name} with solc {solc_version}...")
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
                log(f"⏩ Skipped {contract_name} (no bytecode)")
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
            log(f"✅ {contract_name} compiled successfully")

        return results

    except Exception as e:
        log(f"❌ Compilation Error: {filepath} : {e}")
        return []


def extract_constructor_inputs(abi: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract constructor inputs from ABI"""
    for item in abi:
        if item.get('type') == 'constructor':
            return item.get('inputs', [])
    return []


def find_setup_functions(abi: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find potential setup/initialization functions"""
    setup_words = ["init", "setup", "register", "mint", "whitelist", "add", "open", "start", "set"]
    return [
        f for f in abi
        if f['type'] == 'function' and
           any(word in f['name'].lower() for word in setup_words)
    ]


def is_exploitable_target(contract_info: Dict[str, Any]) -> bool:
    """
    Determine if a contract is a potential exploit target

    Args:
        contract_info: Contract information dictionary

    Returns:
        True if contract is exploitable target, False otherwise
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