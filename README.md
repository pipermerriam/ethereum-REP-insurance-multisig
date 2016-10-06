# Contract Specification

## Contract Data:

* `address partyA`
    * The address that will be depositing Ether
* `address partyB`
    * The address that will be depositing Tokens
* `address arbiter`
    * The address that can *lock* the contract once both deposits are received.
    * The address that can settle a dispute during resolution.
* `address partyAVote`
    * The address that `partyA` thinks should receive the tokens during resolution.
* `address partyBVote`
    * The address that `partyB` thinks should receive the tokens during resolution.
* `address arbiterVote`
    * The address that `arbiter` thinks should receive the tokens during resolution.
* `uint ethDepositMinimum`
    * The minimum deposit of ether (in wei) that will be accepted.
* `uint tokenDepositMinimum`
    * The minimum deposit of Tokens that will be accepted.
* `uint lockedAt`
    * The timestamp at which the `arbiter` locked the contract.
* `uint unlockAt`
    * The timestamp at which point the contract will become unlocked once locked.
* `address trapdoorA`
    * The first address of the set of three addresses that can enact the trapdoor.
* `address trapdoorB`
    * The second address of the set of three addresses that can enact the trapdoor.
* `address trapdoorC`
    * The third address of the set of three addresses that can enact the trapdoor.
* `mapping (address => bytes32) trapdoorData`
    * The `sha3` of the transaction that is being queued for the trapdoor.
* `TokenInterface token`
    * The address of the token contract.
* `string contractTerms`
    * A string registered at creation time that indicates what the agreed upon
      terms are for this contract.

## Contract States

The contract can be in the following states if the listed conditions are met.

* Genesis
    * No deposits received.
    * Before `unlockAt`.
* WaitingForEther
    * Before `unlockAt`.
    * Has received the `tokenDepositMinimum` tokens from `partyB`
    * Has not received the `ethDepositMinimum` ether from `partyA`
* WaitingForTokens
    * Before `unlockAt`.
    * Has not received the `tokenDepositMinimum` tokens from `partyB`
    * Has received the `ethDepositMinimum` ether from `partyA`
* WaitingForArbiterLock
    * Before `unlockAt`.
    * Has received the `tokenDepositMinimum` tokens from `partyB`
    * Has received the `ethDepositMinimum` ether from `partyA`
    * Has not been locked by `arbiter`
* Locked
    * Has received the `tokenDepositMinimum` tokens from `partyB`
    * Has received the `ethDepositMinimum` ether from `partyA`
    * Before `unlockAt`.
    * Has been locked by `arbiter`
* Unlocked
    * Has received the `tokenDepositMinimum` tokens from `partyB`
    * Has received the `ethDepositMinimum` ether from `partyA`
    * Has been locked by `arbiter`
    * At or After `unlockAt`.
* NeverLocked
    * Was not locked by `arbiter`
    * At or After `unlockAt`.


At deployment contract is in *Genesis* state.

When both deposits have been received the contract moves to the
*WaitingForArbiterLock* state.

If the `arbiter` never locks the contract and it is on or after `unlockAt` the
contract enters the *NeverLocked* state.

Anytime prior to the *Locked* stater or in the *NeverLocked* state both token
and ethere deposits can be refunded.

If the contract is in the *WaitingForArbiterLock* and the current time is
before the `unlockAt` time the arbiter can lock the contract which transitions
it into the *Locked* state.

Once the current time is on or after `unlockAt`, the contract transitions to
the *Unlocked* state.

The `partyB` address can withdraw the deposited ether in both the *Locked* and
*Unlocked* states.

Once the contract is in the *Unlocked* state, any of the `arbiter`, `partyA`
and `partyB` may vote on whether `partyA` or `partyB` should receive the
deposited tokens.  Once one of these addresses has at least 2 votes, the tokens
can be withdrawn to that address.

At any point during the contract lifecycle the trapdoor may be enacted by
cooperation between at least two of the trapdoor addresses.  The trapdoor can
send arbitrary transactions from the contract enabling them full access and
control over both the ether and tokens.
