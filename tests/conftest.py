import pytest

import os

import rlp

from ethereum import blocks

from web3.utils.encoding import (
    decode_hex,
)

from testrpc import testrpc


@pytest.fixture()
def party_a(web3):
    return web3.eth.accounts[1]


@pytest.fixture()
def party_b(web3):
    return web3.eth.accounts[2]


@pytest.fixture()
def arbiter(web3):
    return web3.eth.accounts[3]


@pytest.fixture()
def trapdoor_a(web3):
    return web3.eth.accounts[4]


@pytest.fixture()
def trapdoor_b(web3):
    return web3.eth.accounts[5]


@pytest.fixture()
def trapdoor_c(web3):
    return web3.eth.accounts[6]


@pytest.fixture()
def ether_min_deposit(denoms):
    return 5 * denoms.ether


@pytest.fixture()
def token_min_deposit(denoms):
    return 100


@pytest.fixture()
def unlock_at(web3):
    latest_block = web3.eth.getBlock('latest')
    return latest_block['timestamp'] + 60 * 60


@pytest.fixture()
def NULL_ADDRESS(web3):
    return '0x0000000000000000000000000000000000000000'


@pytest.fixture()
def multisig(chain,
             web3,
             party_a,
             party_b,
             arbiter,
             trapdoor_a,
             trapdoor_b,
             trapdoor_c,
             ether_min_deposit,
             token_min_deposit,
             unlock_at,
             mintable_token):
    contract = chain.get_contract('MultiSignature', deploy_kwargs={
        'participants': [party_a, party_b, arbiter],
        'rescuers': [trapdoor_a, trapdoor_b, trapdoor_c],
        '_ethDepositMinimum': ether_min_deposit,
        '_tokenDepositMinimum': token_min_deposit,
        '_tokenAddress': mintable_token.address,
        '_unlockAt': unlock_at,
        '_contractTerms': "Everyone promises to be on their best behavior",
    })

    chain_code = web3.eth.getCode(contract.address)
    assert len(chain_code) > 10

    return contract


@pytest.fixture()
def test_contract_factories(project, web3):
    from solc import compile_files
    from populus.utils.filesystem import recursive_find_files
    from populus.utils.contracts import (
        package_contracts,
        construct_contract_factories,
    )

    base_tests_dir = os.path.dirname(__file__)

    solidity_source_files = [
        os.path.relpath(contract_source_path)
        for contract_source_path
        in recursive_find_files(base_tests_dir, '*.sol')
    ] + [
        os.path.relpath(contract_source_path)
        for contract_source_path
        in recursive_find_files(project.contracts_dir, '*.sol')
    ]
    compiled_contracts = compile_files(solidity_source_files)
    test_contract_factories = construct_contract_factories(web3, compiled_contracts)
    return package_contracts(test_contract_factories)


@pytest.fixture()
def MintableToken(test_contract_factories):
    return test_contract_factories.MintableToken


@pytest.fixture()
def mintable_token(chain, web3, MintableToken, party_b):
    chain.contract_factories['MintableToken'] = MintableToken
    contract = chain.get_contract('MintableToken')

    chain_code = web3.eth.getCode(contract.address)
    assert len(chain_code) > 10

    contract.transact().mint(party_b, 1000000)
    assert contract.call().balanceOf(party_b) == 1000000

    return contract


@pytest.fixture()
def TransactionRecorder(test_contract_factories):
    return test_contract_factories.TransactionRecorder


@pytest.fixture()
def txn_recorder(chain, TransactionRecorder):
    chain.contract_factories['TransactionRecorder'] = TransactionRecorder
    return chain.get_contract('TransactionRecorder')


@pytest.fixture()
def denoms():
    from web3.utils.currency import units
    int_units = {
        key: int(value)
        for key, value in units.items()
    }
    return type('denoms', (object,), int_units)


@pytest.fixture()
def evm(web3):
    tester_client = testrpc.tester_client
    assert web3.eth.blockNumber == len(tester_client.evm.blocks) - 1
    return tester_client.evm


@pytest.fixture()
def set_timestamp(web3, evm):
    def _set_timestamp(timestamp):
        evm.block.finalize()
        evm.block.commit_state()
        evm.db.put(evm.block.hash, rlp.encode(evm.block))

        block = blocks.Block.init_from_parent(
            evm.block,
            decode_hex(web3.eth.coinbase),
            timestamp=timestamp,
        )

        evm.block = block
        evm.blocks.append(evm.block)
        return timestamp
    return _set_timestamp


@pytest.fixture()
def State():
    return type(
        'State',
        (object,),
        {
            'Genesis': 0,
            'WaitingForEther': 1,
            'WaitingForTokens': 2,
            'WaitingForArbiterLock': 3,
            'Locked': 4,
            'Unlocked': 5,
            'NeverLocked': 6,
        },
    )


@pytest.fixture()
def with_ether_deposit(web3,
                       multisig,
                       party_a,
                       ether_min_deposit,
                       State):
    assert multisig.call().currentState() in {State.Genesis, State.WaitingForEther}

    multisig.transact({
        'from': party_a,
        'value': ether_min_deposit,
    }).depositEther()

    assert multisig.call().currentState() in {State.WaitingForTokens, State.WaitingForArbiterLock}
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit


@pytest.fixture()
def with_token_deposit(web3,
                       multisig,
                       party_b,
                       token_min_deposit,
                       mintable_token,
                       State):
    assert multisig.call().currentState() in {State.Genesis, State.WaitingForTokens}

    mintable_token.transact({
        'from': party_b,
    }).transfer(multisig.address, token_min_deposit)

    assert multisig.call().currentState() in {State.WaitingForEther, State.WaitingForArbiterLock}
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit


@pytest.fixture()
def with_both_deposits(with_ether_deposit, with_token_deposit, multisig, State):
    assert multisig.call().currentState() == State.WaitingForArbiterLock


@pytest.fixture()
def with_both_deposits_and_locked(with_both_deposits,
                                  multisig,
                                  State,
                                  arbiter):
    assert multisig.call().currentState() == State.WaitingForArbiterLock

    multisig.transact({
        'from': arbiter,
    }).lock()

    assert multisig.call().currentState() == State.Locked


@pytest.fixture()
def after_unlock(with_both_deposits_and_locked,
                 multisig,
                 set_timestamp,
                 unlock_at,
                 State):
    assert multisig.call().currentState() == State.Locked

    set_timestamp(unlock_at)

    assert multisig.call().currentState() == State.Unlocked
