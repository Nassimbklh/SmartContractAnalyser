"""
Attack Execution Module
Handles execution of generated Solidity attack code
"""

from typing import List, Dict, Any
from web3 import Web3
from solcx import compile_standard


def log(msg: str):
    """Simple logging function"""
    print(msg)


def compile_and_deploy_attack_contract(attack_source: str, w3: Web3, target_address: str):
    """Compile and deploy attack contract"""
    file_name = "LLM_Attacker.sol"
    compiled = compile_standard({
        "language": "Solidity",
        "sources": {file_name: {"content": attack_source}},
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}
        }
    })

    contracts = compiled["contracts"][file_name]
    contract_name = list(contracts.keys())[0]
    abi = contracts[contract_name]["abi"]
    bytecode = contracts[contract_name]["evm"]["bytecode"]["object"]

    acct = w3.eth.accounts[1]
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = Contract.constructor(target_address).transact({'from': acct})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    address = tx_receipt.contractAddress

    return address, abi, bytecode


def find_attack_function_robust(abi: List[Dict[str, Any]]):
    """Find the main attack function in the contract"""
    # Look for functions with attack-related names
    for fn in abi:
        if fn['type'] == 'function':
            if any(x in fn['name'].lower() for x in ["attack", "exploit", "run"]):
                return fn['name'], fn.get('inputs', [])

    # Fallback to first function with no inputs
    for fn in abi:
        if fn['type'] == 'function' and len(fn.get('inputs', [])) == 0:
            return fn['name'], []

    return None, []


def build_attack_args(inputs: List[Dict[str, Any]], w3: Web3):
    """Build arguments for attack function"""
    args = []
    for inp in inputs:
        t = inp['type']
        n = inp['name'].lower()

        if 'deposit' in n:
            args.append(w3.to_wei(2, 'ether'))
        elif 'withdraw' in n:
            args.append(w3.to_wei(2, 'ether'))
        elif 'attack' in n or 'round' in n or 'max' in n or 'count' in n:
            args.append(3)
        elif t.startswith('uint'):
            args.append(1)
        else:
            args.append(0)

    return args


def try_attack_super_generic(attack_address: str, attack_abi: List[Dict[str, Any]], w3: Web3):
    """Execute attack function"""
    attacker = w3.eth.contract(address=attack_address, abi=attack_abi)
    acct = w3.eth.accounts[1]

    fn_name, inputs = find_attack_function_robust(attack_abi)
    if fn_name is None:
        return False, fn_name, []

    args = build_attack_args(inputs, w3)

    # Check if function is payable
    is_payable = False
    for fn in attack_abi:
        if fn['type'] == 'function' and fn['name'] == fn_name:
            if fn.get('stateMutability', '') == 'payable' or fn.get('payable', False):
                is_payable = True

    # Prepare transaction
    tx_dict = {'from': acct}
    if is_payable:
        for i, inp in enumerate(inputs):
            if 'deposit' in inp['name'].lower() and inp['type'].startswith('uint'):
                tx_dict['value'] = args[i]
                break
        else:
            tx_dict['value'] = w3.to_wei(2, 'ether')
    else:
        tx_dict['value'] = 0

    try:
        fn = getattr(attacker.functions, fn_name)
        tx = fn(*args).transact(tx_dict)
        w3.eth.wait_for_transaction_receipt(tx)
        log(f"✅ Attack function {fn_name} called with args {args} (payable={is_payable})")
        return True, fn_name, args
    except Exception as e:
        log(f"❌ Attack failed: {e}")
        return False, fn_name, args


def measure_exploit_success(w3: Web3, contract_info: Dict[str, Any], attacker_address: str):
    """Measure attack success by checking balances"""
    contract_balance = w3.eth.get_balance(contract_info["address"])
    attacker_balance = w3.eth.get_balance(attacker_address)
    return attacker_balance, contract_balance


def execute_attack_on_contracts(code: str, contract_group: List[Dict[str, Any]], w3: Web3,
                                code_type: str = "solidity") -> Dict[str, Any]:
    """
    Execute Solidity attack code on contracts

    Args:
        code: Solidity attack code
        contract_group: List of target contracts
        w3: Web3 instance
        code_type: Type of code (only solidity supported)

    Returns:
        Attack execution results
    """
    if not code:
        return {"success": False, "error": "No code provided"}

    if not code_type.lower().startswith("solidity"):
        return {"success": False, "error": "Only Solidity attacks are supported"}

    # Execute attack
    result = {
        "success": False,
        "error": None,
        "attack_fn": None,
        "attack_args": None,
        "attacker_balance": None,
        "contract_balance": None
    }

    try:
        for ci in contract_group:
            attack_address, attack_abi, _ = compile_and_deploy_attack_contract(code, w3, ci["address"])
            success, fn_name, args = try_attack_super_generic(attack_address, attack_abi, w3)
            attacker_balance, contract_balance = measure_exploit_success(w3, ci, attack_address)

            result = {
                "success": success,
                "attack_fn": fn_name,
                "attack_args": args,
                "attacker_balance": attacker_balance,
                "contract_balance": contract_balance,
                "target_contract": ci["contract_name"]
            }

            if success:
                break

    except Exception as e:
        result["error"] = str(e)

    return result