import pytest


@pytest.mark.parametrize(
    'first,second',
    (
        ('A', 'B'),
        ('A', 'C'),
        ('B', 'A'),
        ('B', 'C'),
        ('C', 'A'),
        ('C', 'B'),
    )
)
def test_simple_trapdoor(multisig,
                         trapdoor_a,
                         trapdoor_b,
                         trapdoor_c,
                         State,
                         txn_recorder,
                         NULL_ADDRESS,
                         with_both_deposits_and_locked,
                         first,
                         second):
    assert multisig.call().currentState() == State.Locked

    if first == 'A':
        first_from = trapdoor_a
    elif first == 'B':
        first_from = trapdoor_b
    elif first == 'C':
        first_from = trapdoor_c
    else:
        raise ValueError('invairiant')

    if second == 'A':
        second_from = trapdoor_a
    elif second == 'B':
        second_from = trapdoor_b
    elif second == 'C':
        second_from = trapdoor_c
    else:
        raise ValueError('invairiant')

    assert txn_recorder.call().lastCaller() == NULL_ADDRESS
    assert txn_recorder.call().lastCallValue() == 0
    assert txn_recorder.call().lastCallData() == ''
    assert txn_recorder.call().wasCalled() is False

    multisig.transact({
        'from': first_from,
    }).trapdoor(txn_recorder.address, 12345, 'some-data')

    assert txn_recorder.call().lastCaller() == NULL_ADDRESS
    assert txn_recorder.call().lastCallValue() == 0
    assert txn_recorder.call().lastCallData() == ''
    assert txn_recorder.call().wasCalled() is False

    multisig.transact({
        'from': second_from,
    }).trapdoor(txn_recorder.address, 12345, 'some-data')

    assert txn_recorder.call().lastCaller() == multisig.address
    assert txn_recorder.call().lastCallValue() == 12345
    assert txn_recorder.call().lastCallData().startswith('some-data')
    assert txn_recorder.call().wasCalled() is True


def test_trapdoor_works_with_one_disagreement(multisig,
                                              trapdoor_a,
                                              trapdoor_b,
                                              trapdoor_c,
                                              State,
                                              txn_recorder,
                                              NULL_ADDRESS,
                                              with_both_deposits_and_locked):
    assert multisig.call().currentState() == State.Locked

    assert txn_recorder.call().lastCaller() == NULL_ADDRESS
    assert txn_recorder.call().lastCallValue() == 0
    assert txn_recorder.call().lastCallData() == ''
    assert txn_recorder.call().wasCalled() is False

    multisig.transact({
        'from': trapdoor_a,
    }).trapdoor(txn_recorder.address, 12345, 'some-data')

    assert txn_recorder.call().lastCaller() == NULL_ADDRESS
    assert txn_recorder.call().lastCallValue() == 0
    assert txn_recorder.call().lastCallData() == ''
    assert txn_recorder.call().wasCalled() is False

    multisig.transact({
        'from': trapdoor_c,
    }).trapdoor(txn_recorder.address, 54321, 'some-data')  # mismatch value

    assert txn_recorder.call().lastCaller() == NULL_ADDRESS
    assert txn_recorder.call().lastCallValue() == 0
    assert txn_recorder.call().lastCallData() == ''
    assert txn_recorder.call().wasCalled() is False

    multisig.transact({
        'from': trapdoor_b,
    }).trapdoor(txn_recorder.address, 12345, 'some-data')

    assert txn_recorder.call().lastCaller() == multisig.address
    assert txn_recorder.call().lastCallValue() == 12345
    assert txn_recorder.call().lastCallData().startswith('some-data')
    assert txn_recorder.call().wasCalled() is True


def test_trapdoor_cannot_be_called_by_anyone(multisig,
                                             web3,
                                             with_both_deposits_and_locked):
    with pytest.raises(ValueError):
        multisig.transact({
            'from': web3.eth.accounts[0],
        }).trapdoor(web3.eth.accounts[0], 12345, 'some-data')
