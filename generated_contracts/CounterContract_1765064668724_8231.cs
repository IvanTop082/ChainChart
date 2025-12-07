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
    [ManifestExtra("Description", "A unique counter contract that increments a stored value.")]
    public class CounterContract_1765064668724_8231 : SmartContract
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