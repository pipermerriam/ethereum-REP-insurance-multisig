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

    event EtherDeposit(address indexed who, uint amount);
    event EtherWithdrawal(address indexed who, uint amount);

    event TokenDeposit(address indexed who, uint amount);
    event TokenWithdrawal(address indexed who, uint amount);

    enum State {
        Genesis,
        WaitingForEther,
        WaitingForTokens,
        WaitingForArbiterLock,
        Locked,
        Unlocked,
        NeverLocked
    }

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

    function ethDepositMet() constant returns (bool) {
        if (msg.value > this.balance) {
            // This should be completely impossible but ensuring it can't
            // happen here anyways.
            throw;
        }
        return (this.balance - msg.value >= ethDepositMinimum);
    }

    function tokenDepositMet() constant returns (bool) {
        return (token.balanceOf(this) >= tokenDepositMinimum);
    }

    function depositsMet() constant returns (bool) {
        return (ethDepositMet() && tokenDepositMet());
    }

    function isLocked() constant returns (bool) {
        if (wasLocked()) {
            return (now < unlockAt);
        } else {
            return false;
        }
    }

    function wasLocked() constant returns (bool) {
        return (lockedAt != 0);
    }

    modifier inState(State state) {
        if (currentState() == state) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    modifier inState2(State stateA, State stateB) {
        var _currentState = currentState();
        if (_currentState == stateA || _currentState == stateB) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    modifier inState3(State stateA, State stateB, State stateC) {
        var _currentState = currentState();
        if (_currentState == stateA || _currentState == stateB || _currentState == stateC) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    modifier onlyArbiter {
        if (msg.sender == arbiter) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    modifier onlyPartyA {
        if (msg.sender == partyA) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    modifier onlyPartyB {
        if (msg.sender == partyB) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    modifier beforeUnlock {
        if (now < unlockAt) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    modifier noEther {
        if (msg.value == 0) {
            _
            // _;  // if solc 0.4.x
        } else {
            throw;
        }
    }

    modifier onlyTrapdoorMultiSig {
        if (msg.sender == trapdoorA || msg.sender == trapdoorB || msg.sender == trapdoorC) {
            _
        } else {
            throw;
        }
    }

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

    function lock() public
                    noEther
                    beforeUnlock
                    onlyArbiter
                    inState(State.WaitingForArbiterLock)
                    returns (bool) {
        lockedAt = now;
    }

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
