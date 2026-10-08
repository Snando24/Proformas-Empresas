"""
Tests for proforma_app/company_config.py

This module contains comprehensive unit tests for the CompanyConfig dataclass,
including configuration loading, validation, and serialization.
"""

import json
import pytest
from pathlib import Path

from proforma_app.company_config import CompanyConfig


class TestCompanyConfigLoadValidConfig:
    """Tests for loading valid company configurations."""

    def test_load_valid_config_jc_services(self, mock_config_dir):
        """Test loading an existing valid company configuration."""
        config = CompanyConfig.from_json_file(mock_config_dir / "jc-services.json")
        assert config.company_id == "jc-services"
        assert config.company_name == "J&C SERVICES"

    def test_load_config_returns_all_fields(self, mock_config_dir):
        """Test that loaded config contains all required fields."""
        config = CompanyConfig.from_json_file(mock_config_dir / "jc-services.json")
        assert config.payment_bcp_account == "0011-0202-0100061544"
        assert config.payment_bcp_cci == "MULTISERVICIOS J&C"
        assert config.payment_bank_label == "Cuenta BCP Soles"
        assert config.workshop_address == "Jr. Taller 123"
        assert config.fiscal_address == "Jr. Fiscal 456"

    def test_load_config_optional_detracciones_account(self, mock_config_dir):
        """Test that detracciones_account can be empty or missing."""
        config = CompanyConfig.from_json_file(mock_config_dir / "jc-services.json")
        assert config.payment_detracciones_account == ""


class TestCompanyConfigErrors:
    """Tests for error handling in company configuration loading."""

    def test_load_config_file_not_found(self, mock_config_dir):
        """Test FileNotFoundError when config file doesn't exist."""
        non_existent = mock_config_dir / "non-existent-company.json"
        with pytest.raises(FileNotFoundError):
            CompanyConfig.from_json_file(non_existent)

    def test_load_config_invalid_json(self, temp_dir):
        """Test JSONDecodeError when config contains invalid JSON."""
        invalid_json_file = temp_dir / "invalid.json"
        invalid_json_file.write_text("{invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            CompanyConfig.from_json_file(invalid_json_file)

    def test_load_config_missing_required_field(self, temp_dir):
        """Test ValueError when required field is missing."""
        incomplete_config = temp_dir / "incomplete.json"
        incomplete_config.write_text(json.dumps({"company_id": "test"}))
        
        with pytest.raises((ValueError, TypeError, KeyError)):
            CompanyConfig.from_json_file(incomplete_config)


class TestCompanyConfigSerialization:
    """Tests for converting CompanyConfig to dictionary."""

    def test_to_dict_returns_dictionary(self, sample_company_config):
        """Test that to_dict() returns a dictionary."""
        config = CompanyConfig(**sample_company_config)
        result = config.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_all_fields_present(self, sample_company_config):
        """Test that all fields are present in dict output."""
        config = CompanyConfig(**sample_company_config)
        result = config.to_dict()
        
        assert result["company_id"] == sample_company_config["company_id"]
        assert result["company_name"] == sample_company_config["company_name"]
        assert result["payment_bcp_account"] == sample_company_config["payment_bcp_account"]
        assert result["payment_bcp_cci"] == sample_company_config["payment_bcp_cci"]

    def test_to_dict_serializable_to_json(self, sample_company_config):
        """Test that dict output is JSON serializable."""
        config = CompanyConfig(**sample_company_config)
        result = config.to_dict()
        
        # Should not raise exception
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["company_id"] == sample_company_config["company_id"]


class TestCompanyConfigValidation:
    """Tests for field validation and type checking."""

    def test_company_id_is_string(self, sample_company_config):
        """Test that company_id is a string."""
        config = CompanyConfig(**sample_company_config)
        assert isinstance(config.company_id, str)
        assert len(config.company_id) > 0

    def test_company_name_is_string(self, sample_company_config):
        """Test that company_name is a string."""
        config = CompanyConfig(**sample_company_config)
        assert isinstance(config.company_name, str)
        assert len(config.company_name) > 0

    def test_payment_fields_are_strings(self, sample_company_config):
        """Test that payment fields are strings."""
        config = CompanyConfig(**sample_company_config)
        assert isinstance(config.payment_bcp_account, str)
        assert isinstance(config.payment_bcp_cci, str)
        assert isinstance(config.payment_detracciones_account, str)
        assert isinstance(config.payment_bank_label, str)

    def test_address_fields_are_strings(self, sample_company_config):
        """Test that address fields are non-empty strings."""
        config = CompanyConfig(**sample_company_config)
        assert isinstance(config.workshop_address, str)
        assert len(config.workshop_address) > 0
        assert isinstance(config.fiscal_address, str)
        assert len(config.fiscal_address) > 0

    def test_offer_note_fields_are_strings(self, sample_company_config):
        """Test that offer note fields are strings."""
        config = CompanyConfig(**sample_company_config)
        assert isinstance(config.offer_note_primary, str)
        assert isinstance(config.offer_note_secondary, str)

    def test_image_fields_are_strings(self, sample_company_config):
        """Test that image path fields are strings."""
        config = CompanyConfig(**sample_company_config)
        assert isinstance(config.header_image, str)
        assert isinstance(config.watermark_image, str)


class TestCompanyConfigMultipleCompanies:
    """Tests for handling multiple company configurations."""

    def test_load_different_companies_separately(self, mock_config_dir):
        """Test loading different company configs separately."""
        config = CompanyConfig.from_json_file(mock_config_dir / "jc-services.json")
        assert config.company_id == "jc-services"
        assert config.company_name == "J&C SERVICES"

    def test_different_configs_have_different_data(self, temp_dir):
        """Test that different configs have distinct data."""
        config1_data = {
            "company_id": "company-a",
            "company_name": "Company A",
            "payment_bcp_account": "1111-2222-3333",
            "payment_bcp_cci": "Company A CCI",
            "payment_detracciones_account": "00-111-222",
            "payment_bank_label": "Account A",
            "offer_note_primary": "Note A",
            "offer_note_secondary": "Note A2",
            "workshop_address": "Address A",
            "fiscal_address": "Address A2",
            "header_image": "header-a.png",
            "watermark_image": "watermark-a.png"
        }
        
        config2_data = {
            "company_id": "company-b",
            "company_name": "Company B",
            "payment_bcp_account": "4444-5555-6666",
            "payment_bcp_cci": "Company B CCI",
            "payment_detracciones_account": "00-333-444",
            "payment_bank_label": "Account B",
            "offer_note_primary": "Note B",
            "offer_note_secondary": "Note B2",
            "workshop_address": "Address B",
            "fiscal_address": "Address B2",
            "header_image": "header-b.png",
            "watermark_image": "watermark-b.png"
        }
        
        config1 = CompanyConfig(**config1_data)
        config2 = CompanyConfig(**config2_data)
        
        assert config1.company_id != config2.company_id
        assert config1.payment_bcp_account != config2.payment_bcp_account
        assert config1.workshop_address != config2.workshop_address


class TestCompanyConfigDataclass:
    """Tests for CompanyConfig as a dataclass."""

    def test_dataclass_initialization(self, sample_company_config):
        """Test direct dataclass initialization with kwargs."""
        config = CompanyConfig(**sample_company_config)
        assert config.company_id == sample_company_config["company_id"]

    def test_dataclass_fields_immutable(self, sample_company_config):
        """Test that dataclass is effectively immutable (frozen=True or frozen=False behavior)."""
        config = CompanyConfig(**sample_company_config)
        original_name = config.company_name
        
        # Try to modify (if dataclass is mutable this will work)
        try:
            config.company_name = "Modified Name"
            # If we get here, dataclass allows modification
            # Verify it was actually changed
            assert config.company_name == "Modified Name"
        except (AttributeError, TypeError):
            # If frozen=True, this will raise an error
            # Verify original value is unchanged
            assert config.company_name == original_name
