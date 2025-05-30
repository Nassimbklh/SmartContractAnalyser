import os
import json
import re
import time
import tempfile
from typing import List, Dict, Any, Tuple
from web3 import Web3
from web3.providers.eth_tester import EthereumTesterProvider
from solcx import (
    compile_standard, install_solc, set_solc_version,
    get_installed_solc_versions
)
import openai
import requests

# -------------------- CONFIGURATION --------------------
# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY environment variable not set")
openai.api_key = OPENAI_API_KEY
BIG_MODEL_THRESHOLD = 1000

# -------------------- SETUP --------------------
w3 = Web3(EthereumTesterProvider())


def log(msg): print(msg)




def extract_solc_version(source_code: str) -> str:
    m = re.search(r'pragma\s+solidity\s+(\^?)([\d\.]+)', source_code)
    if m: return m.group(2)
    return "0.4.26"


def clean_bytecode(bytecode):
    bytecode = re.sub(r'__[^_]+__+', '', bytecode)
    if not bytecode.startswith("0x"): bytecode = "0x" + bytecode
    return bytecode


def extract_events(abi):
    return [{"name": item['name'], "inputs": item['inputs']} for item in abi if item['type'] == 'event']


def extract_function_details(abi):
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


def get_accounts_balances(w3, addresses):
    return {addr: w3.eth.get_balance(addr) for addr in addresses}


def get_public_getters_and_vars_state(w3, contract_info):
    contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])
    state = {}
    for f in contract_info["abi"]:
        if f['type'] == 'function' and f.get('stateMutability', '') in ('view', 'pure'):
            try:
                if len(f['inputs']) == 0:
                    fn = contract.get_function_by_signature(f"{f['name']}()")
                    state[f['name']] = fn().call()
                elif len(f['inputs']) == 1:
                    arg_type = f['inputs'][0]['type']
                    results = []
                    if arg_type == 'address':
                        for acct in w3.eth.accounts[:3]:
                            fn = contract.get_function_by_signature(f"{f['name']}(address)")
                            val = fn(acct).call()
                            results.append({"address": acct, "value": val})
                    elif arg_type.startswith('uint'):
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


def is_exploitable_target(contract_info):
    important_names = ["wallet", "bank", "dao", "crowdsale", "lottery", "fund", "proxy", "casino", "exchange", "ico",
                       "sale", "pool", "staking"]
    safe_names = ["erc20", "standardtoken", "safemath", "ownable", "tokenbasic", "erc20basic", "math", "util",
                  "interface", "library", "recipient"]
    name = contract_info["contract_name"].lower()
    if any(n in name for n in safe_names):
        return False
    if any(n in name for n in important_names):
        return True
    for f in contract_info["abi"]:
        if f['type'] == 'function' and f.get('stateMutability', '') == 'payable':
            return True
    if any("balance" in v['name'].lower() or "fund" in v['name'].lower() or "jackpot" in v['name'].lower() for v in
           contract_info["abi"] if v['type'] == "function"):
        return True
    return False


def extract_constructor_inputs(abi):
    for item in abi:
        if item.get('type') == 'constructor':
            return item.get('inputs', [])
    return []


def find_setup_functions(abi):
    setup_words = ["init", "setup", "register", "mint", "whitelist", "add", "open", "start", "set"]
    return [f for f in abi if f['type'] == 'function' and any(word in f['name'].lower() for word in setup_words)]


# --- PATCH: Appel LLM pour générer les arguments + robustesse ---
def prompt_llm_for_args(fn_abi, context_info="", model="gpt-4.1-nano"):
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

    type_guide = ", ".join(
        [f"{inp['name']} ({inp['type']}) = {type_map.get(inp['type'], 'str')}" for inp in abi_inputs])
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
                    if isinstance(val, str) and Web3.is_address(val):
                        casted.append(Web3.to_checksum_address(val))
                    else:
                        casted.append(Web3.to_checksum_address(w3.eth.accounts[0]))
                except:
                    casted.append(Web3.to_checksum_address(w3.eth.accounts[0]))

            elif typ == "address[]":
                if isinstance(val, list):
                    addresses = []
                    for a in val:
                        if isinstance(a, str) and Web3.is_address(a):
                            addresses.append(Web3.to_checksum_address(a))
                        else:
                            addresses.append(Web3.to_checksum_address(w3.eth.accounts[0]))
                    casted.append(addresses)
                else:
                    casted.append([Web3.to_checksum_address(w3.eth.accounts[0])])

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
        # Fallback de secours si le prompt échoue
        return [
            w3.eth.accounts[0] if inp['type'] == "address" else
            [w3.eth.accounts[0], w3.eth.accounts[1]] if inp['type'] == "address[]" else
            "KEY" if inp['type'] == "bytes32" else
            1 if "uint" in inp['type'] else
            "test" if inp['type'] == "string" else
            False if inp['type'] == "bool" else
            0
            for inp in abi_inputs
        ]

# PATCH: Validation de l'état AVANT d'appeler la fonction setup/init
def should_call_setup_fn(fn, contract_state):
    name = fn['name'].lower()
    if name == "set_percent_reduction":
        if not contract_state.get("bought_tokens", False): return False
        if contract_state.get("rounds", 1) != 0: return False
    return True


def compile_and_deploy_all_contracts(filepath, w3=None):
    encodings = ['utf-8', 'latin-1', 'cp1252']
    source_code = None
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                source_code = f.read()
            break
        except UnicodeDecodeError:
            continue
    if source_code is None:
        raise Exception(f"Impossible de lire le fichier avec encodages {encodings}")
    solc_ver = extract_solc_version(source_code)
    installed_versions = [str(v) for v in get_installed_solc_versions()]
    if solc_ver not in installed_versions:
        log(f"⏳ Installation de solc {solc_ver} ...")
        try:
            install_solc(solc_ver)
        except Exception as e:
            log(f"⚠️ Impossible d'installer solc {solc_ver}: {e}")
            return []
    set_solc_version(solc_ver)
    file_name = os.path.basename(filepath)
    try:
        compiled = compile_standard({
            "language": "Solidity",
            "sources": {file_name: {"content": source_code}},
            "settings": {
                "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}
            }
        })
    except Exception as e:
        log(f"❌ Compilation Error: {filepath} : {e}")
        return []
    if w3 is None: w3 = Web3(EthereumTesterProvider())
    acct = w3.eth.accounts[0]
    results = []
    contracts = compiled["contracts"][file_name]
    for contract_name, contract_data in contracts.items():
        abi = contract_data["abi"]
        bytecode = clean_bytecode(contract_data["evm"]["bytecode"]["object"])
        constructor_inputs = extract_constructor_inputs(abi)
        deploy_args = []
        if constructor_inputs:
            deploy_args = prompt_llm_for_args({'name': 'constructor', 'inputs': constructor_inputs})
            log(f"⏩⏩ Déploiement {contract_name} avec arguments auto-déduits: {deploy_args}")
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        try:
            if constructor_inputs:
                tx_hash = Contract.constructor(*deploy_args).transact({'from': acct})
            else:
                tx_hash = Contract.constructor().transact({'from': acct})
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            log(f"❌ Deploy failed for {contract_name} in {file_name}: {e}")
            continue
        address = tx_receipt.contractAddress
        results.append({
            "filename": file_name,
            "contract_name": contract_name,
            "address": address,
            "abi": abi,
            "bytecode": bytecode,
            "source_code": source_code,
            "solc_version": solc_ver
        })
        log(f"✅ {contract_name} ({file_name}, solc {solc_ver}) déployé à {address}")
    return results


def setup_contract(contract_info, w3):
    contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])
    acct = w3.eth.accounts[0]
    setup_fns = find_setup_functions(contract_info["abi"])
    contract_state = get_public_getters_and_vars_state(w3, contract_info)
    for fn in setup_fns:
        if not should_call_setup_fn(fn, contract_state):
            log(f"⏩ Skip setup/init {fn['name']} (pré-condition non respectée d'après state actuel)")
            continue
        try:
            args = prompt_llm_for_args(fn, context_info=f"Nom du contrat: {contract_info['contract_name']}")
            fn_obj = contract.get_function_by_signature(
                f"{fn['name']}({','.join(i['type'] for i in fn['inputs'])})"
            )
            tx = fn_obj(*args).transact({'from': acct})
            w3.eth.wait_for_transaction_receipt(tx)
            log(f"✅ Setup/init : Appel de {fn['name']}({args}) réussi.")
        except Exception as e:
            log(f"⚠️ Setup/init {fn['name']}({args}) failed: {e}")


def auto_fund_contract_for_attack(w3, contract_info, eth_amount=3):
    contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])
    acct = w3.eth.accounts[1]
    funded = False
    funding_log = ""
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
    if not funded:
        has_payable = any(
            f['type'] == 'function' and f.get('stateMutability', '') == 'payable'
            for f in contract_info["abi"]
        )
        has_fallback = any(
            f['type'] in ['fallback', 'receive'] for f in contract_info["abi"]
        )
        is_token_like = any(
            token in contract_info["contract_name"].lower() for token in ['erc20', 'token', 'standardtoken'])
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


def build_multi_contract_observation(contract_group: List[Dict[str, Any]], w3) -> Dict[str, Any]:
    contracts_obs = []
    for ci in contract_group:
        addresses = [ci["address"]] + w3.eth.accounts[:3]
        contracts_obs.append({
            "contract_name": ci["contract_name"],
            "address": ci["address"],
            "abi": ci["abi"],
            "functions": extract_function_details(ci["abi"]),
            "events": extract_events(ci["abi"]),
            "accounts_balances": get_accounts_balances(w3, addresses),
            "public_state": get_public_getters_and_vars_state(w3, ci),
            "source_code_snippet": ci["source_code"]
        })
    observation = {
        "filename": contract_group[0]["filename"],
        "contracts": contracts_obs
    }
    return observation


def build_multi_contract_attack_prompt(observation: Dict[str, Any]) -> str:
    txt = f"""
You are a world-class smart contract security auditor and black-hat exploit developer.

**Ignore all contracts that are standard utilities (ERC20, SafeMath, Ownable, Math, Interface, Libraries, etc). Focus only on contracts that can hold ETH or user funds, or have business logic.**

Your task:
- Analyze only the real targets (wallets, banks, DAOs, exchanges, casinos, crowdsales, games, proxies, funds, staking, etc.)
- If an initial setup (mint, register, add funds, whitelist, etc.) is required, explain how you would set up the contract for the attack. If any arguments or special values are needed, describe them.

- Find and explain **any vulnerability**: reentrancy, logic bugs, permission issues, math errors, unsafe calls, backdoors, economic exploits, etc.
- Maximize the real-world impact.

Contracts context (JSON):
{json.dumps(observation, indent=2)}

Response format:
1. Reasoning (chain of thought): ...
2. Vulnerability summary: ...
3. Exploit code: ...
---
"""
    return txt


def parse_llm_response(llm_response: str) -> Tuple[str, str, str, str]:
    reasoning = ""
    summary = ""
    code = ""
    code_type = "solidity"
    try:
        reasoning_match = re.search(r'Reasoning.*?:([\s\S]+?)Vulnerability summary:', llm_response, re.IGNORECASE)
        summary_match = re.search(r'Vulnerability summary.*?:([\s\S]+?)Exploit code:', llm_response, re.IGNORECASE)
        code_match = re.search(r'```(\w+)?\n([\s\S]+?)```', llm_response, re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        if summary_match:
            summary = summary_match.group(1).strip()
        if code_match:
            code_type = code_match.group(1) or "solidity"
            code = code_match.group(2).strip()
    except Exception as e:
        reasoning, summary, code, code_type = "", "", "", "solidity"
    return reasoning, summary, code, code_type


# [NEW]
def execute_attack_on_contracts(code: str, contract_group: List[Dict[str, Any]], w3, code_type="solidity") -> Dict[
    str, Any]:
    """
    Exécute le code d'attaque sur chaque contrat du groupe, en supportant Solidity, Python, JS.
    """
    if code_type.lower().startswith("solidity"):
        # (comportement habituel)
        def compile_and_deploy_attack_contract(attack_source, w3, target_address):
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
            tx_hash = Contract.constructor(contract_group[0]["address"]).transact({'from': acct})
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            address = tx_receipt.contractAddress
            return address, abi, bytecode

        def find_attack_function_robust(abi):
            for fn in abi:
                if fn['type'] == 'function':
                    if any(x in fn['name'].lower() for x in ["attack", "exploit", "run"]):
                        return fn['name'], fn.get('inputs', [])
            for fn in abi:
                if fn['type'] == 'function' and len(fn.get('inputs', [])) == 0:
                    return fn['name'], []
            return None, []

        def build_attack_args(inputs, w3):
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

        def try_attack_super_generic(attack_address, attack_abi, w3):
            attacker = w3.eth.contract(address=attack_address, abi=attack_abi)
            acct = w3.eth.accounts[1]
            fn_name, inputs = find_attack_function_robust(attack_abi)
            if fn_name is None:
                return False, fn_name, []
            args = build_attack_args(inputs, w3)
            is_payable = False
            for fn in attack_abi:
                if fn['type'] == 'function' and fn['name'] == fn_name:
                    if fn.get('stateMutability', '') == 'payable' or fn.get('payable', False):
                        is_payable = True
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
                print(f"✅ Attack function {fn_name} called with args {args} (payable={is_payable})")
                return True, fn_name, args
            except Exception as e:
                print(f"❌ Attack failed: {e}")
                return False, fn_name, args

        def measure_exploit_success(w3, contract_info, attacker_address):
            contract_balance = w3.eth.get_balance(contract_info["address"])
            attacker_balance = w3.eth.get_balance(attacker_address)
            return attacker_balance, contract_balance

        result = {"success": False, "error": None, "attack_fn": None, "attack_args": None,
                  "attacker_balance": None, "contract_balance": None}
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

    elif code_type.lower() == "python":
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            pyfile = f.name
        try:
            out = subprocess.run(["python3", pyfile], capture_output=True, timeout=30)
            stdout = out.stdout.decode()
            stderr = out.stderr.decode()
            attacker_balance = w3.eth.get_balance(w3.eth.accounts[1])
            result = {
                "success": out.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "attacker_balance": attacker_balance
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}
        return result

    elif code_type.lower() in ["js", "javascript"]:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            jsfile = f.name
        try:
            out = subprocess.run(["node", jsfile], capture_output=True, timeout=30)
            stdout = out.stdout.decode()
            stderr = out.stderr.decode()
            result = {
                "success": out.returncode == 0,
                "stdout": stdout,
                "stderr": stderr
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}
        return result

    else:
        return {"success": False, "error": "Unsupported code type"}


# ----------- reste inchangé ------------

def query_gpt4(prompt, temperature=0.2):
    t0 = time.time()
    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=1800,
        stop=None,
    )
    out = response.choices[0].message.content
    duration = time.time() - t0
    return out, duration


def query_codestral_ollama(prompt: str, model: str = "codestral", temperature: float = 0.2) -> (str, float):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False
    }
    t0 = time.time()
    try:
        res = requests.post(url, json=data)
        res.raise_for_status()
        out = res.json().get('response', "")
    except Exception as e:
        out = f"ERROR: {e}"
    duration = time.time() - t0
    return out, duration


def query_policy_model(prompt: str, step: int, big_model_threshold: int = BIG_MODEL_THRESHOLD):
    if step < big_model_threshold:
        print("[MODE] Utilisation du gros modèle (GPT-4)")
        return query_gpt4(prompt)
    else:
        print("[MODE] Utilisation du modèle local (Codestral)")
        return query_codestral_ollama(prompt)


def analyze_contract_from_code(code: str) -> dict:
    """
    Analyse un smart contract à partir de son code source.

    Args:
        code (str): Le code source du smart contract à analyser

    Returns:
        dict: Un dictionnaire contenant les résultats de l'analyse
            - status (str): "OK" si aucune vulnérabilité n'est détectée, "KO" sinon
            - attack (str): Le type d'attaque détectée, ou None si aucune attaque n'est détectée
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.sol', delete=False, mode='w', encoding='utf-8') as temp_file:
            temp_file.write(code)
            temp_filepath = temp_file.name

        w3 = Web3(EthereumTesterProvider())
        contract_group_all = compile_and_deploy_all_contracts(temp_filepath, w3)
        os.unlink(temp_filepath)

        if not contract_group_all:
            return {"status": "OK", "attack": None}

        contract_group = [ci for ci in contract_group_all if is_exploitable_target(ci)]
        if not contract_group:
            return {"status": "OK", "attack": None}

        for ci in contract_group:
            setup_contract(ci, w3)
        for ci in contract_group:
            auto_fund_contract_for_attack(w3, ci)

        observation = build_multi_contract_observation(contract_group, w3)
        prompt = build_multi_contract_attack_prompt(observation)
        llm_response, _ = query_policy_model(prompt, 0)
        reasoning, summary, exploit_code, code_type = parse_llm_response(llm_response)

        print("==== LLM RESPONSE ====")
        print(llm_response)
        print("==== PARSED ====")
        print(f"Reasoning: {reasoning}")
        print(f"Summary: {summary}")
        print(f"Exploit code:\n{exploit_code}")
        print("======================")

        attack_result = {}
        if exploit_code:
            attack_result = execute_attack_on_contracts(exploit_code, contract_group, w3, code_type=code_type)
            print("==== ATTACK RESULT ====")
            print(json.dumps(attack_result, indent=2))

        attack_type = None
        if "reentrancy" in summary.lower():
            attack_type = "Reentrancy Attack"
        elif "overflow" in summary.lower():
            attack_type = "Integer Overflow"
        elif "underflow" in summary.lower():
            attack_type = "Integer Underflow"
        elif "delegatecall" in summary.lower():
            attack_type = "Delegatecall Injection"
        elif "timestamp" in summary.lower():
            attack_type = "Timestamp Manipulation"
        elif "frontrun" in summary.lower():
            attack_type = "Frontrunning Attack"
        elif "access control" in summary.lower():
            attack_type = "Access Control Vulnerability"

        status = "KO" if attack_result.get("success", False) or attack_type else "OK"

        return {
            "status": status,
            "attack": attack_type,
            "contract_info": contract_group[0],  # ✅ nécessaire pour le rapport
            "reasoning": reasoning,
            "summary": summary,
            "code": exploit_code,
            "code_type": code_type,
            "attack_result": attack_result
        }

    except Exception as e:
        print(f"Error in analyze_contract_from_code: {e}")
        return {"status": "OK", "attack": None}
