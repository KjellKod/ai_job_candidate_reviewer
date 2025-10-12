"""OpenAI API connection testing and model selection."""

import time
from typing import List, Optional

import openai
from openai import OpenAI

from models import ConnectionResult


class OpenAIConnectionTester:
    """OpenAI API connection testing and model selection."""

    def __init__(self, api_key: str, preferred_model: Optional[str] = None):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            preferred_model: Preferred model to use (will fall back if not available)
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

        # Model priority list - Prefer GPT-5, then GPT-4 variants that are allowed for this project
        # Note: We intentionally exclude GPT-4o family if the project does not have access
        model_priority = [
            "gpt-5",  # GPT-5 base
            "gpt-5-2025",  # Any dated GPT-5 release
            "gpt-5-mini",  # Faster GPT-5
            "gpt-5-nano",  # Efficient GPT-5
            "gpt-4-turbo",  # GPT-4 turbo variants
            "gpt-4",  # Classic GPT-4
        ]

        if preferred_model:
            model_priority.insert(0, preferred_model)

        # Use model selection with fallback limited to accessible models
        self.model = self._select_best_available_model(model_priority)

    def _select_best_available_model(self, model_priority: List[str]) -> Optional[str]:
        """Select the best available model from priority list.

        Args:
            model_priority: List of models in priority order

        Returns:
            Name of the best available model, or None if none are accessible
        """
        available_models = self.get_available_models()

        # Helper to iterate over available ids matching a prefix or exact id
        def candidates_for(preferred: str) -> List[str]:
            return [
                m for m in available_models if m == preferred or m.startswith(preferred)
            ]

        # Try preferred model first if provided
        if model_priority and len(model_priority) > 0:
            pass  # kept for readability

        # Try each priority prefix against available model ids
        for pref in model_priority:
            for candidate in candidates_for(pref):
                if self._test_model_availability(candidate):
                    return candidate

        # As a last attempt, try any available GPT-5/4 model ids
        for candidate in available_models:
            if candidate.startswith(("gpt-5", "gpt-4")):
                if self._test_model_availability(candidate):
                    return candidate

        # No accessible model found
        return None

    def _test_model_availability(self, model: str) -> bool:
        """Test if a model is available for use.

        Args:
            model: Model name to test

        Returns:
            True if model is available, False otherwise
        """
        try:
            # Make a minimal test call with proper parameters for each model
            request_params = {
                "model": model,
                "messages": [{"role": "user", "content": "test"}],
                "temperature": 0,
            }

            # GPT-5 models use max_completion_tokens instead of max_tokens
            if model.startswith("gpt-5"):
                request_params["max_completion_tokens"] = 1
            else:
                request_params["max_tokens"] = 1

            self.client.chat.completions.create(**request_params)
            return True
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available models for this API key.

        Returns:
            List of available model names
        """
        try:
            models = self.client.models.list()
            ids = [model.id for model in models.data if "gpt" in model.id.lower()]
            # Prefer only GPT-5 and GPT-4 families, exclude GPT-4o family unless explicitly allowed
            filtered = [m for m in ids if m.startswith(("gpt-5", "gpt-4"))]
            return filtered or ids
        except Exception:
            return []

    def test_connection(self) -> ConnectionResult:
        """Test API connectivity with minimal request.

        Returns:
            ConnectionResult with success status and details
        """
        start_time = time.time()

        try:
            # Validate model selection
            if not self.model:
                available_models = self.get_available_models()
                return ConnectionResult(
                    success=False,
                    message=(
                        "No accessible GPT-5/GPT-4 model found for this project. "
                        f"Available models detected: {', '.join(available_models) if available_models else 'none'}. "
                        "Please enable a GPT-5 or GPT-4 chat.completions model for this project."
                    ),
                )

            # Build request
            request_params = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, please respond with 'Connection successful'",
                    }
                ],
                "temperature": 0,
            }

            # GPT-5 models use max_completion_tokens instead of max_tokens
            if self.model.startswith("gpt-5"):
                request_params["max_completion_tokens"] = 10
            else:
                request_params["max_tokens"] = 10

            # Call API
            response = self.client.chat.completions.create(**request_params)
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            # Validate response
            if response.choices and response.choices[0].message.content:
                available_models = self.get_available_models()
                model_info = f"Using: {self.model}"
                if len(available_models) > 0:
                    model_info += f" (Available GPT models: {len(available_models)})"
                return ConnectionResult(
                    success=True,
                    message="API connection successful",
                    response_time_ms=response_time_ms,
                    model_info=model_info,
                )

            return ConnectionResult(
                success=False, message="API responded but with empty content"
            )

        except openai.AuthenticationError:
            return ConnectionResult(
                success=False,
                message="Authentication failed. Please check your API key.",
            )
        except openai.RateLimitError:
            return ConnectionResult(
                success=False, message="Rate limit exceeded. Please try again later."
            )
        except openai.APIConnectionError:
            return ConnectionResult(
                success=False,
                message="Failed to connect to OpenAI API. Check your internet connection.",
            )
        except Exception as e:
            return ConnectionResult(
                success=False, message=f"Unexpected error: {str(e)}"
            )


def main():
    """Main function for standalone execution."""
    import os

    from dotenv import load_dotenv

    print("🔧 OpenAI API Connection Tester")
    print("=" * 40)

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("Please set your OpenAI API key in a .env file:")
        print("OPENAI_API_KEY=your_key_here")
        return

    # Test connection
    tester = OpenAIConnectionTester(api_key)

    print(f"🔄 Testing connection with model: {tester.model or 'None'}")
    result = tester.test_connection()

    if result.success:
        print(f"✅ {result.message}")
        if result.model_info:
            print(f"   {result.model_info}")
        if result.response_time_ms:
            print(f"   Response time: {result.response_time_ms:.0f}ms")

        # Show available models
        print("\n📋 Available GPT Models:")
        models = tester.get_available_models()
        if models:
            for i, model in enumerate(sorted(models)[:10], 1):  # Show first 10
                current = " (CURRENT)" if model == tester.model else ""
                print(f"   {i:2d}. {model}{current}")
            if len(models) > 10:
                print(f"   ... and {len(models) - 10} more models")
        else:
            print("   Could not fetch model list")
    else:
        print(f"❌ {result.message}")
        return

    print("\n🎉 Connection test completed successfully!")


if __name__ == "__main__":
    main()
