using Neo.SmartContract.Framework.Attributes;
using Neo;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;

namespace ChainChartGenerated
{
    [ManifestExtra("Author", "SpoonAI")]
    [ManifestExtra("Email", "")]
    [ManifestExtra("Description", "A simple counter contract with increment functionality.")]
    public class CounterContract_1765064753441_8910 : SmartContract
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
            ByteString currentValue = CounterMap.Get("counter");
            BigInteger counter = currentValue is null ? 0 : (BigInteger)currentValue;
            counter = counter + 1;
            CounterMap.Put("counter", counter);
        }
    }
}