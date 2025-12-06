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
        private static StorageMap NewstateMap => new StorageMap(Storage.CurrentContext, "New state");
        private static BigInteger Newstate
        {
            get
            {
                var value = NewstateMap.Get(ByteString.Empty);
                return value is null ? 0 : (BigInteger)value;
            }
        }
        private static void SetNewstate(BigInteger value)
        {
            NewstateMap.Put(ByteString.Empty, (ByteString)value);
        }

        private static StorageMap Newstate_node_1764998304967_266Map => new StorageMap(Storage.CurrentContext, "New state");
        private static BigInteger Newstate_node_1764998304967_266
        {
            get
            {
                var value = Newstate_node_1764998304967_266Map.Get(ByteString.Empty);
                return value is null ? 0 : (BigInteger)value;
            }
        }
        private static void SetNewstate_node_1764998304967_266(BigInteger value)
        {
            Newstate_node_1764998304967_266Map.Put(ByteString.Empty, (ByteString)value);
        }

        // Owner Check Modifier
        private static bool IsOwner()
        {
            return Runtime.CheckWitness(Owner);
        }

        // Events
        public static event Action<string> Log;

        // Functions
        public static void _initialize()
        {
            // Contract initialization
        }

    }
}