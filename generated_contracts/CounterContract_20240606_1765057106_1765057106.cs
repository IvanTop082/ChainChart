using Neo.SmartContract.Framework.Attributes;
using Neo;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;

namespace CounterContract_20240606_1765057106
{
    [ManifestExtra("Author", "SpoonAI")]
    [ManifestExtra("Email", "")]
    [ManifestExtra("Description", "A simple counter contract with increment functionality.")]
    public class CounterContract_20240606_1765057106_1765057106 : SmartContract
    {
        private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "Counter");

        public static BigInteger Counter
        {
            get
            {
                ByteString value = CounterMap.Get("counter");
                return value is null ? 0 : (BigInteger)value;
            }
        }

        public static void Increment()
        {
            BigInteger current = Counter;
            BigInteger updated = current + 1;
            CounterMap.Put("counter", updated);
        }
    }
}