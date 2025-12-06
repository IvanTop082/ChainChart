using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System.Numerics;

namespace ButtonTestContract
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Test contract for deploy button functionality")]
    public class ButtonTest : SmartContract
    {
        private static StorageMap DataMap => new StorageMap(Storage.CurrentContext, "data");

        public static void SetData(string key, BigInteger value)
        {
            DataMap.Put(key, value);
        }

        public static BigInteger GetData(string key)
        {
            ByteString value = DataMap.Get(key);
            return value is null ? 0 : (BigInteger)value;
        }

        public static string GetMessage()
        {
            return "Button test contract deployed successfully!";
        }
    }
}

