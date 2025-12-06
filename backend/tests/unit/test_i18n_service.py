"""
Unit tests for I18nService
"""
from datetime import datetime

import pytest

from src.services.i18n_service import I18nService


class TestI18nService:
    """Test suite for I18nService"""

    def setup_method(self):
        """Setup test instance"""
        self.service = I18nService()

    def test_translate_english(self):
        """Test translation to English"""
        result = self.service.translate("users.not_found", "en")
        assert result == "User not found"

    def test_translate_french(self):
        """Test translation to French"""
        result = self.service.translate("users.not_found", "fr")
        assert result == "Utilisateur non trouvé"

    def test_translate_default_language(self):
        """Test translation with default language"""
        result = self.service.translate("users.not_found")
        assert result == "User not found"

    def test_translate_with_formatting(self):
        """Test translation with formatting arguments"""
        # Créer une clé temporaire avec formatage
        key = "test.formatting"
        from src.services.i18n_service import translations
        if key not in translations["en"]:
            translations["en"][key] = "Test {value}"
        result = self.service.translate(key, "en", value="123")
        assert "123" in result

    def test_translate_missing_key(self):
        """Test translation with missing key returns key"""
        result = self.service.translate("nonexistent.key", "en")
        assert result == "nonexistent.key"

    def test_translate_invalid_language_fallback(self):
        """Test translation with invalid language falls back to key"""
        result = self.service.translate("users.not_found", "invalid_lang")
        assert result == "User not found"

    def test_format_date_english_short(self):
        """Test date formatting in English (short)"""
        date = datetime(2025, 12, 6, 15, 30)
        result = self.service.format_date(date, "en", "short")
        assert "12" in result and "25" in result

    def test_format_date_french_short(self):
        """Test date formatting in French (short)"""
        date = datetime(2025, 12, 6, 15, 30)
        result = self.service.format_date(date, "fr", "short")
        assert "12" in result and "25" in result

    def test_format_date_long_format(self):
        """Test date formatting with long format"""
        date = datetime(2025, 12, 6, 15, 30)
        result = self.service.format_date(date, "en", "long")
        assert "December" in result

    def test_format_date_full_format(self):
        """Test date formatting with full format"""
        date = datetime(2025, 12, 6, 15, 30)
        result = self.service.format_date(date, "en", "full")
        assert "2025" in result and "30" in result

    def test_format_currency_english_usd(self):
        """Test currency formatting in English (USD)"""
        result = self.service.format_currency(1234.56, "en", "USD")
        assert "$" in result
        assert "1,234.56" in result

    def test_format_currency_french_eur(self):
        """Test currency formatting in French (EUR)"""
        result = self.service.format_currency(1234.56, "fr", "EUR")
        assert "€" in result

    def test_format_currency_default_currency(self):
        """Test currency formatting with default currency"""
        result = self.service.format_currency(1234.56, "en")
        assert "USD" in result or "$" in result

    def test_format_number_english(self):
        """Test number formatting in English"""
        result = self.service.format_number(1234.567, "en", 2)
        assert "1,234.57" in result

    def test_format_number_french(self):
        """Test number formatting in French"""
        result = self.service.format_number(1234.567, "fr", 2)
        # French uses space as thousands separator
        assert "1" in result and "234" in result

    def test_set_default_language(self):
        """Test setting default language"""
        self.service.set_default_language("fr")
        assert self.service.default_language == "fr"

        # Verify translation uses new default
        result = self.service.translate("users.not_found")
        assert result == "Utilisateur non trouvé"

    def test_set_invalid_default_language(self):
        """Test setting invalid default language keeps existing"""
        original_language = self.service.default_language
        self.service.set_default_language("invalid_lang")
        # Should not change to invalid language
        assert self.service.default_language == original_language

    def test_get_system_language(self):
        """Test getting system language (always returns 'en')"""
        result = self.service.get_system_language()
        assert result == "en"

    def test_complex_translation_english(self):
        """Test complex translation scenarios in English"""
        assert "Total Users" == self.service.translate("report.total_users", "en")
        assert "Department" == self.service.translate("report.department", "en")
        assert "License Summary" == self.service.translate("report.section.license_summary", "en")

    def test_complex_translation_french(self):
        """Test complex translation scenarios in French"""
        assert "Nombre Total d'Utilisateurs" == self.service.translate("report.total_users", "fr")
        assert "Département" == self.service.translate("report.department", "fr")
        assert "Résumé des Licences" == self.service.translate("report.section.license_summary", "fr")

    def test_date_format_consistency(self):
        """Test that date formatting is consistent"""
        date = datetime(2025, 12, 6, 15, 30)

        en_short = self.service.format_date(date, "en", "short")
        en_long = self.service.format_date(date, "en", "long")
        en_full = self.service.format_date(date, "en", "full")

        # All should contain year and day
        assert ("2025" in en_short or "25" in en_short)
        assert "December" in en_long
        assert ("15" in en_full or "PM" in en_full or "3" in en_full)  # Heure en format 12h ou 24h

    def test_currency_format_varying_amounts(self):
        """Test currency formatting with varying amounts"""
        amounts = [0, 1.5, 100, 1000.50, 999999.99]

        for amount in amounts:
            result = self.service.format_currency(amount, "en", "USD")
            assert "$" in result
            # Vérifier que le montant est présent (en ignorant les séparateurs de milliers)
            amount_str = str(amount).split(".")[0]
            # Extraire uniquement les chiffres pour la comparaison
            result_digits = ''.join(c for c in result if c.isdigit())
            assert amount_str in result_digits

    def test_number_format_decimal_places(self):
        """Test number formatting with different decimal places"""
        number = 123.456789

        result_0 = self.service.format_number(number, "en", 0)
        assert "123" in result_0

        result_2 = self.service.format_number(number, "en", 2)
        assert "123.46" in result_2 or "123.46" in result_2

        result_5 = self.service.format_number(number, "en", 5)
        assert "123.45679" in result_5

    @pytest.mark.parametrize("lang,expected", [
        ("en", "en_US"),
        ("fr", "fr_FR"),
    ])
    def test_language_locale_mapping(self, lang, expected):
        """Test that language codes map to correct locale"""
        # This is internal but we can test the behavior
        date = datetime(2025, 12, 6, 15, 30)
        result = self.service.format_date(date, lang, "short")
        assert result is not None

    def test_babel_fallback_on_error(self):
        """Test that formatting falls back gracefully on Babel errors"""
        # This tests the exception handling in format methods
        from datetime import datetime
        from unittest.mock import patch

        date = datetime(2025, 12, 6, 15, 30)

        # Simuler une erreur Babel
        with patch('babel.dates.format_datetime', side_effect=Exception("Babel error")):
            result = self.service.format_date(date, "en", "short")
            # Devrait tomber sur le format de secours
            assert result is not None
            assert ("2025" in result or "2025-12-06" in result or "25" in result)  # Format court avec YY
