using Neo.SmartContract.Framework.Attributes;
namespace ChainChartGenerated
{
using Neo;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;

[ManifestExtra("Author", "SpoonAI")]
[ManifestExtra("Email", "")]
[ManifestExtra("Description", "A simple counter contract with increment functionality.")]
public class CounterContract_1765069482008_7509 : SmartContract
{
    private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "Counter");

    public static void Increment()
    {
        ByteString value = CounterMap.Get("value");
        BigInteger counter = value is null ? 0 : (BigInteger)value;
        counter = counter + 1;
        CounterMap.Put("value", counter);
    }

    public static BigInteger Counter()
    {
        ByteString value = CounterMap.Get("value");
        return value is null ? 0 : (BigInteger)value;
    }
}
}