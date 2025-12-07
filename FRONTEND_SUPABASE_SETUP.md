# Frontend Supabase Contract Storage

## Overview
Smart contracts are now saved directly from the **frontend** to Supabase. This is simpler because:
- ✅ Frontend already has Supabase client and auth
- ✅ No need for backend Supabase configuration
- ✅ Direct database access from the UI
- ✅ Automatic unique contract names

## How It Works

### Contract Generation Flow:

1. **User clicks "Generate Smart Contract"**
   - Frontend calls backend `/export-contract` endpoint
   - Backend generates contract with unique name (e.g., `CounterContract_1734567890`)
   - Backend saves to filesystem (`generated_contracts/`)
   - **Frontend saves to Supabase** with:
     - Contract name (extracted from code)
     - Contract code (C# source)
     - NEF data (base64 encoded)
     - Manifest data (JSON)
     - Project ID (if available)
   - Frontend stores `contract_id` in state

2. **User clicks "Deploy to TestNet"**
   - Frontend fetches contract from Supabase (if `contract_id` exists)
   - Frontend passes NEF + manifest to backend `/deploy-contract`
   - Backend deploys to Neo TestNet
   - **Frontend updates Supabase** with:
     - `tx_hash` (transaction hash)
     - `contract_hash` (deployed contract hash)
     - `status: 'deployed'`

## Setup

### 1. Run Database Migration

Run the SQL in `ChainChart_new ui/supabase-contracts-schema.sql` in your Supabase SQL Editor:

1. Go to Supabase Dashboard → SQL Editor
2. Paste the contents of `supabase-contracts-schema.sql`
3. Click "Run"

### 2. Frontend Environment Variables

Make sure your `ChainChart_new ui/.env.local` (or `.env`) has:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

These should already be set if you're using Supabase for projects.

## Benefits

1. **No Backend Changes Needed** - Backend doesn't need Supabase keys
2. **Automatic Unique Names** - Each contract gets a unique name
3. **User Authentication** - Uses existing Supabase auth
4. **Project Association** - Contracts linked to projects
5. **Deployment Tracking** - Know which contracts are deployed

## Code Changes

### New Functions in `lib/supabase/storage.ts`:
- `saveContract()` - Save contract to Supabase
- `getLatestContract()` - Get most recent contract
- `getContract()` - Get contract by ID
- `updateContractDeployment()` - Update deployment info
- `getContracts()` - Get all user contracts

### Updated `app/builder/page.tsx`:
- Saves contract to Supabase after generation
- Fetches from Supabase before deployment
- Updates Supabase after successful deployment

## Database Schema

```sql
contracts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  project_id UUID REFERENCES projects(id),
  contract_name TEXT,  -- e.g., "CounterContract_1734567890"
  contract_code TEXT,  -- C# source code
  nef_data TEXT,  -- Base64 encoded NEF
  manifest_data JSONB,  -- Manifest JSON
  contract_hash TEXT,  -- Deployed contract hash
  tx_hash TEXT,  -- Deployment transaction hash
  status TEXT,  -- 'generated', 'compiled', 'deployed', 'failed'
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

## Fallback Behavior

If user is not authenticated:
- ✅ Contract still generates and saves to filesystem
- ✅ Deployment still works
- ⚠️ No Supabase storage
- ⚠️ No unique naming (uses default "Contract")

## Testing

1. **Generate Contract:**
   - Click "Generate Smart Contract"
   - Check Supabase `contracts` table for new entry
   - Verify `contract_name` is unique

2. **Deploy Contract:**
   - Click "Deploy to TestNet"
   - Check that `tx_hash` and `contract_hash` are saved to Supabase
   - Verify `status` is updated to 'deployed'

3. **Multiple Contracts:**
   - Generate multiple contracts
   - Each should have a unique `contract_name`
   - All should be linked to your `user_id`

## Troubleshooting

**"User must be authenticated" error:**
- Make sure you're logged in
- Check Supabase auth is working

**Contract not saving to Supabase:**
- Check browser console for errors
- Verify Supabase environment variables are set
- Check RLS policies allow user to insert contracts

**Deployment not updating Supabase:**
- Check `currentContractId` is set after generation
- Verify contract exists in Supabase
- Check RLS policies allow user to update contracts

