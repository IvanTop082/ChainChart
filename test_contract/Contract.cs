using Neo;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Services;
using System;
using System.Numerics;

namespace ChainChartGenerated
{
    [ManifestExtra("Author", "ChainChart")]
    [ManifestExtra("Description", "Generated from ChainChart diagram")]
    public class Contract : SmartContract
    {
        // Example stored value just so there's *something* to test
        private static StorageMap AppStorage => new StorageMap(Storage.CurrentContext, "app");

        // Optional event
        public static event Action<string> Initialized;

        /// <summary>
        /// The constructor-equivalent for Neo smart contracts.
        /// Only runs once at deployment.
        /// </summary>
        public static void _initialize()
        {
            // Set a simple value in storage
            AppStorage.Put("version", 1);

            // Fire event so we can check in Neo explorer
            Initialized("Contract Deployed");
        }

        /// <summary>
        /// Read stored version
        /// </summary>
        /// <returns>Integer version</returns>
        public static BigInteger GetVersion()
        {
            ByteString value = AppStorage.Get("version");
            return value is null ? 0 : (BigInteger)value;
        }

        /// <summary>
        /// Update version — simple test method
        /// </summary>
        public static void SetVersion(BigInteger v)
        {
            if (v < 0) throw new Exception("Version must be positive");
            AppStorage.Put("version", v);
        }
    }
}
