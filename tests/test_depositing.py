import pytest


def test_ether_deposit_first(web3, multisig, party_a, ether_min_deposit, State):
    assert multisig.call().currentState() == State.Genesis

    multisig.transact({
        'from': party_a,
        'value': ether_min_deposit,
    }).depositEther()

    assert multisig.call().currentState() == State.WaitingForTokens
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit


def test_token_deposit_first_via_approval(web3,
                                          multisig,
                                          party_b,
                                          token_min_deposit,
                                          mintable_token,
                                          State):
    assert multisig.call().currentState() == State.Genesis

    mintable_token.transact({
        'from': party_b,
    }).approve(multisig.address, token_min_deposit)

    assert mintable_token.call().balanceOf(multisig.address) == 0

    multisig.transact({
        'from': party_b,
    }).depositToken()

    assert multisig.call().currentState() == State.WaitingForEther
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit


def test_token_deposit_via_direct_transfer(web3,
                                           multisig,
                                           party_b,
                                           token_min_deposit,
                                           mintable_token,
                                           State):
    assert multisig.call().currentState() == State.Genesis

    assert mintable_token.call().balanceOf(multisig.address) == 0

    mintable_token.transact({
        'from': party_b,
    }).transfer(multisig.address, token_min_deposit)

    assert multisig.call().currentState() == State.WaitingForEther
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit


def test_insufficient_ether_deposit(web3,
                                    multisig,
                                    party_a,
                                    ether_min_deposit,
                                    State):
    assert multisig.call().currentState() == State.Genesis

    multisig.transact({
        'from': party_a,
        'value': ether_min_deposit - 1,
    }).depositEther()

    assert multisig.call().currentState() == State.Genesis
    assert web3.eth.getBalance(multisig.address) == 0


def test_insufficient_token_deposit(web3,
                                    multisig,
                                    party_b,
                                    token_min_deposit,
                                    mintable_token,
                                    State):
    assert multisig.call().currentState() == State.Genesis

    mintable_token.transact({
        'from': party_b,
    }).approve(multisig.address, token_min_deposit - 1)

    assert mintable_token.call().balanceOf(multisig.address) == 0

    multisig.transact({
        'from': party_b,
    }).depositToken()

    assert multisig.call().currentState() == State.Genesis
    assert mintable_token.call().balanceOf(multisig.address) == 0


def test_multipart_token_deposit(web3,
                                 multisig,
                                 party_b,
                                 token_min_deposit,
                                 mintable_token,
                                 State):
    mintable_token.transact({
        'from': party_b,
    }).transfer(multisig.address, token_min_deposit // 2)

    mintable_token.transact({
        'from': party_b,
    }).approve(multisig.address, token_min_deposit - token_min_deposit // 2)

    assert multisig.call().currentState() == State.Genesis
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit // 2

    multisig.transact({
        'from': party_b,
    }).depositToken()

    assert multisig.call().currentState() == State.WaitingForEther
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit


def test_both_deposits_ether_first(web3,
                                   multisig,
                                   party_b,
                                   party_a,
                                   ether_min_deposit,
                                   token_min_deposit,
                                   mintable_token,
                                   State):
    assert multisig.call().currentState() == State.Genesis

    multisig.transact({
        'from': party_a,
        'value': ether_min_deposit,
    }).depositEther()

    assert multisig.call().currentState() == State.WaitingForTokens
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit

    mintable_token.transact({
        'from': party_b,
    }).approve(multisig.address, token_min_deposit)

    multisig.transact({
        'from': party_b,
    }).depositToken()

    assert multisig.call().currentState() == State.WaitingForArbiterLock
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit


def test_both_deposits_token_first(web3,
                                   multisig,
                                   party_b,
                                   party_a,
                                   ether_min_deposit,
                                   token_min_deposit,
                                   mintable_token,
                                   State):
    assert multisig.call().currentState() == State.Genesis

    mintable_token.transact({
        'from': party_b,
    }).approve(multisig.address, token_min_deposit)

    multisig.transact({
        'from': party_b,
    }).depositToken()

    assert multisig.call().currentState() == State.WaitingForEther
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit

    multisig.transact({
        'from': party_a,
        'value': ether_min_deposit,
    }).depositEther()

    assert multisig.call().currentState() == State.WaitingForArbiterLock
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit


def test_ether_refund(web3, multisig, party_a, ether_min_deposit, State):
    assert multisig.call().currentState() == State.Genesis

    multisig.transact({
        'from': party_a,
        'value': ether_min_deposit,
    }).depositEther()

    assert multisig.call().currentState() == State.WaitingForTokens
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit

    multisig.transact({
        'from': party_a,
    }).refundEther()

    assert web3.eth.getBalance(multisig.address) == 0
    assert multisig.call().currentState() == State.Genesis


def test_only_party_a_can_ether_refund(web3, multisig, party_a, ether_min_deposit, State):
    assert multisig.call().currentState() == State.Genesis

    multisig.transact({
        'from': party_a,
        'value': ether_min_deposit,
    }).depositEther()

    assert multisig.call().currentState() == State.WaitingForTokens
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit

    with pytest.raises(ValueError):
        multisig.transact({
            'from': web3.eth.accounts[0],
        }).refundEther()

    assert web3.eth.getBalance(multisig.address) == ether_min_deposit
    assert multisig.call().currentState() == State.WaitingForTokens


def test_token_refund(web3,
                      multisig,
                      party_b,
                      token_min_deposit,
                      mintable_token,
                      State):
    assert multisig.call().currentState() == State.Genesis
    assert mintable_token.call().balanceOf(multisig.address) == 0

    mintable_token.transact({
        'from': party_b,
    }).transfer(multisig.address, token_min_deposit)

    assert multisig.call().currentState() == State.WaitingForEther
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit

    multisig.transact({
        'from': party_b,
    }).refundTokens()

    assert multisig.call().currentState() == State.Genesis
    assert mintable_token.call().balanceOf(multisig.address) == 0


def test_only_party_b_can_token_refund(web3,
                                       multisig,
                                       party_b,
                                       token_min_deposit,
                                       mintable_token,
                                       State):
    assert multisig.call().currentState() == State.Genesis
    assert mintable_token.call().balanceOf(multisig.address) == 0

    mintable_token.transact({
        'from': party_b,
    }).transfer(multisig.address, token_min_deposit)

    assert multisig.call().currentState() == State.WaitingForEther
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit

    with pytest.raises(ValueError):
        multisig.transact({
            'from': web3.eth.accounts[0],
        }).refundTokens()

    assert multisig.call().currentState() == State.WaitingForEther
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit


def test_both_refund_token_first(web3,
                                 multisig,
                                 party_b,
                                 party_a,
                                 token_min_deposit,
                                 ether_min_deposit,
                                 mintable_token,
                                 State):
    assert multisig.call().currentState() == State.Genesis
    assert mintable_token.call().balanceOf(multisig.address) == 0

    mintable_token.transact({
        'from': party_b,
    }).transfer(multisig.address, token_min_deposit)

    multisig.transact({
        'from': party_a,
        'value': ether_min_deposit,
    }).depositEther()

    assert multisig.call().currentState() == State.WaitingForArbiterLock
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit

    multisig.transact({
        'from': party_b,
    }).refundTokens()

    assert multisig.call().currentState() == State.WaitingForTokens
    assert mintable_token.call().balanceOf(multisig.address) == 0

    multisig.transact({
        'from': party_a,
    }).refundEther()

    assert web3.eth.getBalance(multisig.address) == 0
    assert multisig.call().currentState() == State.Genesis


def test_both_refund_ether_first(web3,
                                 multisig,
                                 party_b,
                                 party_a,
                                 token_min_deposit,
                                 ether_min_deposit,
                                 mintable_token,
                                 State):
    assert multisig.call().currentState() == State.Genesis
    assert mintable_token.call().balanceOf(multisig.address) == 0

    mintable_token.transact({
        'from': party_b,
    }).transfer(multisig.address, token_min_deposit)

    multisig.transact({
        'from': party_a,
        'value': ether_min_deposit,
    }).depositEther()

    assert multisig.call().currentState() == State.WaitingForArbiterLock
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit

    multisig.transact({
        'from': party_a,
    }).refundEther()

    assert web3.eth.getBalance(multisig.address) == 0
    assert multisig.call().currentState() == State.WaitingForEther

    multisig.transact({
        'from': party_b,
    }).refundTokens()

    assert multisig.call().currentState() == State.Genesis
    assert mintable_token.call().balanceOf(multisig.address) == 0


def test_both_refund_if_never_locked(web3,
                                     multisig,
                                     party_b,
                                     party_a,
                                     token_min_deposit,
                                     ether_min_deposit,
                                     mintable_token,
                                     set_timestamp,
                                     unlock_at,
                                     State):
    assert multisig.call().currentState() == State.Genesis
    assert mintable_token.call().balanceOf(multisig.address) == 0

    mintable_token.transact({
        'from': party_b,
    }).transfer(multisig.address, token_min_deposit)

    multisig.transact({
        'from': party_a,
        'value': ether_min_deposit,
    }).depositEther()

    assert multisig.call().currentState() == State.WaitingForArbiterLock
    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit
    assert web3.eth.getBalance(multisig.address) == ether_min_deposit

    set_timestamp(unlock_at)

    assert multisig.call().currentState() == State.NeverLocked

    multisig.transact({
        'from': party_b,
    }).refundTokens()

    assert multisig.call().currentState() == State.NeverLocked
    assert mintable_token.call().balanceOf(multisig.address) == 0

    multisig.transact({
        'from': party_a,
    }).refundEther()

    assert web3.eth.getBalance(multisig.address) == 0
    assert multisig.call().currentState() == State.NeverLocked
