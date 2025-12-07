# Supabase Contract Storage Setup

## Overview
Smart contracts are now saved to Supabase database instead of just the filesystem. This provides:
- ✅ Persistent storage across sessions
- ✅ Version history
- ✅ Unique contract names automatically
- ✅ Deployment tracking

## Setup Steps

### 1. Install Supabase Python Client

```bash
pip install supabase
```

### 2. Add Environment Variables

Add to your `.env` file (root directory):

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
# OR use anon key (less secure, but works):
# SUPABASE_ANON_KEY=your-anon-key
```

**Where to find these:**
1. Go to your Supabase project dashboard
2. Settings → API
3. Copy "Project URL" → `SUPABASE_URL`
4. Copy "service_role" key → `SUPABASE_SERVICE_ROLE_KEY` (recommended)
   - OR copy "anon" key → `SUPABASE_ANON_KEY` (less secure)

### 3. Run Database Migration

Run the SQL in `ChainChart_new ui/supabase-contracts-schema.sql` in your Supabase SQL Editor:

1. Go to Supabase Dashboard → SQL Editor
2. Paste the contents of `supabase-contracts-schema.sql`
3. Click "Run"

This creates the `contracts` table with proper RLS policies.

## How It Works

### Contract Generation Flow:

1. **User clicks "Generate Smart Contract"**
   - Frontend sends diagram + `user_id` + `project_id` to backend
   - Backend generates contract with unique name (e.g., `CounterContract_1734567890`)
   - Contract is saved to:
     - ✅ Supabase database (if configured)
     - ✅ Filesystem (`generated_contracts/CounterContract_1734567890.*`)
   - Backend returns `contract_id` to frontend

2. **User clicks "Deploy to TestNet"**
   - Frontend sends `contract_id` + `user_id` to backend
   - Backend fetches contract from Supabase (or falls back to filesystem)
   - Contract is deployed to Neo TestNet
   - Deployment info (tx_hash, contract_hash) is saved back to Supabase

### Database Schema:

```sql
contracts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  project_id UUID REFERENCES projects(id),
  contract_name TEXT,  -- e.g., "CounterContract_1734567890"
  contract_code TEXT,  -- C# source code
  nef_data BYTEA,  -- Compiled NEF (binary)
  manifest_data JSONB,  -- Manifest JSON
  contract_hash TEXT,  -- Deployed contract hash
  tx_hash TEXT,  -- Deployment transaction hash
  status TEXT,  -- 'generated', 'compiled', 'deployed', 'failed'
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

## Benefits

1. **Unique Names**: Each contract gets a unique name automatically (timestamp-based)
2. **No Conflicts**: Can't deploy the same contract twice (different names)
3. **History**: All contracts are saved with timestamps
4. **Cross-Device**: Contracts accessible from any device (via Supabase)
5. **Deployment Tracking**: Know which contracts are deployed and their hashes

## Fallback Behavior

If Supabase is not configured:
- ✅ Contracts still save to filesystem
- ✅ Deployment still works
- ⚠️ No unique naming (uses default "Contract")
- ⚠️ No cross-device access

## Testing

1. Generate a contract → Check Supabase `contracts` table
2. Deploy contract → Check that `contract_hash` and `tx_hash` are saved
3. Generate another contract → Should have different `contract_name`

## Troubleshooting

**"Supabase not available" warning:**
- Check `.env` has `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Verify Supabase client is installed: `pip install supabase`

**"Contract not found in Supabase":**
- Check `contract_id` is correct
- Verify RLS policies allow user to read their contracts
- Check user_id matches the contract owner

**Contracts still using generic names:**
- Check backend logs for "Extracted contract name"
- Verify contract code has a class declaration
- Check that unique name generation is working

