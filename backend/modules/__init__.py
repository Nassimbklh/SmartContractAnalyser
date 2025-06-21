"""
RLAIF Blockchain Security Research Modules
Refactored components for smart contract vulnerability discovery
"""

from .contract_compiler import (
    compile_contracts,
    is_exploitable_target,
    extract_constructor_inputs,
    find_setup_functions
)

from .contract_deployer import (
    compile_and_deploy_all_contracts,
    deploy_contract,
    setup_contract,
    auto_fund_contract_for_attack
)

from .slither_scan import (
    slither_analyze
)

from .contract_analyzer import (
    build_multi_contract_observation,
    get_public_getters_and_vars_state,
    extract_function_details,
    extract_events,
    get_accounts_balances,
    debug_contract_balances
)

from .attack_generator import (
    generate_complete_attack_strategy,
    analyze_contracts,
    generate_attack_code,
    build_contract_analysis_prompt,
    build_attack_code_prompt,
    parse_analysis_response,
    parse_attack_code_response,
    query_policy_model
)

from .attack_executor import (
    execute_attack_on_contracts
)

from .attack_evaluator import (
    evaluate_attack
)

from .results_manager import (
    save_episode_results,
    create_episode_record,
    save_record_to_buffer,
    build_instruction_sample,
    process_good_sample
)

__all__ = [
    # Compilation
    'compile_contracts',
    'is_exploitable_target',
    'extract_constructor_inputs',
    'find_setup_functions',

    # Deployment
    'compile_and_deploy_all_contracts',
    'deploy_contract',
    'setup_contract',
    'auto_fund_contract_for_attack',

    # Slither Analysis
    'slither_analyze',

    # Contract Analysis
    'build_multi_contract_observation',
    'get_public_getters_and_vars_state',
    'extract_function_details',
    'extract_events',
    'get_accounts_balances',
    'debug_contract_balances',

    # Attack Generation
    'generate_complete_attack_strategy',
    'analyze_contracts',
    'generate_attack_code',
    'build_contract_analysis_prompt',
    'build_attack_code_prompt',
    'parse_analysis_response',
    'parse_attack_code_response',
    'query_policy_model',

    # Attack Execution
    'execute_attack_on_contracts',

    # Evaluation
    'evaluate_attack',

    # Results Management
    'save_episode_results',
    'create_episode_record',
    'save_record_to_buffer',
    'build_instruction_sample',
    'process_good_sample'
]
