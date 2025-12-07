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
[ManifestExtra("Description", "A simple counter contract with increment functionality.")]
public class CounterContract_1765071502790_7361 : SmartContract
{
    private static readonly StorageMap CounterMap = new(Storage.CurrentContext, "Counter");
    private static readonly StorageMap NewStateMap = new(Storage.CurrentContext, "New state");

    public static BigInteger Counter
    {
        get
        {
            ByteString value = CounterMap.Get("Counter");
            return value is null ? 0 : (BigInteger)value;
        }
    }

    public static BigInteger NewState
    {
        get
        {
            ByteString value = NewStateMap.Get("New state");
            return value is null ? 0 : (BigInteger)value;
        }
    }

    public static void Increment()
    {
        ByteString counterValue = CounterMap.Get("Counter");
        BigInteger counter = counterValue is null ? 0 : (BigInteger)counterValue;
        counter = counter + 1;
        CounterMap.Put("Counter", counter);
    }
}
}