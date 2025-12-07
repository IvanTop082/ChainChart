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
    public class CounterContract_1765065942375_2642 : SmartContract
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
            ByteString value = CounterMap.Get("counter");
            BigInteger current = value is null ? 0 : (BigInteger)value;
            BigInteger updated = current + 1;
            CounterMap.Put("counter", updated);
        }
    }
}