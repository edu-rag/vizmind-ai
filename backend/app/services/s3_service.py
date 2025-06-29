import boto3
from botocore.exceptions import ClientError
import io  # For BytesIO to wrap bytes for upload_fileobj
import asyncio
from typing import Optional

from app.core.config import settings, logger  # Use centralized settings


class S3Service:
    def __init__(self):
        """
        Initializes the S3 client using credentials from settings.
        The client is stored as an instance variable `self.s3_client`.
        """
        self.s3_client: Optional[boto3.client] = None  # Type hint for clarity

        if self._are_creds_fully_configured():
            try:
                self.s3_client = boto3.client(
                    service_name="s3",
                    endpoint_url=settings.S3_ENDPOINT_URL,
                    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                    # region_name=settings.S3_REGION_NAME # Add if using AWS S3 and not relying on endpoint_url for region
                    # config=boto3.session.Config(signature_version='s3v4') # May be needed for some S3 providers
                )
                logger.info(
                    f"S3 client attempting to connect to endpoint: {settings.S3_ENDPOINT_URL}, bucket: {settings.S3_BUCKET_NAME}"
                )

                # Perform a simple check to ensure the client and bucket are accessible
                # This will raise an exception if the bucket doesn't exist or credentials are wrong for it.
                self.s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
                logger.info(
                    f"Successfully connected to S3 and validated bucket: {settings.S3_BUCKET_NAME}"
                )

            except ClientError as e:
                logger.error(
                    f"S3 ClientError during initialization or bucket validation: {e}. S3 operations will likely fail."
                )
                self.s3_client = None  # Ensure client is None if setup fails
            except Exception as e:  # Catch other potential errors like misconfiguration
                logger.error(
                    f"An unexpected error occurred during S3 client initialization: {e}. S3 operations might fail."
                )
                self.s3_client = None
        else:
            logger.warning(
                "S3 credentials (access key, secret key, endpoint URL, or bucket name) are not fully configured in .env. S3 operations will be disabled."
            )

    def _are_creds_fully_configured(self) -> bool:
        """Helper to check if all necessary S3 settings are present."""
        return all(
            [
                settings.S3_ACCESS_KEY_ID,
                settings.S3_SECRET_ACCESS_KEY,
                settings.S3_ENDPOINT_URL,  # Crucial for MinIO or other S3-compatibles
                settings.S3_BUCKET_NAME,
            ]
        )

    def is_configured(self) -> bool:
        """Checks if the S3 client was successfully initialized and configured."""
        return self.s3_client is not None

    async def upload_pdf_bytes_async(
        self, file_bytes: bytes, object_name: str
    ) -> Optional[str]:
        """
        Uploads PDF bytes to the configured S3 bucket asynchronously.

        Args:
            file_bytes: The PDF content as bytes.
            object_name: The desired object name (key) in the S3 bucket (e.g., "uploads/myfile.pdf").

        Returns:
            The public HTTPS URL to access the file if successful, None otherwise.
        """
        if not self.is_configured():
            logger.warning(
                "S3 client not available or not properly configured. Skipping S3 upload."
            )
            return None

        try:
            # upload_fileobj expects a file-like object, so we wrap bytes in BytesIO
            file_like_object = io.BytesIO(file_bytes)

            # The S3 client's upload_fileobj method is blocking, so run it in a separate thread
            # to avoid blocking the asyncio event loop.
            await asyncio.to_thread(
                self.s3_client.upload_fileobj,
                file_like_object,
                settings.S3_BUCKET_NAME,
                object_name,
                # ExtraArgs={'ACL': 'private'} # Or 'public-read' if needed
            )

            s3_path = self._generate_public_url(object_name)
            logger.info(f"File uploaded successfully to S3, public URL: {s3_path}")
            return s3_path
        except ClientError as e:
            logger.error(f"S3 Upload ClientError for object '{object_name}': {e}")
            return None
        except Exception as e:  # Catch any other unexpected errors during upload
            logger.error(
                f"An unexpected error occurred during S3 upload for object '{object_name}': {e}",
                exc_info=True,
            )
            return None

    def _generate_public_url(self, object_name: str) -> str:
        """
        Generates a public URL for the given object name.
        This handles different S3-compatible services including Cloudflare R2.

        Args:
            object_name: The object key in the S3 bucket

        Returns:
            Public HTTPS URL to access the file
        """
        # Check if we have a custom public domain configured (recommended)
        if hasattr(settings, "S3_PUBLIC_DOMAIN") and settings.S3_PUBLIC_DOMAIN:
            public_domain = (
                settings.S3_PUBLIC_DOMAIN.replace("https://", "")
                .replace("http://", "")
                .rstrip("/")
            )
            return f"https://{public_domain}/{object_name}"

        # If endpoint URL is provided and doesn't look like standard AWS S3
        if settings.S3_ENDPOINT_URL and not settings.S3_ENDPOINT_URL.endswith(
            "amazonaws.com"
        ):
            # Remove the protocol and any trailing slashes from endpoint URL
            base_url = (
                settings.S3_ENDPOINT_URL.replace("https://", "")
                .replace("http://", "")
                .rstrip("/")
            )

            # If it's a Cloudflare R2 URL pattern, extract the domain
            if ".r2.cloudflarestorage.com" in base_url:
                # For Cloudflare R2, we need the actual public domain which is different from the API endpoint
                # The public domain format is typically: pub-{hash}.r2.dev
                # Since we can't determine this automatically, log a warning and use a fallback
                logger.warning(
                    "Cloudflare R2 detected but S3_PUBLIC_DOMAIN not configured. "
                    "Please set S3_PUBLIC_DOMAIN in your environment to the actual public domain "
                    "(e.g., 'pub-12345.r2.dev') for correct URL generation."
                )
                # Extract account ID as fallback (may not work for actual file access)
                account_id = base_url.split(".")[0]
                return f"https://{account_id}.r2.dev/{object_name}"
            else:
                # For other S3-compatible services, try direct public access
                return f"https://{base_url}/{object_name}"
        else:
            # Standard AWS S3 public URL format
            region = getattr(settings, "S3_REGION_NAME", "us-east-1")
            return f"https://{settings.S3_BUCKET_NAME}.s3.{region}.amazonaws.com/{object_name}"

    def get_public_url(self, object_name: str) -> str:
        """
        Public method to get the public URL for an object without uploading.
        Useful for testing or getting URLs for existing objects.

        Args:
            object_name: The object key in the S3 bucket

        Returns:
            Public HTTPS URL to access the file
        """
        return self._generate_public_url(object_name)
