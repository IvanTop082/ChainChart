using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System.Numerics;

namespace FreshTestContract
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Fresh test contract for UI deployment - unique name")]
    public class FreshTest : SmartContract
    {
        private static StorageMap StorageMap => new StorageMap(Storage.CurrentContext, "storage");

        public static void Save(string key, BigInteger value)
        {
            StorageMap.Put(key, value);
        }

        public static BigInteger Load(string key)
        {
            ByteString value = StorageMap.Get(key);
            return value is null ? 0 : (BigInteger)value;
        }

        public static string GetInfo()
        {
            return "FreshTest contract deployed successfully via ChainChart UI!";
        }
    }
}

