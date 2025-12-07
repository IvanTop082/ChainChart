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
[ManifestExtra("Description", "A simple counter contract generated from ChainChart diagram.")]
public class CounterContract_1765059296775_4118 : SmartContract
{
    private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "Counter");

    public static BigInteger Counter
    {
        get
        {
            ByteString value = CounterMap.Get("counter");
            return value is null ? 0 : (BigInteger)value;
        }
    }

    public static void Increment()
    {
        BigInteger current = Counter;
        BigInteger updated = current + 1;
        CounterMap.Put("counter", updated);
    }
}
}