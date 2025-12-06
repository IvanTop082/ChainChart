# Export Smart Contract - Complete Setup Guide

## ✅ What's Been Implemented

1. **Backend API Endpoint**: `POST /export-contract`
2. **Frontend Button**: "Export Smart Contract" in the toolbar
3. **Test Script**: `test_export_endpoint.py`

---

## 🚀 Step 1: Restart API Server

The new endpoint requires a server restart:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
python api_server.py
```

The server should now have the `/export-contract` endpoint available.

---

## 🧪 Step 2: Test the API Endpoint

### Option A: Using the Test Script

```bash
# Make sure API server is running first
python test_export_endpoint.py
```

Expected output:
```
✅ Status Code: 200
✅ Contract generated: XXXX chars
✅ Manifest generated
✅ NEF generated: XXXX chars (base64)
💾 Files saved to: generated_contract.cs, generated_manifest.json, generated_contract.nef
```

### Option B: Using curl

```bash
curl -X POST http://localhost:8000/export-contract \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [
      {
        "id": "1",
        "type": "state",
        "label": "balance",
        "value": "",
        "position": {"x": 0, "y": 0},
        "metadata": {"label": "balance", "dataType": "BigInteger"}
      },
      {
        "id": "2",
        "type": "function",
        "label": "transfer",
        "value": "",
        "position": {"x": 0, "y": 0},
        "metadata": {
          "name": "transfer",
          "params": "UInt160 to, BigInteger amount",
          "visibility": "public"
        }
      }
    ],
    "edges": [
      {"from": "1", "to": "2"}
    ]
  }'
```

---

## 🔧 Step 3: Install Neo Compiler (Optional)

For real compilation (not mock files), install the Neo compiler:

### Windows (PowerShell):
```powershell
dotnet tool install -g Neo.Compiler.CSharp
```

### Verify Installation:
```bash
neoc --version
```

**Note**: Without the compiler, the endpoint will return mock NEF/manifest files (for testing only).

See `INSTALL_NEO_COMPILER.md` for detailed instructions.

---

## 🎨 Step 4: Frontend Integration

The "Export Smart Contract" button has been added to the UI!

### Location
- **Toolbar** (top right)
- Between "Export JSON" and "Save" buttons
- Blue button with file code icon

### How It Works

1. **Click "Export Smart Contract"** button
2. Backend generates contract from your diagram
3. Backend compiles contract (or generates mock files)
4. Browser automatically downloads 3 files:
   - `{ProjectName}.cs` - C# contract source code
   - `{ProjectName}.manifest.json` - Contract manifest
   - `{ProjectName}.nef` - Compiled Neo executable

### Features

- ✅ Disabled when no nodes in diagram
- ✅ Shows loading spinner while exporting
- ✅ Downloads all three files automatically
- ✅ Shows success/error alerts

### Testing in UI

1. Open `http://localhost:3000/builder` (or your Next.js port)
2. Add some nodes (State, Function, Event)
3. Click **"Export Smart Contract"** button
4. Check your Downloads folder for the files

---

## 📋 Complete Checklist

- [ ] Restart API server (`python api_server.py`)
- [ ] Test API endpoint (`python test_export_endpoint.py`)
- [ ] (Optional) Install Neo compiler (`dotnet tool install -g Neo.Compiler.CSharp`)
- [ ] Test in UI - add nodes and click "Export Smart Contract"
- [ ] Verify downloaded files (.cs, .manifest.json, .nef)

---

## 🐛 Troubleshooting

### API Returns 404
- **Solution**: Restart the API server to load the new endpoint

### API Returns 500 Error
- **Check**: Backend console for error details
- **Common**: Missing nodes, invalid diagram format

### Files Not Downloading in UI
- **Check**: Browser console for errors
- **Check**: Backend is running on port 8000
- **Check**: CORS is configured correctly

### Mock Files Generated
- **Expected**: If Neo compiler is not installed
- **Solution**: Install compiler for real compilation (see Step 3)

### Compiler Not Found
- **Check**: `.dotnet/tools` is in your PATH
- **Windows**: Tools are in `%USERPROFILE%\.dotnet\tools`
- **Verify**: Run `neoc --version` in terminal

---

## 📁 Files Created

- `test_export_endpoint.py` - API endpoint test script
- `INSTALL_NEO_COMPILER.md` - Compiler installation guide
- `EXPORT_CONTRACT_SETUP.md` - This file

### Modified Files

- `api_server.py` - Added `/export-contract` endpoint
- `ChainChart_ui/lib/api.ts` - Added `exportContract()` function
- `ChainChart_ui/app/builder/page.tsx` - Added "Export Smart Contract" button

---

## 🎯 Next Steps

1. **Test the endpoint** - Run `python test_export_endpoint.py`
2. **Test in UI** - Click the button and verify downloads
3. **Install compiler** - For real compilation (optional)
4. **Deploy to Neo** - Use the generated NEF + manifest on Neo TestNet

---

## 💡 Usage Example

```typescript
// In your React component
import { exportContract } from '@/lib/api';

const handleExport = async () => {
  const result = await exportContract({ nodes, edges });
  
  if (result.success) {
    // Files are automatically downloaded by the button handler
    console.log('Contract:', result.contract);
    console.log('Manifest:', result.manifest);
    console.log('NEF:', result.nef);
  }
};
```

The button in the UI already handles all of this automatically! 🎉

