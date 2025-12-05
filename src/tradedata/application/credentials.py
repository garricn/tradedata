"""Credential management using system keyring.

Provides secure storage and retrieval of broker credentials using the system's
native credential storage (macOS Keychain, Windows Credential Manager, Linux
Secret Service).

Following the pattern from perfina project for consistent credential management.
"""

from typing import Optional, Tuple

import keyring


class CredentialsNotFoundError(Exception):
    """Raised when credentials are not found in the keyring."""

    pass


def _get_service_name(source: str) -> str:
    """Get keyring service name for a data source.

    Args:
        source: Data source name (e.g., 'robinhood', 'ibkr')

    Returns:
        Service name for keyring (e.g., 'com.tradedata.robinhood')
    """
    return f"com.tradedata.{source}"


def get_credentials(source: str = "robinhood") -> Tuple[str, str]:
    """Retrieve credentials from system keyring.

    Args:
        source: Data source name (default: 'robinhood')

    Returns:
        Tuple of (email, password)

    Raises:
        CredentialsNotFoundError: If credentials not found in keyring

    Example:
        >>> email, password = get_credentials("robinhood")
        >>> print(f"Email: {email}")
    """
    service_name = _get_service_name(source)

    email = keyring.get_password(service_name, f"{source}_email")
    password = keyring.get_password(service_name, f"{source}_password")

    if not email or not password:
        raise CredentialsNotFoundError(
            f"Credentials for '{source}' not found in keyring. "
            f"Please store credentials first using store_credentials()"
        )

    return email, password


def store_credentials(source: str, email: str, password: str) -> None:
    """Store credentials in system keyring.

    Args:
        source: Data source name (e.g., 'robinhood', 'ibkr')
        email: User email address
        password: User password

    Raises:
        ValueError: If email or password is empty

    Example:
        >>> store_credentials("robinhood", "user@example.com", "secure_password")
    """
    if not email or not password:
        raise ValueError("Email and password must not be empty")

    service_name = _get_service_name(source)

    keyring.set_password(service_name, f"{source}_email", email)
    keyring.set_password(service_name, f"{source}_password", password)


def delete_credentials(source: str) -> None:
    """Remove credentials from system keyring.

    Args:
        source: Data source name (e.g., 'robinhood', 'ibkr')

    Note:
        Does not raise an error if credentials don't exist.

    Example:
        >>> delete_credentials("robinhood")
    """
    service_name = _get_service_name(source)

    try:
        keyring.delete_password(service_name, f"{source}_email")
    except keyring.errors.PasswordDeleteError:
        # Credential didn't exist, that's fine
        pass

    try:
        keyring.delete_password(service_name, f"{source}_password")
    except keyring.errors.PasswordDeleteError:
        # Credential didn't exist, that's fine
        pass

    try:
        keyring.delete_password(service_name, f"{source}_password")
    except keyring.errors.PasswordDeleteError:
        # Credential didn't exist, that's fine
        pass


def resolve_credentials(
    source: str = "robinhood",
    email: Optional[str] = None,
    password: Optional[str] = None,
    force: bool = False,
) -> Tuple[str, str]:
    """Resolve credentials from provided values or keyring.

    Resolution order:
    1. If both email and password are provided, use them.
    2. If not force and any value is missing, attempt keyring lookup.
    3. If still missing, raise CredentialsNotFoundError.

    Args:
        source: Data source name.
        email: Optional email override.
        password: Optional password override.
        force: If True, skip keyring lookup and require provided values.

    Returns:
        Tuple of (email, password).

    Raises:
        CredentialsNotFoundError: If credentials are not provided or stored.
    """
    email_value = email
    password_value = password

    if not force and (email_value is None or password_value is None):
        try:
            stored_email, stored_password = get_credentials(source)
            email_value = email_value or stored_email
            password_value = password_value or stored_password
        except CredentialsNotFoundError:
            # No stored credentials; fall through to validation
            pass

    if email_value is None or password_value is None:
        raise CredentialsNotFoundError(
            f"Credentials for '{source}' not found in keyring and not provided."
        )

    return email_value, password_value
