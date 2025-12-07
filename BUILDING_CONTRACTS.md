# Building Smart Contracts with ChainChart

## Current Status ✅
Your ChainChart system is **fully working**:
- ✅ SpoonOS AI generates contracts from diagrams
- ✅ Contracts compile to NEF + manifest
- ✅ Contracts deploy to Neo TestNet
- ✅ Full flow: Diagram → AI → Code → Compile → Deploy

## What You Can Build

### 1. **Counter Contract** (Simplest)
**What it does:** Stores a number that can be incremented/decremented

**Nodes to add:**
- **State:** `Counter` (Integer, initial value: 0)
- **Function:** `Increment()` → **Operation:** `Counter + 1` → **State:** `Counter`
- **Function:** `Decrement()` → **Operation:** `Counter - 1` → **State:** `Counter`
- **Function:** `GetCounter()` → **State:** `Counter` (returns value)

**Use cases:** Simple voting, counting, tracking

---

### 2. **Token Contract** (Most Common)
**What it does:** Create your own cryptocurrency/token

**Nodes to add:**
- **State:** `Balances` (Map: Address → Integer)
- **State:** `TotalSupply` (Integer)
- **Function:** `Transfer(from, to, amount)` → **Operation:** Check balance → **Operation:** Update balances
- **Function:** `BalanceOf(address)` → **State:** `Balances` (returns balance)
- **Function:** `Mint(to, amount)` → **Operation:** Add to supply → **State:** `Balances` + `TotalSupply`

**Use cases:** Custom tokens, rewards, points systems

---

### 3. **Voting Contract**
**What it does:** Allow people to vote on options

**Nodes to add:**
- **State:** `Votes` (Map: Candidate → Integer)
- **State:** `Voters` (Set: Address)
- **Function:** `Vote(candidate)` → **Operation:** Check if voted → **Operation:** Increment votes → **State:** `Votes`
- **Function:** `GetVotes(candidate)` → **State:** `Votes` (returns count)
- **Function:** `HasVoted(address)` → **State:** `Voters` (returns boolean)

**Use cases:** DAO governance, polls, elections

---

### 4. **Storage Contract** (Key-Value Store)
**What it does:** Store and retrieve data on-chain

**Nodes to add:**
- **State:** `Data` (Map: String → Any)
- **Function:** `Set(key, value)` → **Operation:** Store → **State:** `Data`
- **Function:** `Get(key)` → **State:** `Data` (returns value)
- **Function:** `Delete(key)` → **Operation:** Remove → **State:** `Data`

**Use cases:** Registry, database, configuration storage

---

### 5. **Multi-Signature Wallet**
**What it does:** Require multiple approvals for transactions

**Nodes to add:**
- **State:** `Owners` (Array: Address)
- **State:** `RequiredSignatures` (Integer)
- **State:** `PendingTransactions` (Map: TransactionID → Transaction)
- **Function:** `ProposeTransaction(to, amount)` → **Operation:** Create transaction → **State:** `PendingTransactions`
- **Function:** `ApproveTransaction(txId)` → **Operation:** Check signatures → **Operation:** Execute if enough → **State:** `PendingTransactions`

**Use cases:** Team wallets, treasury management, secure funds

---

## How to Build in the UI

### Step-by-Step for Counter Contract:

1. **Add State Node:**
   - Click "Add Node" → Select "State"
   - Label: `Counter`
   - Value: `0`
   - Data Type: `Integer`

2. **Add Increment Function:**
   - Click "Add Node" → Select "Function"
   - Label: `Increment`
   - Name: `Increment`

3. **Add Operation:**
   - Click "Add Node" → Select "Operation"
   - Label: `Add One`
   - Operation: `+`
   - Operand A: `Counter`
   - Operand B: `1`

4. **Connect Nodes:**
   - Draw edge: `Increment` → `Add One`
   - Draw edge: `Add One` → `Counter`

5. **Add Get Function:**
   - Add Function node: `GetCounter`
   - Draw edge: `Counter` → `GetCounter`

6. **Generate & Deploy:**
   - Click "Generate Smart Contract" (SpoonOS will create the code)
   - Click "Deploy to TestNet"

---

## Tips for Better Contracts

1. **Use meaningful names:** `Counter` not `New state`
2. **Add parameters:** Functions can take inputs (address, amount, etc.)
3. **Add conditions:** Use condition nodes to check permissions, balances, etc.
4. **Add events:** Event nodes emit notifications when things happen
5. **Test incrementally:** Start simple, add features one at a time

---

## Next Steps

1. **Try the Counter example** - Load `example_counter_diagram.json` in the UI
2. **Experiment** - Modify nodes and see what SpoonOS generates
3. **Build your own** - Start with a simple idea and expand it
4. **Deploy and test** - Use Neo TestNet to verify your contracts work

---

## Example Files

- `example_counter_diagram.json` - Simple counter with increment/decrement
- `example_token_diagram.json` - Basic token contract structure
- `basic_contract_diagram.json` - Original simple example

Load these in the UI to see how they work!

