def test_genesis_state(multisig,
                       party_a,
                       party_b,
                       arbiter,
                       trapdoor_a,
                       trapdoor_b,
                       trapdoor_c,
                       ether_min_deposit,
                       token_min_deposit,
                       unlock_at,
                       mintable_token,
                       NULL_ADDRESS,
                       State):
    assert multisig.call().partyA() == party_a
    assert multisig.call().partyB() == party_b
    assert multisig.call().arbiter() == arbiter

    assert multisig.call().trapdoorA() == trapdoor_a
    assert multisig.call().trapdoorB() == trapdoor_b
    assert multisig.call().trapdoorC() == trapdoor_c

    assert multisig.call().partyAVote() == NULL_ADDRESS
    assert multisig.call().partyBVote() == NULL_ADDRESS
    assert multisig.call().arbiterVote() == NULL_ADDRESS

    assert multisig.call().ethDepositMinimum() == ether_min_deposit
    assert multisig.call().tokenDepositMinimum() == token_min_deposit

    assert multisig.call().lockedAt() == 0
    assert multisig.call().unlockAt() == unlock_at

    assert multisig.call().token() == mintable_token.address
    assert multisig.call().contractTerms() == "Everyone promises to be on their best behavior"

    assert multisig.call().currentState() == State.Genesis
