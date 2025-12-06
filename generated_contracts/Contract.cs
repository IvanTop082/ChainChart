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
    [ManifestExtra("Description", "Auto-generated contract from ChainChart")]
    public class Contract : SmartContract
    {
        // StorageMap for Counter
        private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "Counter");

        // Event declaration
        public static event Action NewEvent;

        // Public getter for Counter
        public static BigInteger Counter()
        {
            ByteString value = CounterMap.Get("value");
            return value is null ? 0 : (BigInteger)value;
        }

        // Increment function: Counter += 1
        public static void Increment()
        {
            BigInteger current = Counter();
            BigInteger updated = current + 1;
            CounterMap.Put("value", updated);
        }

        // Newfunction: emits New event
        public static void Newfunction()
        {
            NewEvent();
        }
    }
}