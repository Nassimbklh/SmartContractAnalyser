"""
Single Pipeline Test Script
Runs the RLAIF pipeline once with detailed logging of every step
"""

import os
import json
import time
from web3 import Web3
from web3.providers.eth_tester import EthereumTesterProvider

# Import refactored modules
from modules import (
    compile_contracts,
    is_exploitable_target,
    deploy_contract,
    setup_contract,
    auto_fund_contract_for_attack,
    slither_analyze,
    build_multi_contract_observation,
    generate_complete_attack_strategy,
    execute_attack_on_contracts,
    evaluate_attack,
    save_episode_results,
    debug_contract_balances
)
from dotenv import load_dotenv

# -------------------- CONFIGURATION --------------------
# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer la clé API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Test configuration
DATA_FOLDER = "./data/val"
TEST_FILE = "ReentrancyVulnerable.sol"  # Specific file for testing


def print_separator(title: str, char: str = "=", width: int = 80):
    """
    Prints a section separator with a title centered within repeated characters.

    This function helps in visual organization, primarily in console outputs,
    by displaying a separator consisting of a repeated character line, followed
    by a centered title, and another repeated character line below.

    :param title: The title text to be displayed. It will be centered between
                  the separator lines.
    :type title: str
    :param char: The character used to form the separator lines. Defaults to "=".
    :type char: str
    :param width: The total width of the separator line. Defaults to 80.
    :type width: int
    :return: None
    """
    print(f"\n{char * width}")
    print(f"{title.center(width)}")
    print(f"{char * width}")


def print_subsection(title: str, char: str = "-", width: int = 60):
    """
    Prints a subsection header with a title and formatting specified by the given
    character and width.

    This function generates a formatted header for a subsection, which consists of
    a horizontal line (using a specified character repeated for the specified width),
    followed by the title, and another line to close the header. This formatting is
    useful for creating organized textual sections in console applications.

    :param title: The title of the subsection to print.
    :type title: str
    :param char: The character used to create the horizontal line. Default is '-'.
    :type char: str
    :param width: The width (number of characters) of the horizontal line. Default
        is 60.
    :type width: int
    :return: None
    """
    print(f"\n{char * width}")
    print(f" {title}")
    print(f"{char * width}")


def print_json_pretty(data: dict, title: str = None):
    """
    Prints a dictionary in a readable JSON format. Optionally, a title can be provided
    which will be displayed above the JSON data.

    :param data: Dictionary data to be printed in a pretty JSON format.
    :type data: dict
    :param title: Optional title to display above the JSON data.
    :type title: str, optional
    :return: None
    """
    if title:
        print(f"\n📄 {title}:")
    print(json.dumps(data, indent=2, default=str))


def print_balances(w3: Web3, addresses: list, title: str = "Account Balances"):
    """
    Prints the balances of a list of Ethereum addresses in both Wei and Ether.

    A given list of Ethereum addresses is processed to retrieve their balances
    using the provided Web3 connection. The balances are printed to the console
    both in Ether and Wei units. A title can be specified to label the output,
    defaulting to "Account Balances" if not provided.

    :param w3: An instance of the Web3 class used to interact with the Ethereum
        network.
    :param addresses: A list of Ethereum addresses (strings) whose balances will
        be retrieved and displayed.
    :param title: An optional title for the output section. Defaults to "Account
        Balances".
    :return: None
    """
    print(f"\n💰 {title}:")
    for i, addr in enumerate(addresses):
        balance_wei = w3.eth.get_balance(addr)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        print(f"  Account[{i}] ({addr}): {balance_eth} ETH ({balance_wei} wei)")


# FONCTION UTILITAIRE POUR VÉRIFIER LA CONFIGURATION
def verify_web3_setup(w3: Web3) -> bool:
    """
    Verifies the Web3 setup by ensuring there are at least three accounts and that the
    first three accounts have a non-zero ETH balance. This function is primarily used
    to validate that the Web3 provider is correctly configured and the accounts are
    properly funded for subsequent operations.

    :param w3: A Web3 instance connected to a blockchain provider.
    :return: A boolean indicating whether the Web3 setup is correctly configured.
    """
    try:
        # Vérifier qu'on a au moins 3 comptes
        accounts = w3.eth.accounts
        if len(accounts) < 3:
            print(f"❌ Pas assez de comptes: {len(accounts)} (minimum 3 requis)")
            return False

        # Vérifier que les 3 premiers comptes ont de l'ETH
        for i in range(3):
            balance = w3.eth.get_balance(accounts[i])
            balance_eth = w3.from_wei(balance, 'ether')

            if balance == 0:
                print(f"❌ Account[{i}] n'a pas d'ETH: {balance_eth}")
                return False
            else:
                print(f"✅ Account[{i}]: {balance_eth} ETH")

        print("✅ Configuration Web3 correcte: 3 comptes avec ETH")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la vérification Web3: {e}")
        return False


# CONFIGURATION RECOMMANDÉE AU DÉBUT DU SCRIPT
def setup_web3_with_verification():
    """
    Sets up a Web3 instance with EthereumTesterProvider and verifies its configuration.

    This function initializes a Web3 instance using the EthereumTesterProvider,
    ensuring that the Web3 setup is correctly configured. If the verification
    fails, it raises an exception to indicate an invalid setup.

    :raises Exception: If the Web3 setup verification fails.
    :return: A configured and verified Web3 instance.
    :rtype: Web3
    """
    print("🔗 Configuration Web3...")

    # Initialiser Web3 avec EthereumTesterProvider
    w3 = Web3(EthereumTesterProvider())

    # Vérifier la configuration
    if not verify_web3_setup(w3):
        raise Exception("Configuration Web3 invalide")

    return w3


def test_single_pipeline():
    """
    Executes a testing pipeline for a single smart contract, covering compilation,
    deployment, setup, funding, and observation phases. This function is intended for
    evaluating the RLAIF Blockchain Security pipeline on Ethereum test networks.

    This function performs the following steps:
    1. Verifies that the specified test file exists in the appropriate location.
    2. Initializes the Web3 connection and retrieves Ethereum network details.
    3. Compiles the smart contracts, gathers their details, and verifies successful compilation.
    4. Deploys the compiled contracts to the Ethereum test network.
    5. Filters exploitable contract targets from the deployed contracts.
    6. Sets up the relevant contracts for further testing or exploitation.
    7. Funds the contracts for use in attack simulation, with debug logs before and after funding.
    8. Builds an observation of the affected contracts for post-deployment analysis.

    All major steps and phases include logging and execution time measurements for deeper insights.

    :raises AssertionError: Raised when initial account balances have insufficient ETH during verification.
    :raises FileNotFoundError: Raised if the test file specified cannot be found in the expected directory.

    :return: None
    """
    
    print_separator("🚀 RLAIF BLOCKCHAIN SECURITY PIPELINE - SINGLE TEST", "=", 100)
    
    # Check test file exists
    filepath = os.path.join(DATA_FOLDER, TEST_FILE)
    if not os.path.exists(filepath):
        print(f"❌ Test file not found: {filepath}")
        return
    
    print(f"📂 Test file: {filepath}")
    
    # Initialize Web3
    print_subsection("🔗 Initializing Web3 Connection")
    w3 = setup_web3_with_verification()
    print(f"✅ Connected to Ethereum test network")
    print(f"🆔 Network ID: {w3.net.version}")
    print(f"📊 Latest block: {w3.eth.block_number}")
    
    # Show initial account balances
    accounts = w3.eth.accounts[:3]
    print_balances(w3, accounts, "Initial Account Balances")

    # Vérifier que les comptes ont bien de l'ETH par défaut
    print("\n💰 Vérification des balances initiales:")
    for i, addr in enumerate(accounts):
        balance_wei = w3.eth.get_balance(addr)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        print(f"  Account[{i}] ({addr}): {balance_eth} ETH")

        # Assertion pour s'assurer qu'il y a de l'ETH
        assert balance_wei > 0, f"Account {i} should have ETH by default"

    try:
        # Step 1: Compilation
        print_separator("📋 STEP 1: CONTRACT COMPILATION")
        print(f"🔧 Compiling contracts from: {TEST_FILE}")
        
        start_time = time.time()
        contract_group_all = compile_contracts(filepath)
        compile_time = time.time() - start_time
        
        print(f"⏱️  Compilation took: {compile_time:.2f} seconds")
        print(f"📊 Total contracts found: {len(contract_group_all)}")
        
        if not contract_group_all:
            print("❌ No contracts were compiled successfully")
            return
        
        # Show compiled contracts details
        for i, contract in enumerate(contract_group_all):
            print_subsection(f"Contract {i+1}: {contract['contract_name']}")
            print(f"  📄 Filename: {contract['filename']}")
            print(f"  🏷️  Name: {contract['contract_name']}")
            print(f"  🔨 Solc Version: {contract['solc_version']}")
            print(f"  📏 Bytecode Length: {len(contract['bytecode'])} chars")
            print(f"  🔧 Functions: {len([f for f in contract['abi'] if f['type'] == 'function'])}")
            print(f"  📡 Events: {len([f for f in contract['abi'] if f['type'] == 'event'])}")
            
            # Show source code preview
            source_preview = contract['source_code'][:200] + "..." if len(contract['source_code']) > 200 else contract['source_code']
            print(f"  📝 Source Preview:\n{source_preview}")
        
        # Step 2: Deployment
        print_separator("🚀 STEP 2: CONTRACT DEPLOYMENT")
        
        deployed_contracts = []
        for i, contract_info in enumerate(contract_group_all):
            print_subsection(f"Deploying Contract {i+1}: {contract_info['contract_name']}")
            
            start_time = time.time()
            deployed = deploy_contract(contract_info, w3)
            deploy_time = time.time() - start_time
            
            if deployed:
                deployed_contracts.append(deployed)
                print(f"✅ Deployment successful in {deploy_time:.2f} seconds")
                print(f"📍 Contract Address: {deployed['address']}")
                print(f"🧾 Transaction Hash: {deployed['deployment_tx']}")
                print(f"⛽ Gas Used: {deployed['gas_used']:,}")
                print(f"🏗️  Block Number: {deployed['block_number']}")
            else:
                print(f"❌ Deployment failed after {deploy_time:.2f} seconds")
        
        print(f"\n📊 Successfully deployed: {len(deployed_contracts)}/{len(contract_group_all)} contracts")



        # Step 3: Filter exploitable targets
        print_separator("🎯 STEP 3: FILTERING EXPLOITABLE TARGETS")
        
        contract_group = [ci for ci in deployed_contracts if is_exploitable_target(ci)]
        
        print(f"🔍 Analyzing {len(deployed_contracts)} deployed contracts...")
        for contract in deployed_contracts:
            is_target = is_exploitable_target(contract)
            status = "🎯 TARGET" if is_target else "⚪ UTILITY"
            print(f"  {status} - {contract['contract_name']}")
        
        print(f"\n📊 Exploitable targets found: {len(contract_group)}/{len(deployed_contracts)}")
        
        if not contract_group:
            print("❌ No exploitable targets found. Stopping test.")
            return
        
        # Step 4: Contract Setup
        print_separator("⚙️ STEP 4: CONTRACT SETUP")
        
        for i, ci in enumerate(contract_group):
            print_subsection(f"Setting up Contract {i+1}: {ci['contract_name']}")
            
            print(f"📍 Address: {ci['address']}")
            
            # Show setup functions found
            from modules.contract_compiler import find_setup_functions
            setup_fns = find_setup_functions(ci["abi"])
            
            if setup_fns:
                print(f"🔧 Found {len(setup_fns)} setup function(s):")
                for fn in setup_fns:
                    print(f"  - {fn['name']}({', '.join(inp['type'] for inp in fn['inputs'])})")
            else:
                print("🔧 No setup functions found")
            
            start_time = time.time()
            setup_contract(ci, w3)
            setup_time = time.time() - start_time
            print(f"✅ Setup completed in {setup_time:.2f} seconds")

        # Step 5: Funding avec debugging amélioré
        print_separator("💰 STEP 5: CONTRACT FUNDING")

        funding_results = []
        for i, ci in enumerate(contract_group):
            print_subsection(f"Funding Contract {i + 1}: {ci['contract_name']}")

            # NOUVEAU: Debug avant funding
            debug_contract_balances(w3, ci)

            start_time = time.time()
            funded, funding_log = auto_fund_contract_for_attack(w3, ci, eth_amount=3)
            funding_time = time.time() - start_time

            funding_result = {
                "contract_name": ci["contract_name"],
                "address": ci["address"],
                "funded": funded,
                "funding_log": funding_log
            }
            funding_results.append(funding_result)

            print(f"💰 Funding attempt completed in {funding_time:.2f} seconds")
            print(f"✅ Success: {funded}")
            print(f"📝 Log:\n{funding_log}")

            # NOUVEAU: Debug après funding
            debug_contract_balances(w3, ci)
        
        # Show balances after funding
        all_addresses = [ci["address"] for ci in contract_group] + accounts[:3]
        print_balances(w3, all_addresses, "Balances After Funding")

        # Step 6: Build Observation
        print_separator("👁️ STEP 6: BUILDING CONTRACT OBSERVATION")

        start_time = time.time()
        observation = build_multi_contract_observation(contract_group, w3)
        observation_time = time.time() - start_time

        print(f"🔍 Observation built in {observation_time:.2f} seconds")
        print(f"📊 Contracts analyzed: {len(observation['contracts'])}")

        # Show observation details
        for i, contract_obs in enumerate(observation['contracts']):
            print_subsection(f"Contract {i + 1} Observation: {contract_obs['contract_name']}")
            print(f"  📍 Address: {contract_obs['address']}")
            print(f"  🔧 Functions: {len(contract_obs['functions'])}")
            print(f"  📡 Events: {len(contract_obs['events'])}")
            print(f"  📊 Public State Variables: {len(contract_obs['public_state'])}")

            # Show function details
            if contract_obs['functions']:
                print("  🔧 Function Details:")
                for fn in contract_obs['functions']:
                    payable = "💰" if fn['payable'] else "  "
                    print(f"    {payable} {fn['signature']} [{fn['stateMutability']}]")

            # Afficher les balances ETH vs mapping
            public_state = contract_obs['public_state']
            if '_contract_eth_balance_eth' in public_state:
                eth_balance = public_state['_contract_eth_balance_eth']
                print(f"  💰 Real ETH Balance: {eth_balance} ETH")

                # Chercher les fonctions getBalance
                for key, value in public_state.items():
                    if 'balance' in key.lower() and key != '_contract_eth_balance_eth':
                        print(f"  📊 {key}: {value}")

        print_separator("STEP 6.5 : STATIC ANALYZE")

        slith = slither_analyze(filepath)

        # Step 7: Generate Attack Strategy (Two-Step Process)
        print_separator("🧠 STEP 7: GENERATING ATTACK STRATEGY (2 LLM CALLS)")
        
        print("🤖 Using two-step process: Analysis + Attack Code Generation")
        start_time = time.time()
        attack_strategy = generate_complete_attack_strategy(slith, observation, step=0)
        strategy_time = time.time() - start_time
        
        print(f"⏱️  Total strategy generation took: {strategy_time:.2f} seconds")
        print(f"🎯 Code type: {attack_strategy['code_type']}")
        
        # Show analysis step
        print_subsection("🔍 STEP 7A: CONTRACT ANALYSIS")
        print(f"⏱️  Analysis took: {attack_strategy['analysis']['analysis_duration']:.2f} seconds")
        
        print("\n📋 Analysis Prompt Sent to LLM:")
        print(attack_strategy['analysis']['analysis_prompt'])
        
        print("\n🤖 Analysis Raw Response:")
        print(attack_strategy['analysis']['analysis_raw_response'])
        
        print("\n📊 Parsed Analysis Results:")
        print("🔍 Contract Analysis:")
        print(attack_strategy['analysis']['contract_analysis'][:500] + "..." if len(attack_strategy['analysis']['contract_analysis']) > 500 else attack_strategy['analysis']['contract_analysis'])
        
        print("\n⚠️ Vulnerability Assessment:")
        print(attack_strategy['analysis']['vulnerability_assessment'][:500] + "..." if len(attack_strategy['analysis']['vulnerability_assessment']) > 500 else attack_strategy['analysis']['vulnerability_assessment'])
        
        print("\n🎯 Exploitation Requirements:")
        print(attack_strategy['analysis']['exploitation_requirements'][:500] + "..." if len(attack_strategy['analysis']['exploitation_requirements']) > 500 else attack_strategy['analysis']['exploitation_requirements'])

        # Show attack code generation step
        print_subsection("⚔️ STEP 7B: ATTACK CODE GENERATION")
        print(f"⏱️  Attack code generation took: {attack_strategy['attack']['attack_duration']:.2f} seconds")
        
        print("\n📋 Attack Code Prompt Sent to LLM:")
        print(attack_strategy['attack']['attack_prompt'][:1000] + "..." if len(attack_strategy['attack']['attack_prompt']) > 1000 else attack_strategy['attack']['attack_prompt'])
        
        print(f"\n💻 Generated Attack Code ({attack_strategy['code_type']}):")
        print("```" + attack_strategy['code_type'])
        print(attack_strategy['code'])
        print("```")

        # Step 8: Execute Attack avec debugging amélioré
        print_separator("⚔️ STEP 8: EXECUTING ATTACK")

        if attack_strategy["code"]:
            print("🚀 Executing generated attack code...")

            # NOUVEAU: Afficher les balances AVANT l'attaque
            print_subsection("Pre-Attack Balances")
            for ci in contract_group:
                target_balance = w3.eth.get_balance(ci["address"])
                print(f"🎯 Target {ci['contract_name']}: {w3.from_wei(target_balance, 'ether')} ETH")

            for i, acct in enumerate(w3.eth.accounts[:3]):
                acct_balance = w3.eth.get_balance(acct)
                print(f"👤 Account[{i}]: {w3.from_wei(acct_balance, 'ether')} ETH")

            start_time = time.time()
            attack_result = execute_attack_on_contracts(
                attack_strategy["code"],
                contract_group,
                w3,
                code_type=attack_strategy["code_type"]
            )
            attack_time = time.time() - start_time

            print(f"⏱️  Attack execution took: {attack_time:.2f} seconds")

            # NOUVEAU: Afficher les balances APRÈS l'attaque
            print_subsection("Post-Attack Balances")
            for ci in contract_group:
                target_balance = w3.eth.get_balance(ci["address"])
                print(f"🎯 Target {ci['contract_name']}: {w3.from_wei(target_balance, 'ether')} ETH")

            for i, acct in enumerate(w3.eth.accounts[:3]):
                acct_balance = w3.eth.get_balance(acct)
                print(f"👤 Account[{i}]: {w3.from_wei(acct_balance, 'ether')} ETH")

            # Show attack results
            print_subsection("Attack Execution Results")
            print_json_pretty(attack_result, "Attack Result")

            # Show success/failure details avec plus de détails
            if attack_result.get("success"):
                print("\n✅ ATTACK SUCCESSFUL!")
                print(f"🎯 Target: {attack_result.get('target_contract', 'Unknown')}")
                print(f"🔧 Function called: {attack_result.get('attack_fn', 'Unknown')}")
                print(f"📝 Arguments: {attack_result.get('attack_args', [])}")
                if attack_result.get('attacker_balance'):
                    attacker_eth = w3.from_wei(attack_result['attacker_balance'], 'ether')
                    print(f"💰 Attacker balance: {attacker_eth} ETH")
                if attack_result.get('contract_balance'):
                    contract_eth = w3.from_wei(attack_result['contract_balance'], 'ether')
                    print(f"🏦 Contract balance: {contract_eth} ETH")
            else:
                print("\n❌ ATTACK FAILED!")
                if attack_result.get("error"):
                    print(f"🚨 Error: {attack_result['error']}")

                # NOUVEAU: Debugging supplémentaire en cas d'échec
                print("\n🔍 Debugging failed attack:")
                for ci in contract_group:
                    debug_contract_balances(w3, ci)
        else:
            attack_result = {"success": False, "error": "No code generated by LLM"}
            print("❌ No attack code was generated by the LLM")
        
        # Show final balances
        print_balances(w3, all_addresses, "Final Balances After Attack")
        
        # Step 9: Evaluate Attack
        print_separator("📊 STEP 9: EVALUATING ATTACK")
        
        print("🤖 Querying reward model for evaluation...")
        start_time = time.time()
        evaluation = evaluate_attack(observation, attack_strategy["raw_response"], attack_result)
        eval_time = time.time() - start_time
        
        print(f"⏱️  Evaluation took: {eval_time:.2f} seconds")
        
        # Show evaluation results
        print_subsection("Reward Model Evaluation")
        print("📋 Evaluation Prompt:")
        print(evaluation['reward_prompt'][:500] + "..." if len(evaluation['reward_prompt']) > 500 else evaluation['reward_prompt'])
        
        print("\n🤖 Reward Model Response:")
        print(evaluation['reward_raw_output'])
        
        print(f"\n📊 FINAL SCORE: {evaluation['reward_score']}/10")
        print(f"💬 Comment: {evaluation['reward_comment']}")
        
        # Step 10: Save Results
        print_separator("💾 STEP 10: SAVING RESULTS")
        
        print("💾 Saving episode results...")
        start_time = time.time()
        record = save_episode_results(
            observation, 
            funding_results, 
            attack_strategy, 
            attack_result, 
            evaluation,
            buffer_file="test_rlaif_buffer.jsonl",
            sft_trigger_batch=100
        )
        save_time = time.time() - start_time
        
        print(f"⏱️  Saving took: {save_time:.2f} seconds")
        print(f"📄 Results saved to: test_rlaif_buffer.jsonl")
        
        # Final Summary
        print_separator("📈 FINAL SUMMARY", "=", 100)
        
        total_time = (compile_time + sum([deploy_time, setup_time, funding_time, 
                                        observation_time, strategy_time, attack_time, eval_time, save_time]))
        
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"📊 Contracts compiled: {len(contract_group_all)}")
        print(f"🚀 Contracts deployed: {len(deployed_contracts)}")
        print(f"🎯 Exploitable targets: {len(contract_group)}")
        print(f"⚔️  Attack success: {'✅ YES' if attack_result.get('success') else '❌ NO'}")
        print(f"📊 Reward score: {evaluation['reward_score']}/10")
        print(f"🎖️  Quality: {'🏆 EXCELLENT' if evaluation['reward_score'] >= 8 else '🥈 GOOD' if evaluation['reward_score'] >= 6 else '🥉 NEEDS IMPROVEMENT'}")
        
        if evaluation['reward_score'] >= 8 and attack_result.get('success'):
            print("\n🎉 HIGH-QUALITY SUCCESSFUL ATTACK DETECTED!")
            print("📚 This sample would be added to the fine-tuning dataset")

    except Exception as e:
        print_separator("💥 ERROR OCCURRED", "!", 80)
        print(f"🚨 Error: {str(e)}")
        import traceback
        print(f"📜 Traceback:\n{traceback.format_exc()}")


if __name__ == "__main__":
    test_single_pipeline()