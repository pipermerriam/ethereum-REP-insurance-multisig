import pytest


def test_cannot_vote_during_lock_period(web3,
                                        multisig,
                                        party_a,
                                        party_b,
                                        arbiter,
                                        with_both_deposits_and_locked,
                                        NULL_ADDRESS,
                                        State):
    assert multisig.call().currentState() == State.Locked
    assert multisig.call().partyAVote() == NULL_ADDRESS
    assert multisig.call().partyBVote() == NULL_ADDRESS
    assert multisig.call().arbiterVote() == NULL_ADDRESS

    with pytest.raises(ValueError):
        multisig.transact({
            'from': party_a,
        }).submitPartyAVote(party_a)

    with pytest.raises(ValueError):
        multisig.transact({
            'from': party_a,
        }).submitPartyBVote(party_a)

    with pytest.raises(ValueError):
        multisig.transact({
            'from': party_a,
        }).submitArbiterVote(party_a)

    assert multisig.call().currentState() == State.Locked
    assert multisig.call().partyAVote() == NULL_ADDRESS
    assert multisig.call().partyBVote() == NULL_ADDRESS
    assert multisig.call().arbiterVote() == NULL_ADDRESS


@pytest.mark.parametrize(
    'a_vote,b_vote,c_vote,expected_recipient',
    (
        ('A', 'A', 'A', 'A'),
        ('B', 'A', 'A', 'A'),
        ('A', 'B', 'A', 'A'),
        ('A', 'A', 'B', 'A'),
        ('', 'A', 'A', 'A'),
        ('A', '', 'A', 'A'),
        ('A', 'A', '', 'A'),
        ('B', 'B', 'B', 'B'),
        ('A', 'B', 'B', 'B'),
        ('B', 'A', 'B', 'B'),
        ('B', 'B', 'A', 'B'),
        ('', 'B', 'B', 'B'),
        ('B', '', 'B', 'B'),
        ('B', 'B', '', 'B'),
    )
)
def test_voting_with_quorum(web3,
                            multisig,
                            party_a,
                            party_b,
                            arbiter,
                            after_unlock,
                            mintable_token,
                            NULL_ADDRESS,
                            State,
                            a_vote,
                            b_vote,
                            c_vote,
                            token_min_deposit,
                            expected_recipient):
    assert multisig.call().currentState() == State.Unlocked

    vote_map = {
        'A': party_a,
        'B': party_b,
    }

    if a_vote != '':
        multisig.transact({
            'from': party_a,
        }).submitPartyAVote(vote_map[a_vote])

    if b_vote != '':
        multisig.transact({
            'from': party_b,
        }).submitPartyBVote(vote_map[b_vote])

    if c_vote != '':
        multisig.transact({
            'from': arbiter,
        }).submitArbiterVote(vote_map[c_vote])

    before_bal_a = mintable_token.call().balanceOf(party_a)
    before_bal_b = mintable_token.call().balanceOf(party_b)

    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit

    multisig.transact({
        'from': web3.eth.accounts[0],
    }).withdrawTokens()

    assert mintable_token.call().balanceOf(multisig.address) == 0

    after_bal_a = mintable_token.call().balanceOf(party_a)
    after_bal_b = mintable_token.call().balanceOf(party_b)

    if expected_recipient == 'A':
        assert after_bal_a - before_bal_a == token_min_deposit
    else:
        assert after_bal_a - before_bal_a == 0

    if expected_recipient == 'B':
        assert after_bal_b - before_bal_b == token_min_deposit
    else:
        assert after_bal_b - before_bal_b == 0


@pytest.mark.parametrize(
    'a_vote,b_vote,c_vote',
    (
        ('', '', ''),
        ('A', '', ''),
        ('', 'A', ''),
        ('', '', 'A'),
        ('A', 'B', ''),
        ('A', '', 'B'),
        ('B', 'A', ''),
        ('', 'A', 'B'),
        ('B', '', 'A'),
        ('', 'B', 'A'),
        ('B', '', ''),
        ('', 'B', ''),
        ('', '', 'B'),
        ('B', 'A', ''),
        ('B', '', 'A'),
        ('A', 'B', ''),
        ('', 'B', 'A'),
        ('A', '', 'B'),
        ('', 'A', 'B'),
    )
)
def test_cannot_withdraw_if_no_quorum(web3,
                                      multisig,
                                      party_a,
                                      party_b,
                                      arbiter,
                                      after_unlock,
                                      mintable_token,
                                      NULL_ADDRESS,
                                      State,
                                      a_vote,
                                      b_vote,
                                      c_vote,
                                      token_min_deposit):
    assert multisig.call().currentState() == State.Unlocked

    vote_map = {
        'A': party_a,
        'B': party_b,
    }

    if a_vote != '':
        multisig.transact({
            'from': party_a,
        }).submitPartyAVote(vote_map[a_vote])

    if b_vote != '':
        multisig.transact({
            'from': party_b,
        }).submitPartyBVote(vote_map[b_vote])

    if c_vote != '':
        multisig.transact({
            'from': arbiter,
        }).submitArbiterVote(vote_map[c_vote])

    before_bal_a = mintable_token.call().balanceOf(party_a)
    before_bal_b = mintable_token.call().balanceOf(party_b)

    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit

    multisig.transact({
        'from': web3.eth.accounts[0],
    }).withdrawTokens()

    multisig.transact({
        'from': party_a,
    }).withdrawTokens()

    multisig.transact({
        'from': party_b,
    }).withdrawTokens()

    multisig.transact({
        'from': arbiter,
    }).withdrawTokens()

    assert mintable_token.call().balanceOf(multisig.address) == token_min_deposit

    after_bal_a = mintable_token.call().balanceOf(party_a)
    after_bal_b = mintable_token.call().balanceOf(party_b)

    assert before_bal_a == after_bal_a
    assert before_bal_b == after_bal_b


def test_cannot_vote_for_any_address(web3,
                                     multisig,
                                     party_a,
                                     party_b,
                                     arbiter,
                                     after_unlock,
                                     mintable_token,
                                     NULL_ADDRESS,
                                     State):
    assert multisig.call().currentState() == State.Unlocked
    assert multisig.call().partyAVote() == NULL_ADDRESS

    with pytest.raises(ValueError):
        multisig.transact({
            'from': party_a,
        }).submitArbiterVote(arbiter)

    assert multisig.call().partyAVote() == NULL_ADDRESS

    with pytest.raises(ValueError):
        multisig.transact({
            'from': party_a,
        }).submitArbiterVote(web3.eth.accounts[0])

    assert multisig.call().partyAVote() == NULL_ADDRESS
