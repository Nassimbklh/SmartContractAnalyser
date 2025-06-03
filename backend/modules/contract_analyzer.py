"""
Contract Analysis Module
Handles contract state analysis and observation building
"""

from typing import List, Dict, Any
from web3 import Web3


def log(msg: str):
    """Simple logging function"""
    print(msg)


def extract_events(abi: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract event information from ABI"""
    return [
        {"name": item['name'], "inputs": item['inputs']}
        for item in abi
        if item['type'] == 'event'
    ]


def extract_function_details(abi: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract detailed function information from ABI"""
    func_list = []

    for entry in abi:
        if entry['type'] == 'function':
            func_list.append({
                "name": entry['name'],
                "signature": f"{entry['name']}({', '.join(i['type'] for i in entry['inputs'])})",
                "inputs": entry['inputs'],
                "outputs": entry.get('outputs', []),
                "stateMutability": entry.get('stateMutability', ''),
                "payable": entry.get('stateMutability', '') == 'payable',
                "constant": entry.get('stateMutability', '') in ('view', 'pure'),
                "visibility": entry.get('visibility', 'public'),
                "modifiers": [m for m in entry.get('modifiers', [])]
            })

    return func_list


def get_accounts_balances(w3: Web3, addresses: List[str]) -> Dict[str, int]:
    """Get ETH balances for multiple addresses"""
    return {addr: w3.eth.get_balance(addr) for addr in addresses}


def get_public_getters_and_vars_state(w3: Web3, contract_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get current state of public variables and view functions

    Args:
        w3: Web3 instance
        contract_info: Contract information

    Returns:
        Dictionary of contract state
    """
    contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])
    state = {}

    for f in contract_info["abi"]:
        if f['type'] == 'function' and f.get('stateMutability', '') in ('view', 'pure'):
            try:
                if len(f['inputs']) == 0:
                    # No-argument view function
                    fn = contract.get_function_by_signature(f"{f['name']}()")
                    state[f['name']] = fn().call()
                elif len(f['inputs']) == 1:
                    # Single-argument view function
                    arg_type = f['inputs'][0]['type']
                    results = []

                    if arg_type == 'address':
                        # Try with first few accounts
                        for acct in w3.eth.accounts[:3]:
                            fn = contract.get_function_by_signature(f"{f['name']}(address)")
                            val = fn(acct).call()
                            results.append({"address": acct, "value": val})
                    elif arg_type.startswith('uint'):
                        # Try with small integers
                        for v in range(3):
                            fn = contract.get_function_by_signature(f"{f['name']}(uint256)")
                            val = fn(v).call()
                            results.append({"index": v, "value": val})
                    else:
                        results = "Type non pris en charge"

                    state[f['name']] = results
            except Exception:
                state[f['name']] = "N/A"

    return state


def build_multi_contract_observation(contract_group: List[Dict[str, Any]], w3: Web3) -> Dict[str, Any]:
    """
    Build comprehensive observation of multiple contracts

    Args:
        contract_group: List of contract information
        w3: Web3 instance

    Returns:
        Complete observation data
    """
    contracts_obs = []

    for ci in contract_group:
        # Prepare addresses (contract + first 3 accounts)
        addresses = [ci["address"]] + w3.eth.accounts[:3]

        # Build contract observation
        contract_obs = {
            "contract_name": ci["contract_name"],
            "address": ci["address"],
            "abi": ci["abi"],
            "functions": extract_function_details(ci["abi"]),
            "events": extract_events(ci["abi"]),
            "accounts_balances": get_accounts_balances(w3, addresses),
            "public_state": get_public_getters_and_vars_state(w3, ci),
            "source_code_snippet": ci["source_code"],
            "solc_version": ci["solc_version"]
        }

        contracts_obs.append(contract_obs)

    observation = {
        "filename": contract_group[0]["filename"],
        "contracts": contracts_obs
    }

    return observation
    return observation