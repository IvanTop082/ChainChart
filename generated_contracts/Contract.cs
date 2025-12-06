using Neo.SmartContract.Framework.Attributes;
using Neo;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;

namespace NeoContract
{
    [ManifestExtra("Author", "Spoon AI")]
    [ManifestExtra("Email", "")]
    [ManifestExtra("Description", "Auto-generated contract from ChainChart diagram")]
    public class Contract : SmartContract
    {
        // StorageMap for state variable
        private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "Counter");

        // Event declaration
        public static event Action NewEvent;

        // Public getter for Counter
        public static BigInteger Counter()
        {
            ByteString value = CounterMap.Get("value");
            return value is null ? 0 : (BigInteger)value;
        }

        // Increment function: Counter = Counter + 1
        public static void Increment()
        {
            ByteString value = CounterMap.Get("value");
            BigInteger counter = value is null ? 0 : (BigInteger)value;
            counter = counter + 1;
            CounterMap.Put("value", counter);
        }

        // Newfunction: emits NewEvent
        public static void Newfunction()
        {
            NewEvent();
        }
    }
}