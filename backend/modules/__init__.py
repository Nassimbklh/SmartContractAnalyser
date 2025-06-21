"""
RLAIF Blockchain Security Research Modules
Refactored components for smart contract vulnerability discovery
"""

from .contract_compiler import (
    compile_and_deploy_all_contracts,
    is_exploitable_target,
    extract_constructor_inputs,
    find_setup_functions
)

from .contract_deployer import (
    deploy_contract,
    setup_contract,
    auto_fund_contract_for_attack
)

from .contract_analyzer import (
    build_multi_contract_observation,
    get_public_getters_and_vars_state,
    extract_function_details,
    extract_events,
    get_accounts_balances
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



__all__ = [
    # Compilation
    'compile_and_deploy_all_contracts',
    'is_exploitable_target',
    'extract_constructor_inputs',
    'find_setup_functions',

    # Deployment
    'deploy_contract',
    'setup_contract',
    'auto_fund_contract_for_attack',

    # Analysis
    'build_multi_contract_observation',
    'get_public_getters_and_vars_state',
    'extract_function_details',
    'extract_events',
    'get_accounts_balances',

    # Attack Generation
    'generate_complete_attack_strategy',
    'analyze_contracts',
    'generate_attack_code',
    'build_contract_analysis_prompt',
    'build_attack_code_prompt',
    'parse_analysis_response',
    'parse_attack_code_response',
    'query_policy_model'
]
