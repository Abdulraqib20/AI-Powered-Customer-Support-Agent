import logging
import logging.config
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Setup comprehensive logging configuration"""

    # Create logs directory
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # 🔧 CRITICAL FIX: Clear existing handlers to prevent duplicate logs
    for logger_name in ['customer_support_app', 'api_usage', 'app_errors', 'werkzeug', 'flask.app']:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()  # Clear existing handlers

    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(asctime)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'api': {
                'format': '%(asctime)s - API - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'app_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': str(log_dir / 'app.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'api_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'api',
                'filename': str(log_dir / 'api_usage.log'),
                'maxBytes': 5242880,  # 5MB
                'backupCount': 3,
                'encoding': 'utf8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': str(log_dir / 'errors.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'config_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': str(log_dir / 'config.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            'customer_support_app': {
                'level': 'INFO',
                'handlers': ['console', 'app_file', 'config_file'],
                'propagate': False
            },
            'api_usage': {
                'level': 'INFO',
                'handlers': ['console', 'api_file', 'config_file'],
                'propagate': False
            },
            'app_errors': {
                'level': 'ERROR',
                'handlers': ['console', 'error_file', 'config_file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'config_file']
        }
    }

    # Apply configuration
    logging.config.dictConfig(config)

    # Get loggers
    app_logger = logging.getLogger('customer_support_app')
    api_logger = logging.getLogger('api_usage')
    error_logger = logging.getLogger('app_errors')

    # Log startup
    app_logger.info("=" * 80)
    app_logger.info(f"🚀 Customer Support Application Started - {datetime.now()}")
    app_logger.info("=" * 80)

    return app_logger, api_logger, error_logger

def get_loggers():
    """Get existing loggers (call after setup_logging)"""
    return (
        logging.getLogger('customer_support_app'),
        logging.getLogger('api_usage'),
        logging.getLogger('app_errors')
    )
