using Neo.SmartContract.Framework.Attributes;
using Neo;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;

namespace ChainChartGenerated
{
    [ManifestExtra("Author", "SpoonAI")]
    [ManifestExtra("Email", "")]
    [ManifestExtra("Description", "A simple counter contract generated from ChainChart diagram.")]
    public class CounterContract_1765103709429_4640 : SmartContract
    {
        private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "counter");

        public static void increment()
        {
            ByteString value = CounterMap.Get(ByteString.Empty);
            BigInteger counter = value is null ? 0 : (BigInteger)value;
            counter = counter + 1;
            CounterMap.Put(ByteString.Empty, counter);
        }
    }
}