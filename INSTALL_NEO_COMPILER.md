# Installing Neo Compiler

## Option 1: Neo.Compiler.CSharp (Recommended)

This is the official Neo N3 compiler.

### Prerequisites
- .NET SDK 6.0 or later installed

### Installation

**Windows (PowerShell):**
```powershell
dotnet tool install -g Neo.Compiler.CSharp
```

**Linux/Mac:**
```bash
dotnet tool install -g Neo.Compiler.CSharp
```

### Verify Installation
```bash
neoc --version
```

### Usage
```bash
neoc compile Contract.cs -o output/
```

---

## Option 2: Neo-Express (Alternative)

Neo-express includes a compiler and local blockchain.

### Installation
```bash
dotnet tool install -g neo-express
```

### Verify Installation
```bash
neoxp --version
```

### Usage
```bash
neoxp contract compile Contract.cs --out output/
```

---

## Troubleshooting

### "dotnet: command not found"
- Install .NET SDK from: https://dotnet.microsoft.com/download
- Restart your terminal after installation

### "neoc: command not found"
- Make sure .NET tools are in your PATH
- Try: `dotnet tool list -g` to see installed tools
- On Windows, tools are usually in: `%USERPROFILE%\.dotnet\tools`

### Compilation Errors
- Make sure your C# contract follows Neo N3 syntax
- Check that all required using statements are present
- Verify contract inherits from `SmartContract`

---

## Testing Compiler

After installation, test with:

```bash
# Create a test contract
echo 'using Neo.SmartContract.Framework;
public class Test : SmartContract {
    public static void Main() { }
}' > test.cs

# Compile it
neoc compile test.cs -o output/

# Check output
ls output/
# Should see: test.nef and test.manifest.json
```

---

## Notes

- The ChainChart backend will automatically use the compiler if installed
- If compiler is not installed, mock files will be generated (for testing only)
- Real compilation is required for actual Neo blockchain deployment

