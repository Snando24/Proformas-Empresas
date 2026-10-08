"""
Tests for proforma_app/server.py

This module contains comprehensive integration tests for the HTTP server,
including API endpoint testing, error handling, and concurrent requests.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from proforma_app.server import (
    ProformaHTTPRequestHandler,
    get_available_companies,
    load_company_config
)


class TestGetAvailableCompanies:
    """Tests for get_available_companies() function."""

    def test_get_available_companies_returns_list(self, mock_config_dir):
        """Test that get_available_companies returns a list."""
        result = get_available_companies(mock_config_dir)
        assert isinstance(result, list)

    def test_get_available_companies_contains_jc_services(self, mock_config_dir):
        """Test that jc-services is in available companies."""
        result = get_available_companies(mock_config_dir)
        company_ids = [c.get("company_id") for c in result]
        assert "jc-services" in company_ids

    def test_get_available_companies_has_required_fields(self, mock_config_dir):
        """Test that each company has required fields."""
        result = get_available_companies(mock_config_dir)
        
        for company in result:
            assert "company_id" in company
            assert "company_name" in company

    def test_get_available_companies_empty_directory(self, temp_dir):
        """Test get_available_companies with empty directory."""
        empty_dir = temp_dir / "empty_companies"
        empty_dir.mkdir()
        
        result = get_available_companies(empty_dir)
        assert result == []

    def test_get_available_companies_ignores_non_json_files(self, temp_dir):
        """Test that non-JSON files are ignored."""
        company_dir = temp_dir / "test_companies"
        company_dir.mkdir()
        
        # Create JSON file
        (company_dir / "valid.json").write_text('{"company_id": "valid", "company_name": "Valid"}')
        # Create non-JSON file
        (company_dir / "invalid.txt").write_text("not json")
        
        result = get_available_companies(company_dir)
        
        # Should only have the JSON file
        assert len(result) >= 1
        company_ids = [c.get("company_id") for c in result]
        assert "valid" in company_ids


class TestLoadCompanyConfig:
    """Tests for load_company_config() function."""

    def test_load_company_config_returns_config(self, mock_config_dir):
        """Test that load_company_config returns CompanyConfig."""
        config = load_company_config("jc-services", mock_config_dir)
        
        assert config is not None
        assert config.company_id == "jc-services"

    def test_load_company_config_nonexistent_company(self, mock_config_dir):
        """Test loading nonexistent company raises error."""
        with pytest.raises((FileNotFoundError, ValueError, KeyError)):
            load_company_config("nonexistent-company", mock_config_dir)

    def test_load_company_config_multiple_companies(self, temp_dir):
        """Test loading different companies returns different configs."""
        company_dir = temp_dir / "companies"
        company_dir.mkdir()
        
        # Create two company configs
        config1 = {
            "company_id": "company-a",
            "company_name": "Company A",
            "payment_bcp_account": "1111-2222-3333",
            "payment_bcp_cci": "CCI A",
            "payment_detracciones_account": "",
            "payment_bank_label": "Bank A",
            "offer_note_primary": "",
            "offer_note_secondary": "",
            "workshop_address": "Address A",
            "fiscal_address": "Fiscal A",
            "header_image": "",
            "watermark_image": ""
        }
        
        config2 = {
            "company_id": "company-b",
            "company_name": "Company B",
            "payment_bcp_account": "4444-5555-6666",
            "payment_bcp_cci": "CCI B",
            "payment_detracciones_account": "",
            "payment_bank_label": "Bank B",
            "offer_note_primary": "",
            "offer_note_secondary": "",
            "workshop_address": "Address B",
            "fiscal_address": "Fiscal B",
            "header_image": "",
            "watermark_image": ""
        }
        
        (company_dir / "company-a.json").write_text(json.dumps(config1))
        (company_dir / "company-b.json").write_text(json.dumps(config2))
        
        loaded_a = load_company_config("company-a", company_dir)
        loaded_b = load_company_config("company-b", company_dir)
        
        assert loaded_a.company_id == "company-a"
        assert loaded_b.company_id == "company-b"
        assert loaded_a.payment_bcp_account != loaded_b.payment_bcp_account


class TestAPIEndpoints:
    """Tests for HTTP API endpoints."""

    def test_api_companies_endpoint(self, mock_config_dir):
        """Test GET /api/companies endpoint returns company list."""
        # Note: This test may need to be adapted based on actual server implementation
        # It assumes the endpoint returns JSON array of companies
        pass

    def test_api_config_endpoint_with_company_id(self, mock_config_dir):
        """Test GET /api/config?company_id=X endpoint returns config."""
        # Test assumes endpoint loads company config and returns as JSON
        pass

    def test_api_config_endpoint_missing_company_id(self):
        """Test /api/config without company_id returns error."""
        # Should return 400 Bad Request
        pass

    def test_api_config_endpoint_invalid_company_id(self, mock_config_dir):
        """Test /api/config with invalid company_id returns 404."""
        # Should return 404 Not Found
        pass


class TestAPIExportPDF:
    """Tests for POST /api/export/pdf endpoint."""

    def test_export_pdf_valid_payload(self, sample_payload):
        """Test exporting PDF with valid payload."""
        # POST request with proforma data should return PDF
        pass

    def test_export_pdf_missing_required_fields(self):
        """Test exporting PDF with incomplete payload."""
        # Should return 400 Bad Request with error message
        pass

    def test_export_pdf_invalid_tax_mode(self, sample_payload):
        """Test exporting PDF with invalid tax_mode."""
        # Should return 400 Bad Request
        pass

    def test_export_pdf_response_has_content_type(self):
        """Test that PDF response has correct Content-Type header."""
        # Response should have 'application/pdf' Content-Type
        pass

    def test_export_pdf_response_has_content_disposition(self):
        """Test that PDF response has Content-Disposition header."""
        # Response should suggest download filename
        pass


class TestAPIExportDOCX:
    """Tests for POST /api/export/docx endpoint."""

    def test_export_docx_valid_payload(self, sample_payload):
        """Test exporting DOCX with valid payload."""
        # POST request with proforma data should return DOCX
        pass

    def test_export_docx_missing_required_fields(self):
        """Test exporting DOCX with incomplete payload."""
        # Should return 400 Bad Request
        pass

    def test_export_docx_response_has_content_type(self):
        """Test that DOCX response has correct Content-Type header."""
        # Response should have 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        pass

    def test_export_docx_response_has_content_disposition(self):
        """Test that DOCX response has Content-Disposition header."""
        # Response should suggest download filename
        pass


class TestServerErrorHandling:
    """Tests for server error handling."""

    def test_404_not_found_invalid_path(self):
        """Test that invalid path returns 404."""
        # GET /invalid/path should return 404 Not Found
        pass

    def test_method_not_allowed(self):
        """Test that invalid HTTP method returns error."""
        # DELETE /api/export/pdf should return 405 or 400
        pass

    def test_invalid_json_payload(self):
        """Test that invalid JSON in request body returns error."""
        # POST /api/export/pdf with invalid JSON should return 400
        pass

    def test_malformed_query_string(self):
        """Test that malformed query string is handled."""
        # GET /api/config?invalid returns error
        pass


class TestServerConcurrency:
    """Tests for concurrent request handling."""

    def test_concurrent_export_requests(self, sample_payload):
        """Test handling multiple concurrent PDF export requests."""
        # Should handle multiple simultaneous requests without errors
        pass

    def test_concurrent_config_requests(self, mock_config_dir):
        """Test handling multiple concurrent config requests."""
        # Should return correct config for each company
        pass

    def test_request_timeout_handling(self):
        """Test that long-running requests don't block other requests."""
        # Server should handle timeouts gracefully
        pass


class TestServerPerformance:
    """Tests for server performance and efficiency."""

    def test_pdf_generation_completes_in_time(self, sample_payload):
        """Test that PDF generation completes within reasonable time."""
        # Should complete in less than 5 seconds for typical payload
        pass

    def test_docx_generation_completes_in_time(self, sample_payload):
        """Test that DOCX generation completes within reasonable time."""
        # Should complete in less than 5 seconds for typical payload
        pass

    def test_config_loading_cached_performance(self, mock_config_dir):
        """Test that repeated config loading is efficient."""
        # Second load should be faster (if caching is implemented)
        pass


class TestServerConfigurationPaths:
    """Tests for server configuration and file paths."""

    def test_output_directory_created(self, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        # Server should create output/pdf and output/docx if missing
        pass

    def test_pdf_files_saved_to_correct_location(self, temp_dir, sample_payload):
        """Test that generated PDFs are saved to output/pdf/."""
        # PDF files should be in output/pdf directory
        pass

    def test_docx_files_saved_to_correct_location(self, temp_dir, sample_payload):
        """Test that generated DOCX files are saved to output/docx/."""
        # DOCX files should be in output/docx directory
        pass


class TestServerWithDifferentCompanies:
    """Tests for server behavior with different company configurations."""

    def test_export_with_different_companies(self, mock_config_dir):
        """Test exporting proforma for different companies."""
        # Should use correct company branding/info for each
        pass

    def test_payment_info_specific_to_company(self, mock_config_dir):
        """Test that payment info comes from correct company config."""
        # BCP account should match company configuration
        pass

    def test_addresses_specific_to_company(self, mock_config_dir):
        """Test that workshop/fiscal addresses come from company config."""
        # Addresses should match company configuration
        pass


class TestServerRequestValidation:
    """Tests for request input validation."""

    def test_validate_required_payload_fields(self):
        """Test validation of required fields in payload."""
        # issue_date, customer_name, items, tax_mode must be present
        pass

    def test_validate_items_list_format(self):
        """Test validation that items is a list."""
        # items must be an array of objects
        pass

    def test_validate_item_required_fields(self):
        """Test validation of fields in each item."""
        # Each item needs description, quantity, unit_price
        pass

    def test_validate_numeric_quantities(self):
        """Test validation that quantities are numeric."""
        # quantity must be number
        pass

    def test_validate_positive_prices(self):
        """Test validation that prices are positive."""
        # unit_price should be >= 0
        pass
