"""
Contract Deployment Module
Handles smart contract deployment and setup
"""

import openai
from typing import List, Dict, Any, Tuple
from web3 import Web3
from .contract_compiler import compile_contracts

def compile_and_deploy_all_contracts(filepath: str) -> List[Dict[str, Any]]:
    """
    Compiles all contracts in the given file and deploys them to the blockchain.

    This function combines the compilation and deployment processes. It first compiles
    all contracts found in the specified file using the compile_contracts function,
    then deploys each compiled contract using the deploy_contract function.

    :param filepath: Path to the Solidity source file to be compiled and deployed.
    :type filepath: str
    :return: A list of dictionaries, each containing details of deployed contracts.
    :rtype: List[Dict[str, Any]]
    """
    try:
        # Set up Web3 connection to Ganache
        ganache_url = "http://ganache:8545"
        w3 = Web3(Web3.HTTPProvider(ganache_url))

        # Compile all contracts in the file
        compiled_contracts = compile_contracts(filepath)

        # Deploy each contract
        deployed_contracts = []
        for contract_info in compiled_contracts:
            deployed_contract = deploy_contract(contract_info, w3)
            if deployed_contract:
                deployed_contracts.append(deployed_contract)

        return deployed_contracts
    except Exception as e:
        print(f"❌ Compilation and deployment error: {e}")
        return []

def prompt_llm_for_args(fn_abi: Dict[str, Any], context_info: str = "", model: str = "gpt-4.1-nano") -> List:
    """
    Generates a valid Python array with argument values for a Solidity function call based on
    its ABI and context. This function utilizes language model prompts to provide valid
    argument suggestions and performs necessary type casting and validation.

    :param fn_abi: A dictionary representation of the function's Solidity ABI, including
                   its name and input parameters.
    :type fn_abi: Dict[str, Any]
    :param context_info: Additional contextual information or instructions for tailoring the
                         prompt sent to the language model.
    :type context_info: str, optional
    :param model: The name of the language model used for generating the prompt response.
                  Defaults to "gpt-4.1-nano".
    :type model: str, optional
    :return: A list of Python arguments correctly cast and validated according to the Solidity
             function's ABI input specifications.
    :rtype: List
    """
    fn_name = fn_abi.get('name', 'constructor')
    abi_inputs = fn_abi.get('inputs', [])

    type_map = {
        'uint256': 'int',
        'int': 'int',
        'address': 'str',
        'address[]': 'list',
        'string': 'str',
        'bool': 'bool',
        'bytes32': 'str'
    }

    # Create clear prompt for LLM
    type_guide = ", ".join([
        f"{inp['name']} ({inp['type']}) = {type_map.get(inp['type'], 'str')}" 
        for inp in abi_inputs
    ])

    prompt = (
        f"Je dois appeler la fonction '{fn_name}' d'un smart contract Solidity. "
        f"Voici les arguments attendus (type Python): {type_guide}. "
        f"Donne-moi un array Python contenant des arguments valides dans le bon ordre et le bon type, ex: [123, 'alice', '0x123...']. "
        f"Réponds uniquement par l'array Python, sans texte, sans commentaire."
    )

    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )
        txt = response.choices[0].message.content

        # Parse and cast arguments
        args = eval(txt) if "[" in txt else []
        casted = []

        for val, inp in zip(args, abi_inputs):
            typ = inp['type']
            if typ.startswith('uint') or typ.startswith('int'):
                try:
                    casted.append(int(val))
                except:
                    casted.append(1)
            elif typ == "bool":
                if isinstance(val, bool):
                    casted.append(val)
                elif isinstance(val, str) and val.lower() in ["true", "1"]:
                    casted.append(True)
                else:
                    casted.append(False)
            elif typ == "address":
                try:
                    if isinstance(val, str) and Web3.is_checksum_address(val):
                        casted.append(val)
                    elif isinstance(val, str) and val.startswith("0x") and len(val) == 42:
                        casted.append(Web3.to_checksum_address(val))
                    else:
                        casted.append(Web3.to_checksum_address("0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf"))
                except:
                    casted.append(Web3.to_checksum_address("0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf"))
            elif typ == "address[]":
                if isinstance(val, list):
                    l = []
                    for a in val:
                        if isinstance(a, str) and a.startswith("0x") and len(a) == 42:
                            l.append(Web3.to_checksum_address(a))
                        else:
                            l.append(Web3.to_checksum_address("0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf"))
                    casted.append(l)
                else:
                    casted.append([Web3.to_checksum_address("0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf")])
            elif typ == "bytes32":
                if isinstance(val, str) and val.startswith("0x") and len(val) == 66:
                    casted.append(val)
                elif isinstance(val, str):
                    casted.append(val.encode("utf-8").ljust(32, b'\x00')[:32])
                else:
                    casted.append("KEY".encode("utf-8").ljust(32, b'\x00'))
            elif typ == "string" or typ.startswith("bytes"):
                casted.append(str(val))
            else:
                casted.append(val)

        return casted

    except Exception as e:
        # Fallback with default values
        return [
            "0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf" if inp['type'] == "address" else
            ["0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf"] if inp['type'] == "address[]" else
            "KEY" if inp['type'] == "bytes32" else
            1 if "uint" in inp['type'] else
            "test" if inp['type'] == "string" else
            False if inp['type'] == "bool" else
            0
            for inp in abi_inputs
        ]


def deploy_contract(contract_info: Dict[str, Any], w3: Web3) -> Dict[str, Any]:
    """
    Deploys a smart contract on the Ethereum blockchain based on provided contract
    information and Web3 connection. This function handles the constructor arguments
    using an external prompt-based inference, deploys the contract, fetches the
    transaction receipt, and updates the contract information with deployment
    details including the contract address, transaction hash, block number, and
    gas used.

    :param contract_info: Dictionary containing the contract's ABI, bytecode, and
        contract name. It may include any additional required metadata for the
        deployment process.
    :type contract_info: Dict[str, Any]
    :param w3: Instance of Web3 used for deploying the contract and interacting
        with the Ethereum blockchain.
    :type w3: Web3
    :return: Updated contract information dictionary with deployment details
        including the deployed contract address, transaction hash (formatted as
        hexadecimal), block number, and gas used. Returns None if deployment fails.
    :rtype: Dict[str, Any]
    """
    try:
        abi = contract_info["abi"]
        bytecode = contract_info["bytecode"]
        contract_name = contract_info["contract_name"]

        # Extract constructor inputs
        constructor_inputs = []
        for item in abi:
            if item.get('type') == 'constructor':
                constructor_inputs = item.get('inputs', [])
                break

        # Get deployment arguments
        deploy_args = []
        if constructor_inputs:
            deploy_args = prompt_llm_for_args(
                {'name': 'constructor', 'inputs': constructor_inputs}
            )
            print(f"⏩⏩ Déploiement {contract_name} avec arguments auto-déduits: {deploy_args}")

        # Deploy contract
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        acct = w3.eth.accounts[0]

        if constructor_inputs:
            tx_hash = Contract.constructor(*deploy_args).transact({'from': acct})
        else:
            tx_hash = Contract.constructor().transact({'from': acct})

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        address = tx_receipt.contractAddress

        # Update contract info with deployment details
        contract_info.update({
            "address": address,
            "deployment_tx": tx_hash.hex(),
            "block_number": tx_receipt.blockNumber,
            "gas_used": tx_receipt.gasUsed
        })

        print(f"✅ {contract_name} déployé à {address}")
        return contract_info

    except Exception as e:
        print(f"❌ Deploy failed for {contract_info['contract_name']}: {e}")
        return None


def should_call_setup_fn(fn: Dict[str, Any], contract_state: Dict[str, Any]) -> bool:
    """
    Determines whether a setup function should be called based on its name and
    the state of the contract.

    The function evaluates the input `fn` dictionary and checks for specific
    conditions in the `contract_state` dictionary to decide if the function
    represented by `fn` is eligible for execution.

    :param fn: A dictionary containing details about the function to evaluate.
    :param contract_state: A dictionary representing the current state of the
                           contract.
    :return: A boolean value indicating whether the function should be called
             (True) or not (False).
    """
    name = fn['name'].lower()

    # Specific logic for certain functions
    if name == "set_percent_reduction":
        if not contract_state.get("bought_tokens", False):
            return False
        if contract_state.get("rounds", 1) != 0:
            return False

    return True


def setup_contract(contract_info: Dict[str, Any], w3: Web3):
    """
    Set up a smart contract by identifying and executing the setup/init functions defined in its ABI.

    This function connects to the smart contract, determines its current state by calling all
    public getter functions and accessing public variables, and then evaluates if specific setup
    functions should be executed based on the current state. If the setup function preconditions are
    met, arguments for the function are generated and the function is called. Transactions are
    monitored for success, and detailed logs are produced.

    :param contract_info: A dictionary containing contract details such as its ABI, address, and contract name.
    :param w3: The Web3 instance used to interact with the blockchain.
    :return: None
    """
    from .contract_analyzer import get_public_getters_and_vars_state
    from .contract_compiler import find_setup_functions

    contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])
    acct = w3.eth.accounts[0]

    # Find setup functions
    setup_fns = find_setup_functions(contract_info["abi"])

    # Get current contract state
    contract_state = get_public_getters_and_vars_state(w3, contract_info)

    for fn in setup_fns:
        if not should_call_setup_fn(fn, contract_state):
            print(f"⏩ Skip setup/init {fn['name']} (pré-condition non respectée d'après state actuel)")
            continue

        args = []
        args_generated = False
        try:
            # Generate arguments for setup function
            args = prompt_llm_for_args(
                fn,
                context_info=f"Nom du contrat: {contract_info['contract_name']}"
            )
            args_generated = True

            # Call the function
            fn_obj = contract.get_function_by_signature(
                f"{fn['name']}({','.join(i['type'] for i in fn['inputs'])})"
            )
            tx = fn_obj(*args).transact({'from': acct})
            w3.eth.wait_for_transaction_receipt(tx)

            print(f"✅ Setup/init : Appel de {fn['name']}({args}) réussi.")

        except Exception as e:
            if args_generated:
                print(f"⚠️ Setup/init {fn['name']}({args}) failed: {e}")
            else:
                print(f"⚠️ Setup/init {fn['name']} failed: {e}")


def auto_fund_contract_for_attack(w3: Web3, contract_info: Dict[str, Any], eth_amount: int = 3) -> Tuple[bool, str]:
    """
    Automatically funds a smart contract with the specified amount of Ether.

    This function attempts to fund the given smart contract in two ways. First, it
    searches for a payable function in the contract's ABI (Application Binary
    Interface) that takes no arguments and attempts to fund the contract using
    this function. If this approach fails, it falls back to sending Ether directly
    to the contract's address. After the transaction, it verifies whether the
    contract's balance increased as expected. Logs are generated throughout the
    process to confirm the outcome of each funding attempt.

    :param w3: Web3 instance to interact with the Ethereum blockchain.
    :type w3: Web3
    :param contract_info: Dictionary containing the contract's 'address' and 'abi',
        where 'address' is the Ethereum address of the contract, and 'abi' is its
        Application Binary Interface.
    :type contract_info: Dict[str, Any]
    :param eth_amount: The amount of Ether to fund the contract with. Defaults to
        3 ETH.
    :type eth_amount: int, optional
    :return: A tuple where the first element is a boolean indicating whether the
        funding was successful, and the second element is a string containing a
        log of the funding operation.
    :rtype: Tuple[bool, str]
    """
    contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])
    acct = w3.eth.accounts[1]  # Use different account for funding
    funded = False
    funding_log = ""

    # Vérifier la balance initiale
    initial_balance = w3.eth.get_balance(contract_info["address"])
    funding_log += f"📊 Balance initiale du contrat: {w3.from_wei(initial_balance, 'ether')} ETH\n"

    # Try funding via payable functions FIRST
    for f in contract_info["abi"]:
        if (
                f['type'] == 'function'
                and f.get('stateMutability', '') == 'payable'
                and len(f.get('inputs', [])) == 0
        ):
            try:
                fn = contract.get_function_by_signature(f"{f['name']}()")
                tx = fn().transact({'from': acct, 'value': w3.to_wei(eth_amount, 'ether')})
                receipt = w3.eth.wait_for_transaction_receipt(tx)

                # Vérifier que le funding a marché
                new_balance = w3.eth.get_balance(contract_info["address"])
                balance_increase = new_balance - initial_balance

                msg = f"✅ Funded with {eth_amount} ETH via {f['name']}() - Balance increase: {w3.from_wei(balance_increase, 'ether')} ETH"
                print(msg)
                funding_log += msg + "\n"

                if balance_increase > 0:
                    funded = True
                    break
                else:
                    funding_log += f"⚠️  WARNING: {f['name']}() succeeded but contract balance didn't increase!\n"

            except Exception as e:
                msg = f"⚠️ Funding via {f['name']}() failed: {e}"
                print(msg)
                funding_log += msg + "\n"

    # Try direct ETH transfer if payable functions failed
    if not funded:
        try:
            tx_hash = w3.eth.send_transaction({
                'from': acct,
                'to': contract_info["address"],
                'value': w3.to_wei(eth_amount, 'ether')
            })
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            # Vérifier le funding
            final_balance = w3.eth.get_balance(contract_info["address"])
            balance_increase = final_balance - initial_balance

            if balance_increase > 0:
                msg = f"✅ Direct transfer: {w3.from_wei(balance_increase, 'ether')} ETH sent to {contract_info['address']}"
                print(msg)
                funding_log += msg + "\n"
                funded = True
            else:
                msg = f"⚠️  Direct transfer failed: no balance increase"
                print(msg)
                funding_log += msg + "\n"

        except Exception as e:
            msg = f"❗️Direct transfer failed: {e}"
            print(msg)
            funding_log += msg + "\n"

    # Final verification
    final_balance = w3.eth.get_balance(contract_info["address"])
    funding_log += f"📊 Balance finale du contrat: {w3.from_wei(final_balance, 'ether')} ETH\n"

    return funded, funding_log
