import os
import re
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent

from qdrant_client import QdrantClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).resolve().parent.parent / 'config/logs/config.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def safe_env_var(key: str, default: str = None) -> str:
    """Safely get environment variable with robust error handling"""
    try:
        value = os.getenv(key, default)
        if value is None:
            logger.warning(f"Environment variable {key} not found, using default: {default}")
            return default
        # Remove quotes and extra whitespace
        cleaned_value = value.strip().strip('"').strip("'").strip('\r').strip('\n')
        return cleaned_value
    except Exception as e:
        logger.warning(f"Error reading environment variable {key}: {e}, using default: {default}")
        return default

try:
    # Check if we're in production (Cloud Run) or development
    is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('K_SERVICE') is not None

    if is_production:
        logger.info("Running in production mode - using environment variables from Cloud Run")
        # In production, don't load .env file, use environment variables directly
    else:
        # Try to load .env file if it exists (for local development)
        env_path = project_root / '.env'
        if env_path.exists():
            logger.info(f"Loading .env file from {env_path}")
            load_dotenv(env_path, override=True)
        else:
            logger.info("No .env file found, using environment variables directly")

    # Required environment variables with defaults for production
    REQUIRED_VARS = [
        'QDRANT_URL_CLOUD',
        'QDRANT_URL_LOCAL',
        'QDRANT_API_KEY',
        'GROQ_API_KEY',
        'GOOGLE_API_KEY',
    ]

    # Load environment variables with safe parsing
    config = {var: safe_env_var(var) for var in REQUIRED_VARS}

    # Log all environment variables for debugging
    logger.info("Environment variables loaded:")
    for var in REQUIRED_VARS:
        value = config[var]
        if value:
            # Mask sensitive values for logging
            if 'API_KEY' in var or 'SECRET' in var:
                masked_value = f"{value[:8]}****{value[-8:]}" if len(value) > 16 else "****"
                logger.info(f"  {var}: {masked_value}")
            else:
                logger.info(f"  {var}: {value}")
        else:
            logger.warning(f"  {var}: NOT FOUND")

    # Check for missing critical variables
    critical_vars = ['QDRANT_URL_CLOUD', 'QDRANT_API_KEY', 'GROQ_API_KEY']
    missing_critical = [var for var in critical_vars if not config[var]]

    if missing_critical:
        logger.error(f"Missing critical environment variables: {', '.join(missing_critical)}")
        # Don't exit in production, just log the error
        if os.getenv('FLASK_ENV') == 'production':
            logger.warning("Running in production mode with missing variables - some features may not work")
        else:
            logger.critical("Missing required environment variables")
            sys.exit(1)

    # Export variables with safe defaults
    QDRANT_URL_CLOUD = config['QDRANT_URL_CLOUD'] or 'https://your-qdrant-url.cloud'
    QDRANT_URL_LOCAL = config['QDRANT_URL_LOCAL'] or 'http://localhost:6333'
    QDRANT_API_KEY = config['QDRANT_API_KEY'] or 'your-qdrant-api-key'
    GROQ_API_KEY = config['GROQ_API_KEY'] or 'your-groq-api-key'
    GOOGLE_API_KEY = config['GOOGLE_API_KEY'] or 'your-google-api-key'

    # Secure logging for sensitive variables
    sensitive_vars = ['QDRANT_URL_CLOUD', 'QDRANT_URL_LOCAL', 'QDRANT_API_KEY',
                      'GROQ_API_KEY', 'GOOGLE_API_KEY']
    for var in REQUIRED_VARS:
        value = locals().get(var, '')
        logged_value = f"{value[:8]}****{value[-8:]}" if var in sensitive_vars and len(value) > 4 else str(value)
        logger.info(f"{var}: {logged_value}")

    logger.info("Configuration loaded successfully")

except Exception as e:
    logger.critical(f"Configuration initialization failed: {str(e)}")
    # Don't exit in production, just log the error
    if os.getenv('FLASK_ENV') != 'production':
        sys.exit(1)

__all__ = REQUIRED_VARS
