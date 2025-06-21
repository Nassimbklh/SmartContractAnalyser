"""
Attack Execution Module
Handles execution of generated Solidity attack code
"""

from typing import List, Dict, Any
from web3 import Web3
from solcx import compile_standard


def log(msg: str):
    """
    Logs a message to the standard output. The function takes a string-based message
    and prints it directly to the standard output, primarily useful for simple logging.

    :param msg: The message to be printed to the output.
    :type msg: str
    :return: None
    """
    print(msg)


def compile_and_deploy_attack_contract(attack_source: str, w3: Web3, target_address: str):
    """
    Compiles and deploys a Solidity attack contract to a target address. This function
    uses a Solidity source code string, compiles it, deploys the resulting bytecode
    to the Ethereum blockchain using the provided Web3 instance, and optionally funds
    the deployed contract with Ether.

    :param attack_source: The Solidity source code of the attack contract.
    :type attack_source: str
    :param w3: An instance of the Web3 client used for interaction with the Ethereum blockchain.
    :type w3: Web3
    :param target_address: The address of the target to which the attack contract will interact.
    :type target_address: str
    :return: A tuple containing the contract address, the contract ABI, and the bytecode of the contract.
    :rtype: tuple[str, ABI, str]
    """
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

    # NOUVEAU: Envoyer de l'ETH au contrat attaquant pour les gas et appels
    try:
        fund_tx = w3.eth.send_transaction({
            'from': acct,
            'to': address,
            'value': w3.to_wei(5, 'ether')  # 5 ETH pour l'attaquant
        })
        w3.eth.wait_for_transaction_receipt(fund_tx)

        attacker_balance = w3.eth.get_balance(address)
        log(f"💰 Attacker contract funded with {w3.from_wei(attacker_balance, 'ether')} ETH")
    except Exception as e:
        log(f"⚠️  Failed to fund attacker contract: {e}")

    return address, abi, bytecode


def find_attack_function_robust(abi: List[Dict[str, Any]]):
    """
    Finds an attack-related function in a smart contract's ABI.

    This function scans the provided ABI (Application Binary Interface) for functions that
    have names indicating a potential attack, such as "attack", "exploit", or "run". If no
    such function is found, it falls back to identifying the first function with no inputs.

    :param abi: The ABI of the smart contract, provided as a list of dictionaries. Each dictionary
        should define details about a function, including its type, name, and optionally its inputs.
    :return: A tuple where the first element is the name of the identified function (or None if
        no function is found), and the second element is a list detailing the inputs to that
        function (or an empty list if there are no inputs or if no function is found).
    :rtype: Tuple[Optional[str], List[Dict[str, Any]]]
    """
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
    """
    Builds and returns a list of arguments to be used for constructing an "attack" function call
    based on provided input parameters and specified type conditions. Each argument is determined
    dynamically by inspecting the properties of the elements within the inputs list and applying
    predefined rules.

    :param inputs: A list of dictionaries where each dictionary represents a function parameter
        with its attributes such as 'type' and 'name'.
    :type inputs: List[Dict[str, Any]]
    :param w3: An instance of the Web3 object used for blockchain interactions, particularly
        for converting Ether denominations to Wei.
    :type w3: Web3
    :return: A list of dynamically calculated arguments based on input properties and preset
        conditions.
    :rtype: List[Any]
    """
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
    """
    Attempts to execute an attack function on a target smart contract. This function identifies
    and calls the most likely attack function in the given contract ABI, providing necessary
    arguments and ensuring gas requirements are met. If the attack function is payable, it also
    handles sending ETH as needed.

    The process includes verifying the attacker's contract balance, identifying a suitable
    function, preparing transaction details, and executing the function. Outcomes from the attack
    are logged, including success, failure, and gas usage.

    :param attack_address: Address of the smart contract to attack
    :type attack_address: str
    :param attack_abi: ABI (Application Binary Interface) of the contract to attack
    :type attack_abi: List[Dict[str, Any]]
    :param w3: Web3 instance connected to the blockchain
    :type w3: Web3
    :return: A tuple indicating whether the attack succeeded, name of the function called, and the arguments used.
    :rtype: Tuple[bool, Optional[str], List[Any]]
    """
    attacker = w3.eth.contract(address=attack_address, abi=attack_abi)
    acct = w3.eth.accounts[1]

    # Vérifier que l'attaquant a de l'ETH
    attacker_balance = w3.eth.get_balance(attack_address)
    log(f"💰 Attacker balance before attack: {w3.from_wei(attacker_balance, 'ether')} ETH")

    if attacker_balance == 0:
        log("⚠️  WARNING: Attacker contract has no ETH for gas/calls!")

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

    # Prepare transaction avec plus d'ETH si nécessaire
    tx_dict = {'from': acct, 'gas': 500000}  # Augmenter la limite de gas

    if is_payable:
        # Si la fonction d'attaque est payable, on peut envoyer de l'ETH
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
        receipt = w3.eth.wait_for_transaction_receipt(tx)

        log(f"✅ Attack function {fn_name} called with args {args} (payable={is_payable})")
        log(f"⛽ Gas used: {receipt.gasUsed:,}")

        return True, fn_name, args
    except Exception as e:
        log(f"❌ Attack failed: {e}")

        # Plus de debugging si l'attaque échoue
        final_attacker_balance = w3.eth.get_balance(attack_address)
        log(f"💰 Attacker balance after failed attack: {w3.from_wei(final_attacker_balance, 'ether')} ETH")

        return False, fn_name, args


def measure_exploit_success(w3: Web3, contract_info: Dict[str, Any], attacker_address: str):
    """
    Measures the success of an exploit by comparing the balance of the attacker
    to the balance of the targeted contract.

    This function retrieves the current Ether balance of the given contract
    and the attacker, and then returns these values for further analysis.

    :param w3: A Web3 instance used to interact with the Ethereum blockchain.
    :param contract_info: A dictionary containing information about the contract,
        including its address.
    :param attacker_address: The Ethereum address of the attacker.
    :return: A tuple containing the attacker's balance and the contract's balance.
    :rtype: tuple
    """
    contract_balance = w3.eth.get_balance(contract_info["address"])
    attacker_balance = w3.eth.get_balance(attacker_address)
    return attacker_balance, contract_balance


def execute_attack_on_contracts(code: str, contract_group: List[Dict[str, Any]], w3: Web3, code_type: str = "solidity") -> Dict[str, Any]:
    """
    Executes an attack on a group of contracts using the provided code and identifies its success.

    This function compiles the given code, deploys a corresponding attack contract, and attempts
    to exploit the target smart contracts provided in `contract_group`. For each target contract,
    it tests the attack strategy and measures balances to verify the exploit's success. The execution
    halts upon the first successful exploit.

    :param code: The attack code in Solidity, used to compile the attack contract.
                 Must be non-empty.
    :type code: str
    :param contract_group: A list of dictionaries containing details of the target contracts.
                           Each dictionary should include the contract address and name as keys.
                           Example key names expected: `address`, `contract_name`.
    :type contract_group: List[Dict[str, Any]]
    :param w3: A Web3 instance connected to the pertinent blockchain network for
               deploying and testing the attack.
    :type w3: Web3
    :param code_type: The type of the provided `code`. Defaults to "solidity". Other
                      types (if any) are not supported.
    :type code_type: str
    :return: A dictionary containing the status and details of the attack attempt. The
             dictionary includes success status, error messages (if any), information on
             the attack function, and balance changes on success.
             Keys in the dictionary include:
             - "success" (bool): Whether the attack succeeded.
             - "error" (str or None): Error message if the execution failed.
             - "attack_fn" (str or None): Name of the attack function used.
             - "attack_args" (Any): Arguments passed to the attack function.
             - "attacker_balance" (Any): Attacker contract's balance post-attack.
             - "contract_balance" (Any): Target contract's balance post-attack.
             - "target_contract" (str or None): Name of the target contract exploited.
    :rtype: Dict[str, Any]
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
