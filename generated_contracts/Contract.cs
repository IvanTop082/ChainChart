using System.Numerics;
using Neo;
using Neo.SmartContract;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System;

namespace ChainChartContract
{    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Generated from ChainChart diagram")]
    public class ChainChartContract : SmartContract
    {
        private static StorageMap NewstateMap => new StorageMap(Storage.CurrentContext, "New state");        public static event Action<> Newevent;        public static event Action<> Newevent;

        public static void Newfunction()
        {
            // TODO: Implement function logic
        }

    }
}