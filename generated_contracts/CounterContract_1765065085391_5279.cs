using Neo.SmartContract.Framework.Attributes;
using Neo;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;

namespace ChainChartGenerated
{
    [ManifestExtra("Author", "Spoon AI")]
    [ManifestExtra("Email", "")]
    [ManifestExtra("Description", "A simple counter contract with increment functionality.")]
    public class CounterContract_1765065085391_5279 : SmartContract
    {
        private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "Counter");

        public static BigInteger Counter
        {
            get
            {
                ByteString value = CounterMap.Get("value");
                return value is null ? 0 : (BigInteger)value;
            }
        }

        public static void Increment()
        {
            BigInteger current = Counter;
            BigInteger updated = current + 1;
            CounterMap.Put("value", updated);
        }
    }
}