"""Tests for credential management."""

from unittest.mock import patch

import keyring.errors
import pytest

from tradedata.application.credentials import (
    CredentialsNotFoundError,
    delete_credentials,
    get_credentials,
    store_credentials,
)


class TestGetCredentials:
    """Tests for get_credentials function."""

    @patch("tradedata.application.credentials.keyring.get_password")
    def test_get_credentials_success(self, mock_get_password):
        """Test successful credential retrieval."""
        # Setup
        mock_get_password.side_effect = ["user@example.com", "secure_password"]

        # Execute
        email, password = get_credentials("robinhood")

        # Assert
        assert email == "user@example.com"
        assert password == "secure_password"
        assert mock_get_password.call_count == 2
        mock_get_password.assert_any_call("com.tradedata.robinhood", "robinhood_email")
        mock_get_password.assert_any_call("com.tradedata.robinhood", "robinhood_password")

    @patch("tradedata.application.credentials.keyring.get_password")
    def test_get_credentials_not_found_missing_email(self, mock_get_password):
        """Test error when email is not found."""
        # Setup
        mock_get_password.side_effect = [None, "password"]

        # Execute & Assert
        with pytest.raises(CredentialsNotFoundError) as exc_info:
            get_credentials("robinhood")

        assert "not found in keyring" in str(exc_info.value)
        assert "robinhood" in str(exc_info.value)

    @patch("tradedata.application.credentials.keyring.get_password")
    def test_get_credentials_not_found_missing_password(self, mock_get_password):
        """Test error when password is not found."""
        # Setup
        mock_get_password.side_effect = ["user@example.com", None]

        # Execute & Assert
        with pytest.raises(CredentialsNotFoundError) as exc_info:
            get_credentials("robinhood")

        assert "not found in keyring" in str(exc_info.value)

    @patch("tradedata.application.credentials.keyring.get_password")
    def test_get_credentials_different_source(self, mock_get_password):
        """Test credentials retrieval for different source."""
        # Setup
        mock_get_password.side_effect = ["ibkr@example.com", "ibkr_password"]

        # Execute
        email, password = get_credentials("ibkr")

        # Assert
        assert email == "ibkr@example.com"
        assert password == "ibkr_password"
        mock_get_password.assert_any_call("com.tradedata.ibkr", "ibkr_email")
        mock_get_password.assert_any_call("com.tradedata.ibkr", "ibkr_password")


class TestStoreCredentials:
    """Tests for store_credentials function."""

    @patch("tradedata.application.credentials.keyring.set_password")
    def test_store_credentials_success(self, mock_set_password):
        """Test successful credential storage."""
        # Execute
        store_credentials("robinhood", "user@example.com", "secure_password")

        # Assert
        assert mock_set_password.call_count == 2
        mock_set_password.assert_any_call(
            "com.tradedata.robinhood", "robinhood_email", "user@example.com"
        )
        mock_set_password.assert_any_call(
            "com.tradedata.robinhood", "robinhood_password", "secure_password"
        )

    @patch("tradedata.application.credentials.keyring.set_password")
    def test_store_credentials_empty_email(self, mock_set_password):
        """Test error when email is empty."""
        # Execute & Assert
        with pytest.raises(ValueError) as exc_info:
            store_credentials("robinhood", "", "password")

        assert "must not be empty" in str(exc_info.value)
        mock_set_password.assert_not_called()

    @patch("tradedata.application.credentials.keyring.set_password")
    def test_store_credentials_empty_password(self, mock_set_password):
        """Test error when password is empty."""
        # Execute & Assert
        with pytest.raises(ValueError) as exc_info:
            store_credentials("robinhood", "user@example.com", "")

        assert "must not be empty" in str(exc_info.value)
        mock_set_password.assert_not_called()

    @patch("tradedata.application.credentials.keyring.set_password")
    def test_store_credentials_different_source(self, mock_set_password):
        """Test credential storage for different source."""
        # Execute
        store_credentials("ibkr", "ibkr@example.com", "ibkr_pass")

        # Assert
        mock_set_password.assert_any_call("com.tradedata.ibkr", "ibkr_email", "ibkr@example.com")
        mock_set_password.assert_any_call("com.tradedata.ibkr", "ibkr_password", "ibkr_pass")


class TestDeleteCredentials:
    """Tests for delete_credentials function."""

    @patch("tradedata.application.credentials.keyring.delete_password")
    def test_delete_credentials_success(self, mock_delete_password):
        """Test successful credential deletion."""
        # Execute
        delete_credentials("robinhood")

        # Assert
        assert mock_delete_password.call_count == 2
        mock_delete_password.assert_any_call("com.tradedata.robinhood", "robinhood_email")
        mock_delete_password.assert_any_call("com.tradedata.robinhood", "robinhood_password")

    @patch("tradedata.application.credentials.keyring.delete_password")
    def test_delete_credentials_not_found(self, mock_delete_password):
        """Test deletion when credentials don't exist (should not raise error)."""
        # Setup - simulate credentials not found
        mock_delete_password.side_effect = keyring.errors.PasswordDeleteError("Not found")

        # Execute - should not raise error
        delete_credentials("robinhood")

        # Assert
        assert mock_delete_password.call_count == 2

    @patch("tradedata.application.credentials.keyring.delete_password")
    def test_delete_credentials_partial_exists(self, mock_delete_password):
        """Test deletion when only one credential exists."""
        # Setup - first deletion succeeds, second raises error
        mock_delete_password.side_effect = [
            None,  # Email deletion succeeds
            keyring.errors.PasswordDeleteError("Not found"),  # Password not found
        ]

        # Execute - should not raise error
        delete_credentials("robinhood")

        # Assert
        assert mock_delete_password.call_count == 2

    @patch("tradedata.application.credentials.keyring.delete_password")
    def test_delete_credentials_different_source(self, mock_delete_password):
        """Test credential deletion for different source."""
        # Execute
        delete_credentials("ibkr")

        # Assert
        mock_delete_password.assert_any_call("com.tradedata.ibkr", "ibkr_email")
        mock_delete_password.assert_any_call("com.tradedata.ibkr", "ibkr_password")
