import pytest


def test_cannot_lock_with_no_deposits(multisig, arbiter, State):
    assert multisig.call().currentState() == State.Genesis

    with pytest.raises(ValueError):
        multisig.transact({
            'from': arbiter,
        }).lock()

    assert multisig.call().currentState() == State.Genesis


def test_cannot_lock_without_ether_deposit(multisig,
                                           arbiter,
                                           State,
                                           with_token_deposit):
    assert multisig.call().currentState() == State.WaitingForEther

    with pytest.raises(ValueError):
        multisig.transact({
            'from': arbiter,
        }).lock()

    assert multisig.call().currentState() == State.WaitingForEther


def test_cannot_lock_without_token_deposit(multisig,
                                           arbiter,
                                           State,
                                           with_ether_deposit):
    assert multisig.call().currentState() == State.WaitingForTokens

    with pytest.raises(ValueError):
        multisig.transact({
            'from': arbiter,
        }).lock()

    assert multisig.call().currentState() == State.WaitingForTokens


def test_locking(multisig,
                 arbiter,
                 State,
                 with_both_deposits):
    assert multisig.call().currentState() == State.WaitingForArbiterLock

    multisig.transact({
        'from': arbiter,
    }).lock()

    assert multisig.call().currentState() == State.Locked


def test_only_arbiter_can_lock(web3,
                               multisig,
                               State,
                               with_both_deposits):
    assert multisig.call().currentState() == State.WaitingForArbiterLock

    with pytest.raises(ValueError):
        multisig.transact({
            'from': web3.eth.accounts[0],
        }).lock()

    assert multisig.call().currentState() == State.WaitingForArbiterLock


def test_cannot_lock_after_unlock_at(multisig,
                                     arbiter,
                                     State,
                                     unlock_at,
                                     set_timestamp,
                                     with_both_deposits):
    set_timestamp(unlock_at - 1)

    assert multisig.call().currentState() == State.WaitingForArbiterLock

    set_timestamp(unlock_at)

    assert multisig.call().currentState() == State.NeverLocked

    with pytest.raises(ValueError):
        multisig.transact({
            'from': arbiter,
        }).lock()

    assert multisig.call().currentState() == State.NeverLocked


def test_party_b_can_withdraw_in_locked_state(web3,
                                              multisig,
                                              arbiter,
                                              party_b,
                                              ether_min_deposit,
                                              State,
                                              with_both_deposits):
    assert multisig.call().currentState() == State.WaitingForArbiterLock

    multisig.transact({
        'from': arbiter,
    }).lock()

    assert multisig.call().currentState() == State.Locked

    before_balance = web3.eth.getBalance(party_b)
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit

    txn_hash = multisig.transact({
        'from': party_b,
    }).withdrawEther()
    txn = web3.eth.getTransaction(txn_hash)
    txn_receipt = web3.eth.getTransactionReceipt(txn_hash)

    after_balance = web3.eth.getBalance(party_b)
    assert web3.eth.getBalance(multisig.address) == 0

    assert after_balance - before_balance == ether_min_deposit - txn['gasPrice'] * txn_receipt['gasUsed']


def test_anyone_can_trigger_party_b_withdraw(web3,
                                             multisig,
                                             arbiter,
                                             party_b,
                                             ether_min_deposit,
                                             State,
                                             with_both_deposits):
    assert multisig.call().currentState() == State.WaitingForArbiterLock

    multisig.transact({
        'from': arbiter,
    }).lock()

    assert multisig.call().currentState() == State.Locked

    before_balance = web3.eth.getBalance(party_b)
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit

    multisig.transact({
        'from': web3.eth.accounts[0],
    }).withdrawEther()

    after_balance = web3.eth.getBalance(party_b)
    assert web3.eth.getBalance(multisig.address) == 0

    assert after_balance - before_balance == ether_min_deposit
