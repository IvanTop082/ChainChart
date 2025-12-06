using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System.Numerics;

namespace UIDeployTest
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Fresh contract for UI deploy button testing - unique name")]
    public class UIDeployTest : SmartContract
    {
        private static StorageMap StorageMap => new StorageMap(Storage.CurrentContext, "data");

        public static void Put(string key, BigInteger value)
        {
            StorageMap.Put(key, value);
        }

        public static BigInteger Get(string key)
        {
            ByteString value = StorageMap.Get(key);
            return value is null ? 0 : (BigInteger)value;
        }

        public static string Message()
        {
            return "UIDeployTest successfully deployed via ChainChart UI!";
        }
    }
}

