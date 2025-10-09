import unittest
from app.core.validators import (
    validate_email, validate_phone, validate_user_id, validate_password_strength,
    validate_url, validate_json_data, sanitize_string, validate_pagination_params,
    validate_sort_params, validate_date_range, validate_request_data, validate_api_key,
    validate_correlation_id, validate_rate_limit_params, validate_file_upload,
    validate_search_query, validate_recommendation_params, validate_health_check_params
)
from app.core.exceptions import ValidationError as CustomValidationError

class TestValidators(unittest.TestCase):

    def test_validate_email_valid(self):
        self.assertEqual(validate_email("test@example.com"), "test@example.com")
        self.assertEqual(validate_email("  Test@Example.COM  "), "test@example.com")

    def test_validate_email_invalid(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_email("invalid")
        self.assertIn("Invalid email format", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_email("@example.com")
        self.assertIn("Invalid email format", str(cm.exception))

    def test_validate_phone_valid(self):
        self.assertEqual(validate_phone("+1 (123) 456-7890"), "11234567890")
        self.assertEqual(validate_phone("1234567"), "1234567")

    def test_validate_phone_invalid(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_phone("123")
        self.assertIn("between 7 and 15 digits", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_phone("1" * 16)
        self.assertIn("between 7 and 15 digits", str(cm.exception))

    def test_validate_user_id_valid(self):
        self.assertEqual(validate_user_id("user-123"), "user-123")
        self.assertEqual(validate_user_id("abc_456"), "abc_456")

    def test_validate_user_id_invalid_type(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_user_id(123)
        self.assertIn("non-empty string", str(cm.exception))

    def test_validate_user_id_invalid_empty(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_user_id("")
        self.assertIn("non-empty string", str(cm.exception))

    def test_validate_user_id_invalid_length(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_user_id("us")
        self.assertIn("between 3 and 50 characters", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_user_id("a" * 51)
        self.assertIn("between 3 and 50 characters", str(cm.exception))

    def test_validate_user_id_invalid_characters(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_user_id("user@123")
        self.assertIn("only contain letters, numbers, underscores, and hyphens", str(cm.exception))

    def test_validate_password_strength_valid(self):
        self.assertEqual(validate_password_strength("Passw0rd!"), "Passw0rd!")

    def test_validate_password_strength_invalid_length(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_password_strength("short")
        self.assertIn("at least 8 characters long", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_password_strength("a" * 129)
        self.assertIn("no more than 128 characters long", str(cm.exception))

    def test_validate_password_strength_invalid_composition(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_password_strength("password1!")
        self.assertIn("one uppercase letter", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_password_strength("PASSWORD1!")
        self.assertIn("one lowercase letter", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_password_strength("Password!")
        self.assertIn("one digit", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_password_strength("Password1")
        self.assertIn("one special character", str(cm.exception))

    def test_validate_url_valid(self):
        self.assertEqual(validate_url("https://example.com"), "https://example.com")
        self.assertEqual(validate_url("http://www.example.com/path?query=1#fragment"), "http://www.example.com/path?query=1#fragment")

    def test_validate_url_invalid(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_url("invalid")
        self.assertIn("Invalid URL format", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_url("ftp://example.com")
        self.assertIn("Invalid URL format", str(cm.exception))

    def test_validate_json_data_valid(self):
        data = {"key1": "value1", "key2": "value2"}
        self.assertEqual(validate_json_data(data, ["key1", "key2"]), data)

    def test_validate_json_data_invalid_type(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_json_data("not dict", [])
        self.assertIn("must be a JSON object", str(cm.exception))

    def test_validate_json_data_invalid_missing_fields(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_json_data({}, ["key1"])
        self.assertIn("Missing required fields: key1", str(cm.exception))

    def test_sanitize_string(self):
        self.assertEqual(sanitize_string("  test \x00 "), "test")
        self.assertEqual(sanitize_string(123), "123")
        self.assertEqual(sanitize_string("a" * 300), "a" * 255)

    def test_validate_pagination_params_valid(self):
        self.assertEqual(validate_pagination_params(1, 10), (1, 10))
        self.assertEqual(validate_pagination_params(5, 100), (5, 100))

    def test_validate_pagination_params_invalid(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_pagination_params(0, 10)
        self.assertIn("at least 1", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_pagination_params(1, 0)
        self.assertIn("between 1 and 100", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_pagination_params(1, 101)
        self.assertIn("between 1 and 100", str(cm.exception))

    def test_validate_sort_params_valid(self):
        self.assertEqual(validate_sort_params("name", ["name", "id"]), "name")
        self.assertEqual(validate_sort_params("-name", ["name", "id"]), "-name")
        self.assertEqual(validate_sort_params("", ["name", "id"]), "name")
        self.assertEqual(validate_sort_params("", []), "id")

    def test_validate_sort_params_invalid(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_sort_params("invalid", ["name", "id"])
        self.assertIn("must be one of: name, id", str(cm.exception))

    def test_validate_date_range_valid(self):
        self.assertEqual(validate_date_range("2023-01-01", "2023-12-31"), ("2023-01-01", "2023-12-31"))
        self.assertEqual(validate_date_range(None, None), (None, None))
        self.assertEqual(validate_date_range("2023-01-01", None), ("2023-01-01", None))

    def test_validate_date_range_invalid_format(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_date_range("2023-1-1", "2023-12-31")
        self.assertIn("YYYY-MM-DD format", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_date_range("2023-01-01", "2023-1-1")
        self.assertIn("YYYY-MM-DD format", str(cm.exception))

    def test_validate_date_range_invalid_order(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_date_range("2023-01-01", "2022-12-31")
        self.assertIn("before end date", str(cm.exception))

    def test_validate_request_data_valid(self):
        data = {"email": "test@example.com", "name": "test"}
        validators = {"email": validate_email}
        self.assertEqual(validate_request_data(data, ["email"], ["name"], validators), {"email": "test@example.com", "name": "test"})

        # Test without validators and optional fields
        self.assertEqual(validate_request_data({"key": "value"}, ["key"]), {"key": "value"})

    def test_validate_request_data_invalid_missing_fields(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_request_data({}, ["email"])
        self.assertIn("Missing required fields: email", str(cm.exception))

    def test_validate_request_data_invalid_field_validation(self):
        data = {"email": "invalid"}
        validators = {"email": validate_email}
        with self.assertRaises(CustomValidationError) as cm:
            validate_request_data(data, ["email"], field_validators=validators)
        self.assertIn("Validation failed for email", str(cm.exception))

    def test_validate_api_key_valid(self):
        self.assertEqual(validate_api_key("abc123-DEF456-ghi789"), "abc123-DEF456-ghi789")

    def test_validate_api_key_invalid(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_api_key("")
        self.assertIn("non-empty string", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_api_key("short")
        self.assertIn("between 16 and 64 characters", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_api_key("a" * 65)
        self.assertIn("between 16 and 64 characters", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_api_key("abc123@def")
        self.assertIn("only contain letters, numbers, and hyphens", str(cm.exception))

    def test_validate_correlation_id_valid(self):
        self.assertEqual(validate_correlation_id("12345678-1234-1234-1234-123456789abc"), "12345678-1234-1234-1234-123456789abc")
        self.assertEqual(validate_correlation_id("abc_123-DEF"), "abc_123-DEF")

    def test_validate_correlation_id_invalid(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_correlation_id("")
        self.assertIn("non-empty string", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_correlation_id("short")
        self.assertIn("valid UUID or 8-32 character", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_correlation_id("a" * 33)
        self.assertIn("valid UUID or 8-32 character", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_correlation_id("invalid@format")
        self.assertIn("valid UUID or 8-32 character", str(cm.exception))

    def test_validate_rate_limit_params_valid(self):
        self.assertEqual(validate_rate_limit_params(100, 50), (100, 50))

    def test_validate_rate_limit_params_invalid(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_rate_limit_params(0, 10)
        self.assertIn("between 1 and 10000", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_rate_limit_params(100, 0)
        self.assertIn("between 1 and 1000", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_rate_limit_params(100, 200)
        self.assertIn("cannot exceed requests per minute", str(cm.exception))

    def test_validate_file_upload_valid(self):
        self.assertEqual(validate_file_upload("file.txt", "text/plain"), ("file.txt", "text/plain"))
        allowed = ["image/jpeg"]
        self.assertEqual(validate_file_upload("image.jpg", "image/jpeg", allowed_types=allowed), ("image.jpg", "image/jpeg"))

    def test_validate_file_upload_invalid_filename(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_file_upload("", "text/plain")
        self.assertIn("non-empty string", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_file_upload("a" * 256, "text/plain")
        self.assertIn("no more than 255 characters", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_file_upload("../file.txt", "text/plain")
        self.assertIn("dangerous characters", str(cm.exception))

    def test_validate_file_upload_invalid_content_type(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_file_upload("file.txt", "")
        self.assertIn("non-empty string", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_file_upload("file.txt", "invalid", allowed_types=["text/plain"])
        self.assertIn("must be one of: text/plain", str(cm.exception))

    def test_validate_search_query_valid(self):
        self.assertEqual(validate_search_query("test query"), "test query")
        self.assertEqual(validate_search_query("  ab  ", min_length=1), "ab")

    def test_validate_search_query_invalid(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_search_query("")
        self.assertIn("non-empty string", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_search_query("a", min_length=2)
        self.assertIn("at least 2 characters", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_search_query("a" * 101)
        self.assertIn("no more than 100 characters", str(cm.exception))

    def test_validate_search_query_sql_pattern(self):
        # Ensures the SQL pattern check branch is covered (logging is a side effect)
        self.assertEqual(validate_search_query("select * from users"), "select * from users")

    def test_validate_recommendation_params_valid(self):
        self.assertEqual(validate_recommendation_params("user-123", 10), ("user-123", 10, None))
        self.assertEqual(validate_recommendation_params("user-123", 50, {"key": "value"}), ("user-123", 50, {"key": "value"}))

    def test_validate_recommendation_params_invalid_limit(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_recommendation_params("user-123", 0)
        self.assertIn("between 1 and 100", str(cm.exception))

    def test_validate_recommendation_params_invalid_filters(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_recommendation_params("user-123", 10, "not dict")
        self.assertIn("must be a dictionary", str(cm.exception))

    def test_validate_recommendation_params_invalid_user_id(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_recommendation_params("us", 10)
        self.assertIn("between 3 and 50 characters", str(cm.exception))

    def test_validate_health_check_params_valid(self):
        self.assertEqual(validate_health_check_params("service", 30), ("service", 30))
        self.assertEqual(validate_health_check_params("  test  ", 100), ("test", 100))

    def test_validate_health_check_params_invalid(self):
        with self.assertRaises(CustomValidationError) as cm:
            validate_health_check_params("", 30)
        self.assertIn("non-empty string", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_health_check_params("service", 0)
        self.assertIn("between 1 and 300 seconds", str(cm.exception))

        with self.assertRaises(CustomValidationError) as cm:
            validate_health_check_params("service", 301)
        self.assertIn("between 1 and 300 seconds", str(cm.exception))

if __name__ == '__main__':
    unittest.main()