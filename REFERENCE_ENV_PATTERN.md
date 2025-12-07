# Reference: Complete Working Environment Variable Pattern

## ✅ Complete Working Example

### .env File:

```env
# Neo Configuration
NEO_PRIVATE_KEY=L5XYZ...your_actual_wif_key_here
NEO_RPC_URL=https://testnet1.neo.org:443
NEO_NETWORK=testnet

# NeoFS (uses same key)
NEOFS_PRIVATE_KEY_WIF=L5XYZ...your_actual_wif_key_here
NEOFS_OWNER_ADDRESS=NXXXxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NEOFS_BASE_URL=https://rest.fs.neo.org
```

### Backend (deploy.py):

```python
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

def get_config():
    """Get configuration with validation"""
    config = {
        'private_key': os.getenv('NEO_PRIVATE_KEY'),
        'rpc_url': os.getenv('NEO_RPC_URL', 'https://testnet1.neo.org:443'),
        'network': os.getenv('NEO_NETWORK', 'testnet')
    }
    
    # Validate
    if not config['private_key']:
        raise ValueError(
            "NEO_PRIVATE_KEY not set!\n"
            "Add to .env file:\n"
            "NEO_PRIVATE_KEY=L5XYZ..."
        )
    
    # Safe strip
    config['private_key'] = config['private_key'].strip()
    
    return config

# Use it
try:
    config = get_config()
    print(f"✅ Config loaded: {config['private_key'][:10]}...")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
```

## Key Principles:

1. **Load .env at module level** - `load_dotenv()` called once at import
2. **Centralized config function** - `get_config()` validates and returns all config
3. **Validation before use** - Check if values exist before stripping
4. **Safe stripping** - Only strip after validation
5. **Clear error messages** - Tell user exactly what's missing
6. **Fallback values** - Provide defaults for optional config
7. **Try/except handling** - Catch configuration errors gracefully

## Current Implementation Status:

✅ Our code follows this pattern:
- `load_dotenv()` called at module level in `api_server.py` and `generator/neonova_deploy_neonjs.py`
- Validation checks before using values
- Safe stripping with None checks
- Error handling with clear messages

## When Things Go Wrong:

1. Check `.env` file location (must be in project root)
2. Verify `load_dotenv()` is called before accessing `os.getenv()`
3. Validate values exist before calling `.strip()`
4. Use centralized config function pattern
5. Provide clear error messages with instructions



