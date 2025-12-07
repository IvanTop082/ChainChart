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
        private static StorageMap CounterMap => new StorageMap(Storage.CurrentContext, "Counter");
        public static void Increment()
        {
            // TODO: Implement function logic
        }

    }
}