"""
Contract Analysis Module
Handles contract state analysis and observation building
"""

from typing import List, Dict, Any
from web3 import Web3

def extract_events(abi: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts events from a given ABI (Application Binary Interface).

    This function scans through the provided list of ABI items, filters
    out items that represent blockchain events, and constructs a list
    of dictionaries containing the event's name and its inputs.

    :param abi: A list of dictionaries where each dictionary represents
        an item in the ABI. Each item must include a "type" key
        (indicating the type of ABI item) and an "inputs" key (defining
        the inputs for that ABI item). Additionally, for event-type items,
        the "name" key is required to specify the event name.
    :return: A list of dictionaries where each dictionary represents an
        event from the ABI. Each dictionary contains the "name" of the
        event and its "inputs".
    """
    return [
        {"name": item['name'], "inputs": item['inputs']} 
        for item in abi 
        if item['type'] == 'event'
    ]


def extract_function_details(abi: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts details of functions from a given ABI (Application Binary Interface).

    This function processes a provided list of dictionary entries representing
    an ABI and filters out those entries with a 'type' of 'function'. It then
    extracts relevant details including the name, signature, inputs, outputs,
    state mutability, and other properties. All extracted information is
    compiled into a list of dictionaries for each function.

    :param abi: A list of dictionaries, each representing an element of the ABI.
                Each dictionary must contain at least the 'type' key, and if that
                value is 'function', additional keys such as `name`, `inputs`,
                and optional keys like `outputs` or `stateMutability` may be used.
    :type abi: List[Dict[str, Any]]

    :return: A list of dictionaries, each containing details of a function in the ABI.
             Keys in each dictionary include:
             - 'name': The name of the function.
             - 'signature': The function signature including input types.
             - 'inputs': The list of input types and details.
             - 'outputs': The list of outputs, if any.
             - 'stateMutability': The mutability state of the function.
             - 'payable': A boolean indicating if the function accepts payments.
             - 'constant': A boolean indicating if the function is view or pure.
             - 'visibility': The visibility of the function (default to 'public').
             - 'modifiers': The list of specified modifiers, if any.
    :rtype: List[Dict[str, Any]]
    """
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
    """
    Retrieves the balances for a list of addresses from a Web3 provider.

    This function connects to a Web3 instance and fetches the Ether balance for each address
    provided in the list of addresses. It returns a dictionary mapping each address to its
    corresponding balance in Wei.

    :param w3: A Web3 instance used to interact with the Ethereum blockchain.
    :param addresses: A list of Ethereum addresses for which balances are to be retrieved.
    :return: A dictionary mapping each Ethereum address to its balance in Wei.
    """
    return {addr: w3.eth.get_balance(addr) for addr in addresses}


# 1. CORRECTION DANS modules/contract_analyzer.py
# Ajouter une vérification de balance ETH réelle du contrat

def get_public_getters_and_vars_state(w3: Web3, contract_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and returns the state of public getters and variable states for a specific Ethereum contract.
    This function interacts with the Ethereum blockchain to retrieve data from a contract's public
    read-only functions (view or pure) and gathers their outputs into a dictionary format. It also
    includes the ETH balance of the contract in the result.

    :param w3: An instance of the Web3 class used to interact with an Ethereum node.
    :type w3: Web3
    :param contract_info: A dictionary containing information about the contract. Must include `address`
        (Ethereum address of the contract as a string) and `abi` (ABI of the contract as a list).
    :type contract_info: Dict[str, Any]
    :return: A dictionary containing the Ethereum contract's public getter functions and variable states.
        The key-value pairs represent the names of the functions/variables and their corresponding values
        or results. Includes additional keys for the contract's ETH balance in both Wei and Ether.
    :rtype: Dict[str, Any]
    """
    contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])
    state = {}

    # NOUVEAU: Ajouter la balance ETH réelle du contrat
    contract_eth_balance = w3.eth.get_balance(contract_info["address"])
    state["_contract_eth_balance_wei"] = contract_eth_balance
    state["_contract_eth_balance_eth"] = w3.from_wei(contract_eth_balance, 'ether')

    for f in contract_info["abi"]:
        if f['type'] == 'function' and f.get('stateMutability', '') in ('view', 'pure'):
            try:
                if len(f['inputs']) == 0:
                    # No-argument view function
                    fn = contract.get_function_by_signature(f"{f['name']}()")
                    result = fn().call()
                    state[f['name']] = result

                    print(f"Contract has {state['_contract_eth_balance_eth']} ETH")

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

                            # DEBUGGING: Pour les fonctions de balance
                            if f['name'].lower() in ['balances', 'getbalance', 'balance']:
                                print(f"🔍 {f['name']}({acct}) = {val}")

                    elif arg_type.startswith('uint'):
                        # Try with small integers
                        for v in range(3):
                            fn = contract.get_function_by_signature(f"{f['name']}(uint256)")
                            val = fn(v).call()
                            results.append({"index": v, "value": val})
                    else:
                        results = "Type non pris en charge"

                    state[f['name']] = results
            except Exception as e:
                state[f['name']] = f"ERROR: {e}"

    return state


def build_multi_contract_observation(contract_group: List[Dict[str, Any]], w3: Web3) -> Dict[str, Any]:
    """
    Builds a multi-contract observation by processing a group of smart contracts
    and extracting relevant details such as functions, events, state variables,
    and account balances.

    This function processes a list of smart contract metadata and extracts
    information from each contract's ABI, address, and associated state.
    It utilizes Web3 to interact with the blockchain and retrieve account
    balances and state variables.

    :param contract_group: A list of dictionaries representing the contract group
        to be processed. Each dictionary should contain metadata such as
        contract address, ABI, source code, and Solidity compiler version.
    :param w3: Web3 instance used to interact with the blockchain.
    :return: A dictionary with keys 'filename' and 'contracts'. The 'filename'
        field contains the name of the file associated with the contract group.
        The 'contracts' field is a list of dictionaries, each containing detailed
        observations of its respective contract.
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


# 4. FONCTION DE DEBUG POUR ANALYSER LES BALANCES
def debug_contract_balances(w3: Web3, contract_info: Dict[str, Any]):
    """
    Debugs balances for a given Ethereum smart contract by analyzing its ETH balance and
    checking balance-related functions in its ABI.

    This function performs the following tasks:
    1. Retrieves and logs the actual ETH balance of the contract.
    2. Identifies and lists functions in the contract's ABI that are related to balances.
    3. Executes these balance-related functions, where applicable, and logs their results.

    :param w3: A Web3 instance connected to an Ethereum node, used for contract interactions.
    :type w3: Web3
    :param contract_info: A dictionary containing contract details, including "address", "abi",
        and "contract_name".
    :type contract_info: Dict[str, Any]
    :return: None
    :rtype: None
    """
    contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])

    print(f"\n🔍 === DEBUG BALANCES for {contract_info['contract_name']} ===")

    # 1. Balance ETH réelle du contrat
    eth_balance = w3.eth.get_balance(contract_info["address"])
    print(f"💰 Contract ETH balance: {w3.from_wei(eth_balance, 'ether')} ETH ({eth_balance} wei)")

    # 2. Vérifier les fonctions de balance dans l'ABI
    balance_functions = []
    for f in contract_info["abi"]:
        if f['type'] == 'function' and 'balance' in f['name'].lower():
            balance_functions.append(f)

    print(f"🔧 Balance-related functions found: {[f['name'] for f in balance_functions]}")

    # 3. Appeler ces fonctions pour voir ce qu'elles retournent
    for f in balance_functions:
        try:
            if len(f.get('inputs', [])) == 0:
                fn = contract.get_function_by_signature(f"{f['name']}()")
                result = fn().call()
                print(f"📊 {f['name']}() = {result}")
            elif len(f.get('inputs', [])) == 1 and f['inputs'][0]['type'] == 'address':
                for i, acct in enumerate(w3.eth.accounts[:3]):
                    fn = contract.get_function_by_signature(f"{f['name']}(address)")
                    result = fn(acct).call()
                    print(f"📊 {f['name']}(account[{i}]) = {result}")
        except Exception as e:
            print(f"❌ Error calling {f['name']}: {e}")

    print("=== END DEBUG BALANCES ===\n")