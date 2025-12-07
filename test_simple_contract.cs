using Neo;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;

namespace TestContract
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Simple test contract")]
    public class TestContract : SmartContract
    {
        private static StorageMap CounterMap => new StorageMap(Storage.CurrentContext, "counter");
        
        public static BigInteger GetCounter()
        {
            var value = CounterMap.Get(ByteString.Empty);
            return value is null ? 0 : (BigInteger)value;
        }
        
        public static void Increment()
        {
            var current = GetCounter();
            CounterMap.Put(ByteString.Empty, (ByteString)(current + 1));
        }
    }
}


