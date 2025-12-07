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
    [ManifestExtra("Description", "A simple counter contract generated from ChainChart diagram.")]
    public class CounterContract_1765071119946_2338 : SmartContract
    {
        private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "Counter");
        private static readonly StorageMap NewStateMap = new(Storage.CurrentContext, "NewState");

        public static BigInteger Counter
        {
            get
            {
                ByteString value = CounterMap.Get("counter");
                return value is null ? 0 : (BigInteger)value;
            }
        }

        public static BigInteger NewState
        {
            get
            {
                ByteString value = NewStateMap.Get("newstate");
                return value is null ? 0 : (BigInteger)value;
            }
        }

        public static void Increment()
        {
            ByteString counterValue = CounterMap.Get("counter");
            BigInteger counter = counterValue is null ? 0 : (BigInteger)counterValue;
            counter = counter + 1;
            CounterMap.Put("counter", counter);
        }
    }
}