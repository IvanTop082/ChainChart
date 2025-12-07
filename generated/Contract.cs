using Neo;
using Neo.SmartContract;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;
using System.Runtime.InteropServices;

namespace ChainChartGenerated
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Generated from ChainChart diagram")]
    public class Contract : SmartContract
    {
        private static readonly UInt160 Owner = default;

        // Storage Variables
        private static StorageMap counterMap => new StorageMap(Storage.CurrentContext, "counter");
        private static BigInteger counter
        {
            get
            {
                var value = counterMap.Get(ByteString.Empty);
                return value is null ? 0 : (BigInteger)value;
            }
        }
        private static void SetCounter(BigInteger value)
        {
            counterMap.Put(ByteString.Empty, (ByteString)value);
        }

        // Owner Check Modifier
        private static bool IsOwner()
        {
            return Runtime.CheckWitness(Owner);
        }

        // Events
        public static event Action<string> Log;

        // Functions
        public static void increment()
        {
            // Add your logic here
        }

    }
}