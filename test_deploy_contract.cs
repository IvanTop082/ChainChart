using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System.Numerics;

namespace TestDeployContract
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "A test contract for deployment verification")]
    public class TestDeploy : SmartContract
    {
        private static StorageMap DataMap => new StorageMap(Storage.CurrentContext, "data");

        public static void SetValue(string key, BigInteger value)
        {
            DataMap.Put(key, value);
        }

        public static BigInteger GetValue(string key)
        {
            ByteString value = DataMap.Get(key);
            return value is null ? 0 : (BigInteger)value;
        }

        public static string Hello()
        {
            return "Hello from deployed contract!";
        }
    }
}

