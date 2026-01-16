"""
Custom exceptions for production error handling.

These exceptions replace silent fallbacks and ensure proper error propagation
throughout the application. Each exception maps to a specific HTTP status code
via FastAPI exception handlers in main.py.
"""


class DatabaseUnavailableError(Exception):
    """
    Raised when the database connection is not available.

    HTTP Status: 503 Service Unavailable

    This replaces silent fallbacks to YAML/file-based data.
    The application should fail fast rather than serve stale data.
    """
    pass


class DataNotFoundError(Exception):
    """
    Raised when required data is not found in the database.

    HTTP Status: 404 Not Found

    This indicates the database is connected but the required
    data (protocol rules, benchmarks, study data) is missing.
    """
    pass


class DatabaseQueryError(Exception):
    """
    Raised when a database query fails unexpectedly.

    HTTP Status: 500 Internal Server Error

    This indicates a SQL error or data integrity issue.
    """
    pass


class LLMServiceError(Exception):
    """
    Raised when LLM service fails and cannot generate a response.

    HTTP Status: 503 Service Unavailable

    This replaces:
    - Hardcoded "[AI-generated narrative unavailable]" messages
    - Pattern matching fallbacks for risk factor extraction
    """
    pass


class StudyDataLoadError(Exception):
    """
    Raised when study data cannot be loaded from the database.

    HTTP Status: 503 Service Unavailable

    This replaces fallback to synthetic Excel data.
    """
    pass


class ConfigurationError(Exception):
    """
    Raised when required configuration is missing.

    HTTP Status: 500 Internal Server Error

    This indicates missing environment variables or invalid settings.
    """
    pass
