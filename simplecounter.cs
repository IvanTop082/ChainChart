using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System.Numerics;

namespace SimpleCounterContract
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "A minimal counter smart contract")]
    public class SimpleCounter : SmartContract
    {
        private static StorageMap CounterMap => new StorageMap(Storage.CurrentContext, "counter");

        public static void Increment()
        {
            ByteString value = CounterMap.Get("value");
            BigInteger current = value is null ? 0 : (BigInteger)value;
            CounterMap.Put("value", current + 1);
        }

        public static BigInteger Get()
        {
            ByteString value = CounterMap.Get("value");
            return value is null ? 0 : (BigInteger)value;
        }
    }
}
