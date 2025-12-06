using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System.Numerics;

namespace FinalTestContract
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Final test contract for UI deployment - unique name")]
    public class FinalTest : SmartContract
    {
        private static StorageMap StorageMap => new StorageMap(Storage.CurrentContext, "data");

        public static void Set(string key, BigInteger value)
        {
            StorageMap.Put(key, value);
        }

        public static BigInteger Get(string key)
        {
            ByteString value = StorageMap.Get(key);
            return value is null ? 0 : (BigInteger)value;
        }

        public static string Status()
        {
            return "FinalTest contract deployed via ChainChart UI!";
        }
    }
}

