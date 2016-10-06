//pragma solidity ^0.4.0;


import {TokenInterface} from "contracts/TokenInterface.sol";


contract MultiSignature {
    // The party who is depositing ether
    address public partyA;
    // The party who is depositing tokens
    address public partyB;
    // The 3rd party who will arbitrate the terms of the contract.
    address public arbiter;

    // The opinion of partyA as to who should receive the tokens.
    address public partyAVote;
    // The opinion of partyB as to who should receive the tokens.
    address public partyBVote;
    // The opinion of aribiter as to who should receive the tokens.
    address public arbiterVote;

    // The minimum ether deposit amount (in wei)
    uint public ethDepositMinimum;
    // The minimum token deposit amount.
    uint public tokenDepositMinimum;

    // The UTC time that the arbiter locked this contract.
    uint public lockedAt;
    // The UTC time that this contract will become *unlocked*.
    uint public unlockAt;

    // Three address multisig that can execute the trapdoor function.
    address public trapdoorA;
    address public trapdoorB;
    address public trapdoorC;

    // Storage for the desired execution to be sent from the trapdoor.
    mapping (address => bytes32) public trapdoorData;

    TokenInterface public token;

    string public contractTerms;

    function MultiSignature(address[3] participants,
                            address[3] rescuers,
                            uint _ethDepositMinimum,
                            uint _tokenDepositMinimum,
                            address _tokenAddress,
                            uint _unlockAt,
                            string _contractTerms) {
        partyA = participants[0];
        partyB = participants[1];
        arbiter = participants[2];

        trapdoorA = rescuers[0];
        trapdoorB = rescuers[1];
        trapdoorC = rescuers[2];

        ethDepositMinimum = _ethDepositMinimum;
        tokenDepositMinimum = _tokenDepositMinimum;
        token = TokenInterface(_tokenAddress);

        unlockAt = _unlockAt;
        contractTerms = _contractTerms;
    }

    /*
     *  ----------
     *  | Events |
     *  ----------
     */
    event EtherDeposit(address indexed who, uint amount);
    event EtherWithdrawal(address indexed who, uint amount);

    event TokenDeposit(address indexed who, uint amount);
    event TokenWithdrawal(address indexed who, uint amount);

    /*
     *  -----------------------------
     *  | Contract State Management |
     *  -----------------------------
     */
    enum State {
        Genesis,
        WaitingForEther,
        WaitingForTokens,
        WaitingForArbiterLock,
        Locked,
        Unlocked,
        NeverLocked
    }

    /*
     *  The current "state" that the contract is in.
     */
    function currentState() constant returns (State) {
        if (isLocked()) {
            return State.Locked;
        } else if (wasLocked()) {
            return State.Unlocked;
        } else if (now >= unlockAt) {
            return State.NeverLocked;
        } else if (depositsMet()) {
            return State.WaitingForArbiterLock;
        } else if (ethDepositMet()) {
            return State.WaitingForTokens;
        } else if (tokenDepositMet()) {
            return State.WaitingForEther;
        } else {
            return State.Genesis;
        }
    }

    /*
     *  Has the minimum ether deposit been met.  This is crafted specially to
     *  ensure it still returns `false` during the transaction that the deposit
     *  is sent.
     */
    function ethDepositMet() constant returns (bool) {
        if (msg.value > this.balance) {
            // This should be completely impossible but ensuring it can't
            // happen here anyways.
            throw;
        }
        return (this.balance - msg.value >= ethDepositMinimum);
    }

    /*
     *  Has the minimum token deposit been met.
     */
    function tokenDepositMet() constant returns (bool) {
        return (token.balanceOf(this) >= tokenDepositMinimum);
    }

    /*
     *  Have both deposit minimums been met
     */
    function depositsMet() constant returns (bool) {
        return (ethDepositMet() && tokenDepositMet());
    }

    /*
     *  Is the contract currently locked.
     */
    function isLocked() constant returns (bool) {
        if (wasLocked()) {
            return (now < unlockAt);
        } else {
            return false;
        }
    }

    /*
     *  Did the arbiter ever lock the contract
     */
    function wasLocked() constant returns (bool) {
        return (lockedAt != 0);
    }

    /*
     *  -------------
     *  | Modifiers |
     *  -------------
     */

    /*
     *  Only allow execution if the contract is in the specified state.
     */
    modifier inState(State state) {
        if (currentState() == state) {
            _
        } else {
            throw;
        }
    }

    /*
     *  Only allow execution if the contract is in one of the two provided
     *  states.
     */
    modifier inState2(State stateA, State stateB) {
        var _currentState = currentState();
        if (_currentState == stateA || _currentState == stateB) {
            _
        } else {
            throw;
        }
    }

    /*
     *  Only allow execution if the contract is in one of the three provided
     *  states.
     */
    modifier inState3(State stateA, State stateB, State stateC) {
        var _currentState = currentState();
        if (_currentState == stateA || _currentState == stateB || _currentState == stateC) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    /*
     *  Only allow execution from the arbiter
     */
    modifier onlyArbiter {
        if (msg.sender == arbiter) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    /*
     *  Only allow execution from partyA
     */
    modifier onlyPartyA {
        if (msg.sender == partyA) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    /*
     *  Only allow execution from partyb
     */
    modifier onlyPartyB {
        if (msg.sender == partyB) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    /*
     *  Only allow execution prior to the `unlockAt` time.
     */
    modifier beforeUnlock {
        if (now < unlockAt) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    /*
     *  Do not allow sending of ether to this function.
     */
    modifier noEther {
        if (msg.value == 0) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    /*
     *  Only allow one of the trapdoor multisig accounts to execute this
     *  function.
     */
    modifier onlyTrapdoorMultiSig {
        if (msg.sender == trapdoorA || msg.sender == trapdoorB || msg.sender == trapdoorC) {
            _
        } else {
            throw;
        }
    }

    /*
     *  -----------
     *  | Actions |
     *  -----------
     */

    /*
     *  Function for partyA to deposit ether
     */
    function depositEther() public
                            beforeUnlock
                            onlyPartyA
                            inState2(State.Genesis, State.WaitingForEther)
                            returns (bool) {
        if (msg.value >= ethDepositMinimum) {
            EtherDeposit(msg.sender, msg.value);
            return true;
        } else {
            if (msg.sender.call.value(msg.value)()) {
                return false;
            } else {
                throw;
            }
        }
    }

    /*
     *  Function for partyB to deposit tokens.  This handles both a direct
     *  transfer out of band, or using the `transferFrom` and `approve` API.
     */
    function depositToken() public 
                            noEther
                            beforeUnlock
                            onlyPartyB
                            inState2(State.Genesis, State.WaitingForTokens)
                            returns (bool) {
        uint currentTokenBalance = token.balanceOf(this);
        if (currentTokenBalance >= tokenDepositMinimum) {
            return true;
        }
        uint neededTokens = tokenDepositMinimum - currentTokenBalance;
        if (token.allowance(msg.sender, this) >= neededTokens) {
            if (token.transferFrom(msg.sender, this, neededTokens)) {
                TokenDeposit(msg.sender, neededTokens);
                return true;
            }
        }
        return false;
    }

    /*
     *  Function for the arbiter to enable the lock.
     */
    function lock() public
                    noEther
                    beforeUnlock
                    onlyArbiter
                    inState(State.WaitingForArbiterLock)
                    returns (bool) {
        lockedAt = now;
    }

    /*
     *  Function for partyA to recover their ether
     */
    function refundEther() public
                           noEther
                           onlyPartyA
                           inState3(
                               State.WaitingForTokens,
                               State.WaitingForArbiterLock,
                               State.NeverLocked
                           )
                           returns (bool) {
        var etherBalance = this.balance;
        if (this.balance > 0 && partyA.call.value(this.balance)()) {
            EtherWithdrawal(partyA, etherBalance);
            return true;
        } else {
            return false;
        }
    }

    /*
     *  Function for partyA to recover their tokens
     */
    function refundTokens() public
                            noEther
                            onlyPartyB
                            inState3(
                                State.WaitingForEther,
                                State.WaitingForArbiterLock,
                                State.NeverLocked
                            )
                            returns (bool) {
        var tokenBalance = token.balanceOf(this);
        if (tokenBalance > 0 && token.transfer(partyB, tokenBalance)) {
            TokenWithdrawal(partyB, tokenBalance);
            return true;
        }
        return false;
    }

    /*
     *  Function for partyB to withdraw the ether deposit once the contract has
     *  been locked.
     */
    function withdrawEther() public
                             noEther
                             inState2(State.Locked, State.Unlocked)
                             returns (bool) {
        var etherBalance = this.balance;
        if (etherBalance > 0 && partyB.call.value(this.balance)()) {
            EtherWithdrawal(partyB, etherBalance);
            return true;
        } else {
            return false;
        }
    }

    /*
     *  Function for sending the tokens once the contract has been resolved
     *  through voting.
     */
    function withdrawTokens() public
                              noEther
                              inState(State.Unlocked)
                              returns (bool) {
        uint tokenBalance = token.balanceOf(this);

        if (tokenBalance == 0) {
            return false;
        }

        uint numAVotes;
        uint numBVotes;

        if (partyAVote == partyA) {
            numAVotes += 1;
        } else if (partyAVote == partyB) {
            numBVotes += 1;
        }

        if (partyBVote == partyA) {
            numAVotes += 1;
        } else if (partyBVote == partyB) {
            numBVotes += 1;
        }

        if (arbiterVote == partyA) {
            numAVotes += 1;
        } else if (arbiterVote == partyB) {
            numBVotes += 1;
        }

        if (numAVotes >= 2) {
            if (token.transfer(partyA, token.balanceOf(this))) {
                TokenWithdrawal(partyA, tokenBalance);
                return true;
            }
        } else if (numBVotes >= 2) {
            if (token.transfer(partyB, token.balanceOf(this))) {
                TokenWithdrawal(partyB, tokenBalance);
                return true;
            }
        }
        return false;
    }

    /*
     *  Function for partyA to vote on the recipient of the tokens.
     */
    function submitPartyAVote(address _who) public
                                            noEther
                                            inState(State.Unlocked)
                                            onlyPartyA
                                            returns (bool) {
        if (_who != partyA && _who != partyB) {
            return false;
        } else if (partyAVote != 0x0) {
            return false;
        } else {
            partyAVote = _who;
            return true;
        }
    }

    /*
     *  Function for partyB to vote on the recipient of the tokens.
     */
    function submitPartyBVote(address _who) public
                                            noEther
                                            inState(State.Unlocked)
                                            onlyPartyB
                                            returns (bool) {
        if (_who != partyA && _who != partyB) {
            return false;
        } else if (partyBVote != 0x0) {
            return false;
        } else {
            partyBVote = _who;
            return true;
        }
    }

    /*
     *  Function for the arbiter to vote on the recipient of the tokens.
     */
    function submitArbiterVote(address _who) public
                                            noEther
                                            inState(State.Unlocked)
                                            onlyArbiter
                                            returns (bool) {
        if (_who != partyA && _who != partyB) {
            return false;
        } else if (arbiterVote != 0x0) {
            return false;
        } else {
            arbiterVote = _who;
            return true;
        }
    }

    event TrapdoorInitiated(address _from, bytes32 _hash);
    event TrapdoorExecuted(bytes32 _hash);

    /*
     *  Safety hatch style function that allows anything in the contract to be
     *  recovered in the event that something unforseen happens.  Requires
     *  multisignature action from 2 of 3 of the trapdoor addresses.
     */
    function trapdoor(address to,
                      uint callValue,
                      bytes callData) public
                                      onlyTrapdoorMultiSig
                                      returns (bool)
    {
        bytes32 executionHash = sha3(to, callValue, callData);
        trapdoorData[msg.sender] = executionHash;

        TrapdoorInitiated(msg.sender, executionHash);

        uint numSigs;

        if (trapdoorData[trapdoorA] == executionHash) {
            numSigs += 1;
        }

        if (trapdoorData[trapdoorB] == executionHash) {
            numSigs += 1;
        }

        if (trapdoorData[trapdoorC] == executionHash) {
            numSigs += 1;
        }

        if (numSigs >= 2) {
            trapdoorData[trapdoorA] = 0x0;
            trapdoorData[trapdoorB] = 0x0;
            trapdoorData[trapdoorC] = 0x0;

            bool result = to.call.value(callValue)(callData);
            TrapdoorExecuted(executionHash);
        }
    }
}
