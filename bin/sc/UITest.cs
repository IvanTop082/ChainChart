using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System.Numerics;

namespace UITestContract
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Fresh contract for UI deploy button testing")]
    public class UITest : SmartContract
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
            return "UITest contract deployed via ChainChart UI!";
        }
    }
}

