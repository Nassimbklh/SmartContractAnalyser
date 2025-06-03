"""
Contract Deployment Module
Handles smart contract deployment and setup
"""

import openai
from typing import List, Dict, Any, Tuple
from web3 import Web3
from ..utils import openai_utils


def log(msg: str):
    """Simple logging function"""
    print(msg)


def prompt_llm_for_args(fn_abi: Dict[str, Any], context_info: str = "", model: str = "gpt-4") -> List:
    """
    Use LLM to generate constructor/function arguments

    Args:
        fn_abi: Function ABI information
        context_info: Additional context for the LLM
        model: LLM model to use

    Returns:
        List of generated arguments
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
    Deploy a single contract

    Args:
        contract_info: Contract compilation information
        w3: Web3 instance

    Returns:
        Updated contract info with deployment details
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
            log(f"⏩⏩ Déploiement {contract_name} avec arguments auto-déduits: {deploy_args}")

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

        log(f"✅ {contract_name} déployé à {address}")
        return contract_info

    except Exception as e:
        log(f"❌ Deploy failed for {contract_info['contract_name']}: {e}")
        return None


def should_call_setup_fn(fn: Dict[str, Any], contract_state: Dict[str, Any]) -> bool:
    """
    Determine if a setup function should be called based on contract state

    Args:
        fn: Function ABI
        contract_state: Current contract state

    Returns:
        True if function should be called
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
    Call setup/initialization functions on deployed contract

    Args:
        contract_info: Contract information with deployment details
        w3: Web3 instance
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
            log(f"⏩ Skip setup/init {fn['name']} (pré-condition non respectée d'après state actuel)")
            continue

        try:
            # Generate arguments for setup function
            args = prompt_llm_for_args(
                fn,
                context_info=f"Nom du contrat: {contract_info['contract_name']}"
            )

            # Call the function
            fn_obj = contract.get_function_by_signature(
                f"{fn['name']}({','.join(i['type'] for i in fn['inputs'])})"
            )
            tx = fn_obj(*args).transact({'from': acct})
            w3.eth.wait_for_transaction_receipt(tx)

            log(f"✅ Setup/init : Appel de {fn['name']}({args}) réussi.")

        except Exception as e:
            log(f"⚠️ Setup/init {fn['name']}({args}) failed: {e}")


def auto_fund_contract_for_attack(w3: Web3, contract_info: Dict[str, Any], eth_amount: int = 3) -> Tuple[bool, str]:
    """
    Automatically fund contract for attack testing

    Args:
        w3: Web3 instance
        contract_info: Contract information
        eth_amount: Amount of ETH to send

    Returns:
        Tuple of (success, log_message)
    """
    contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])
    acct = w3.eth.accounts[1]  # Use different account for funding
    funded = False
    funding_log = ""

    # Try funding via payable functions
    for f in contract_info["abi"]:
        if (
                f['type'] == 'function'
                and f.get('stateMutability', '') == 'payable'
                and len(f.get('inputs', [])) == 0
        ):
            try:
                fn = contract.get_function_by_signature(f"{f['name']}()")
                tx = fn().transact({'from': acct, 'value': w3.to_wei(eth_amount, 'ether')})
                w3.eth.wait_for_transaction_receipt(tx)
                msg = f"✅ Funded with {eth_amount} ETH via {f['name']}()"
                log(msg)
                funding_log += msg + "\n"
                funded = True
                break
            except Exception as e:
                msg = f"⚠️ Funding via {f['name']}() failed: {e}"
                log(msg)
                funding_log += msg + "\n"

    # Try direct ETH transfer if payable functions failed
    if not funded:
        try:
            tx_hash = w3.eth.send_transaction({
                'from': acct,
                'to': contract_info["address"],
                'value': w3.to_wei(eth_amount, 'ether')
            })
            w3.eth.wait_for_transaction_receipt(tx_hash)
            msg = f"✅ Native funding {eth_amount} ETH sent to {contract_info['address']}"
            log(msg)
            funding_log += msg + "\n"
            funded = True
        except Exception as e:
            msg = f"❗️Funding failed: can't fund contract {contract_info['contract_name']} at {contract_info['address']}. Error: {e}"
            log(msg)
            funding_log += msg + "\n"

    # Log information about non-fundable contracts
    if not funded:
        has_payable = any(
            f['type'] == 'function' and f.get('stateMutability', '') == 'payable'
            for f in contract_info["abi"]
        )
        has_fallback = any(
            f['type'] in ['fallback', 'receive'] for f in contract_info["abi"]
        )

        if not has_payable and not has_fallback:
            msg = (
                f"ℹ️  [INFO] Contract {contract_info['contract_name']} at {contract_info['address']} "
                f"does not accept native funding (no payable/fallback/receive, standard for ERC20 etc)."
            )
            log(msg)
            funding_log += msg + "\n"
        else:
            msg = (
                f"❗️Warning: No funding method found for contract {contract_info['contract_name']} "
                f"({contract_info['address']})!"
            )
            log(msg)
            funding_log += msg + "\n"

    return funded, funding_log
