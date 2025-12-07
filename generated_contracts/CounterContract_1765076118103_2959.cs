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
[ManifestExtra("Description", "A simple counter contract generated from ChainChart")]
public class CounterContract_1765076118103_2959 : SmartContract
{
    private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "counter");

    public static BigInteger counter
    {
        get
        {
            ByteString value = CounterMap.Get("counter");
            return value is null ? 0 : (BigInteger)value;
        }
    }

    public static void increment()
    {
        ByteString value = CounterMap.Get("counter");
        BigInteger current = value is null ? 0 : (BigInteger)value;
        BigInteger updated = current + 1;
        CounterMap.Put("counter", updated);
    }
}
}