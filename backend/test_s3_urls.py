#!/usr/bin/env python3
"""
Test script for S3 URL generation
This script tests the URL generation logic without actually uploading files.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.s3_service import S3Service
from app.core.config import settings


def test_url_generation():
    """Test URL generation with different configurations"""

    # Create S3 service instance (this will try to connect)
    s3_service = S3Service()

    # Test object name similar to your examples
    test_object_name = "user_683db9fcbb6a0efc0b23019d/uploads/0dbb5252-2c34-4170-a633-4e810370c340-20220209125325_LN02%20-%20Logical%20Agent.pdf"

    print("S3 Configuration:")
    print(f"  S3_ENDPOINT_URL: {settings.S3_ENDPOINT_URL}")
    print(f"  S3_BUCKET_NAME: {settings.S3_BUCKET_NAME}")
    print(f"  S3_PUBLIC_DOMAIN: {getattr(settings, 'S3_PUBLIC_DOMAIN', 'Not set')}")
    print()

    print("Generated URL (current config):")
    try:
        url = s3_service.get_public_url(test_object_name)
        print(f"  {url}")

        # Compare with your expected pattern
        if "pub-" in url and ".r2.dev" in url:
            print("✅ URL matches Cloudflare R2 pattern")
        else:
            print("⚠️  URL doesn't match expected Cloudflare R2 pattern")

    except Exception as e:
        print(f"❌ Error generating URL: {e}")

    print()
    print(
        "To get the correct URL format, set the S3_PUBLIC_DOMAIN environment variable:"
    )
    print("Example: S3_PUBLIC_DOMAIN=pub-54da46e8a2604cab93be4f47302d66c5.r2.dev")

    # Simulate what the URL would look like with proper config
    example_domain = "pub-54da46e8a2604cab93be4f47302d66c5.r2.dev"
    example_url = f"https://{example_domain}/{test_object_name}"
    print(f"Expected URL: {example_url}")


if __name__ == "__main__":
    test_url_generation()
