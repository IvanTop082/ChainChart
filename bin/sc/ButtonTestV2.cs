using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System.Numerics;

namespace ButtonTestV2
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Second test contract for deploy button - unique name")]
    public class ButtonTestV2 : SmartContract
    {
        private static StorageMap StorageMap => new StorageMap(Storage.CurrentContext, "storage");

        public static void Store(string key, BigInteger value)
        {
            StorageMap.Put(key, value);
        }

        public static BigInteger Retrieve(string key)
        {
            ByteString value = StorageMap.Get(key);
            return value is null ? 0 : (BigInteger)value;
        }

        public static string GetStatus()
        {
            return "ButtonTestV2 deployed successfully via UI!";
        }
    }
}

