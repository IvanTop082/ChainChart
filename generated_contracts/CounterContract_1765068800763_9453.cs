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
    [ManifestExtra("Description", "A unique Counter contract generated from ChainChart diagram.")]
    public class CounterContract_1765068800763_9453 : SmartContract
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