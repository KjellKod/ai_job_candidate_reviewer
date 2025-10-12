#!/usr/bin/env python3
"""Monitor GPT-5 availability and test when ready."""

import time

from config import Config
from open_api_test_connection import OpenAIConnectionTester


def monitor_gpt5_access():
    """Monitor GPT-5 access until available."""

    config = Config()

    print("🔍 Monitoring GPT-5 access...")
    print("Will check every 30 seconds until GPT-5 is available")
    print("Press Ctrl+C to stop monitoring\n")

    attempt = 1

    while True:
        try:
            print(f"📡 Attempt {attempt}: Testing GPT-5 access...")

            # Test connection with GPT-5 preferred
            tester = OpenAIConnectionTester(config.openai_api_key, "gpt-5")
            result = tester.test_connection()

            if result.success and tester.model.startswith("gpt-5"):
                print(f"🎉 SUCCESS! GPT-5 is now available!")
                print(f"   Using model: {tester.model}")
                print(f"   Response time: {result.response_time_ms:.0f}ms")
                print(f"\n✅ Your system will now automatically use GPT-5!")
                break
            else:
                current_model = tester.model
                print(f"⏳ Still waiting... Currently using: {current_model}")

                if not result.success:
                    print(f"   Error: {result.message}")

            print(f"   Next check in 30 seconds...\n")
            time.sleep(30)
            attempt += 1

        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"❌ Error during monitoring: {e}")
            time.sleep(30)


if __name__ == "__main__":
    monitor_gpt5_access()
