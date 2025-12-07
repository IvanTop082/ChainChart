# ChainChart

**Visual Smart Contract Builder for Neo N3 Blockchain**

Build, generate, compile, and deploy Neo N3 smart contracts using a visual diagram interface powered by AI.

## 🚀 Quick Start

### Prerequisites

- **Node.js 18+** and npm
- **Python 3.9+**
- **Supabase account** (for contract storage)
- **Neo TestNet private key** (WIF format, for deployment)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd ChainChart
   ```

2. **Backend Setup:**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Create .env file
   cp .env.example .env
   ```

3. **Frontend Setup:**
   ```bash
   cd chain-chart-ui
   npm install
   
   # Create .env.local file
   cp .env.example .env.local
   ```

4. **Configure Environment Variables:**

   **Backend `.env`:**
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   NEO_PRIVATE_KEY=your_wif_private_key
   NEO_RPC_URL=https://testnet.onegate.space
   OPENAI_API_KEY=your_openai_key
   SPOON_AI_API_KEY=your_spoon_ai_key
   ```

   **Frontend `.env.local`:**
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

5. **Start the servers:**
   ```bash
   # Terminal 1: Backend
   python api_server.py
   
   # Terminal 2: Frontend
   cd chain-chart-ui
   npm run dev
   ```

6. **Open your browser:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 📖 How to Use

### 1. Create a Diagram

1. Go to **Builder** page
2. Drag nodes from the palette:
   - **State**: Variables (Integer, String, Map, etc.)
   - **Function**: Public methods
   - **Operation**: Logic (add, subtract, check, etc.)
   - **Event**: Emit events
   - **Modifier**: Access control

3. Connect nodes with edges to define flow

### 2. Generate Contract

1. Click **"Generate Contract"**
2. AI generates C# Neo N3 contract code
3. Contract is automatically validated and fixed
4. Contract compiles to NEF + manifest

### 3. Deploy Contract

1. Click **"Deploy to TestNet"**
2. Contract deploys to Neo N3 TestNet
3. Get **Contract Hash** from success modal
4. Use hash to interact with contract

### 4. Use in Your Frontend

Copy the contract hash and use it in your app:

```javascript
import { rpc, sc, u } from '@cityofzion/neon-js';

const contractHash = '0x1234...'; // From deployment
const client = new rpc.RPCClient('https://testnet.onegate.space');

// Call contract method
const script = sc.createScript({
  scriptHash: contractHash,
  operation: 'increment',
  args: []
});
```

## 🎯 Example: Counter Contract

**Nodes:**
- State: `Counter` (Integer, initial: 0)
- Function: `increment()` → Operation: `Counter + 1` → State: `Counter`

**Result:**
- Generates working counter contract
- Deploys to TestNet
- Can increment counter from any frontend

## ✨ Features

- ✅ **Visual Diagram Builder** - Drag-and-drop interface
- ✅ **AI-Powered Generation** - SpoonOS AI generates contracts
- ✅ **Auto-Validation** - Fixes common bugs automatically
- ✅ **One-Click Deployment** - Deploy to Neo TestNet
- ✅ **Supabase Storage** - Contracts saved in cloud
- ✅ **Contract History** - View all generated contracts

## 📁 Project Structure

```
ChainChart/
├── api_server.py          # FastAPI backend
├── chain-chart-ui/        # Next.js frontend
├── agent/                 # AI contract generator
├── generator/             # Contract compiler & validator
├── lib/                   # Supabase helpers
└── generated_contracts/   # Compiled contracts
```

## 🔧 Key Files

- **`api_server.py`** - Backend API (contract generation, compilation, deployment)
- **`chain-chart-ui/app/builder/page.tsx`** - Main diagram builder UI
- **`agent/contract_agent.py`** - AI contract generator
- **`generator/contract_validator.py`** - Auto-fixes contract bugs

## 📚 Documentation

- **`E2E_TEST_FRONTEND_GUIDE.md`** - How to test contracts in separate frontend
- **`VERCEL_DEPLOYMENT.md`** - Deploy to production
- **`HOW_TO_INTERACT_WITH_COUNTER.md`** - Contract interaction examples

## 🐛 Troubleshooting

**Backend not starting:**
- Check Python version (3.9+)
- Install dependencies: `pip install -r requirements.txt`
- Check `.env` file exists

**Frontend not connecting:**
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

**Deployment fails:**
- Verify `NEO_PRIVATE_KEY` is set in backend `.env`
- Check private key is WIF format (starts with L or K)
- Ensure wallet has TestNet GAS

## 🚢 Deployment

See `VERCEL_DEPLOYMENT.md` for production deployment guide.

**Quick deploy:**
- Frontend: Deploy to Vercel
- Backend: Deploy to Railway/Render

## 📝 License

[Your License Here]

---

**Built with:** Next.js, FastAPI, Neo N3, SpoonOS AI, Supabase
