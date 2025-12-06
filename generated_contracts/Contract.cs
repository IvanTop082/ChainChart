using Neo.SmartContract.Framework.Attributes;
using Neo;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;

namespace NeoN3Contract
{
    [ManifestExtra("Author", "Spoon AI")]
    [ManifestExtra("Email", "")]
    [ManifestExtra("Description", "Auto-generated contract from ChainChart diagram")]
    public class Contract : SmartContract
    {
        // StorageMap for state variable 'Counter'
        private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "Counter");

        // Event declaration
        public static event Action NewEvent;

        // Public static method: Increment
        public static void Increment()
        {
            // Get current counter value
            ByteString counterBytes = CounterMap.Get("counter");
            BigInteger counter = counterBytes is null ? 0 : (BigInteger)counterBytes;

            // Add 1 to counter
            counter = counter + 1;

            // Store updated counter
            CounterMap.Put("counter", counter);

            // After operation, as per edge, call Newfunction()
            Newfunction();
        }

        // Public static method: Newfunction
        public static void Newfunction()
        {
            // Emit NewEvent as per edge
            NewEvent();
        }

        // Optional: Public getter for Counter (since it's public in the diagram)
        public static BigInteger GetCounter()
        {
            ByteString counterBytes = CounterMap.Get("counter");
            return counterBytes is null ? 0 : (BigInteger)counterBytes;
        }
    }
}