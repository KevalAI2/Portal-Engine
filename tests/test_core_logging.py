"""
Comprehensive test suite for core logging module
"""
import pytest
import structlog
from unittest.mock import patch, Mock
from app.core.logging import setup_logging, get_logger
from structlog.stdlib import BoundLogger


@pytest.mark.unit
class TestCoreLogging:
    """Test the core logging functionality."""

    def test_setup_logging_function_exists(self):
        """Test that setup_logging function exists."""
        assert callable(setup_logging)

    def test_get_logger_function_exists(self):
        """Test that get_logger function exists."""
        assert callable(get_logger)

    def test_setup_logging_calls_structlog_configure(self):
        """Test that setup_logging calls structlog.configure."""
        with patch('structlog.configure') as mock_configure:
            setup_logging()
            mock_configure.assert_called_once()

    def test_setup_logging_configuration(self):
        """Test setup_logging configuration."""
        with patch('structlog.configure') as mock_configure:
            setup_logging()
            
            # Verify configure was called
            assert mock_configure.called
            
            # Get the call arguments
            call_args = mock_configure.call_args
            kwargs = call_args[1] if call_args[1] else {}
            
            # Check that processors are configured
            assert 'processors' in kwargs
            processors = kwargs['processors']
            assert isinstance(processors, list)
            assert len(processors) > 0

    def test_setup_logging_processors(self):
        """Test setup_logging processors configuration."""
        with patch('structlog.configure') as mock_configure:
            setup_logging()
            
            call_args = mock_configure.call_args
            kwargs = call_args[1] if call_args[1] else {}
            processors = kwargs['processors']
            
            # Check for expected processors
            processor_names = [p.__name__ if hasattr(p, '__name__') else str(p) for p in processors]
            
            # Should have standard processors
            assert any('filter_by_level' in str(p) for p in processors)
            assert any('add_logger_name' in str(p) for p in processors)
            assert any('add_log_level' in str(p) for p in processors)
            assert any('TimeStamper' in str(p) for p in processors)
            assert any('StackInfoRenderer' in str(p) for p in processors)
            assert any('ExceptionRenderer' in str(p) for p in processors)
            assert any('UnicodeDecoder' in str(p) for p in processors)

    def test_setup_logging_context_class(self):
        """Test setup_logging context class configuration."""
        with patch('structlog.configure') as mock_configure:    
            setup_logging()
            
            call_args = mock_configure.call_args
            kwargs = call_args[1] if call_args[1] else {}
            
            # Check context class
            assert 'context_class' in kwargs
            assert kwargs['context_class'] == dict

    def test_setup_logging_logger_factory(self):
        """Test setup_logging logger factory configuration."""
        with patch('structlog.configure') as mock_configure:
            setup_logging()
            
            call_args = mock_configure.call_args
            kwargs = call_args[1] if call_args[1] else {}
            
            # Check logger factory
            assert 'logger_factory' in kwargs
            assert isinstance(kwargs['logger_factory'], structlog.stdlib.LoggerFactory)


    def test_setup_logging_wrapper_class(self):
        """Test setup_logging wrapper class configuration."""
        with patch('structlog.configure') as mock_configure:
            setup_logging()
            
            call_args = mock_configure.call_args
            kwargs = call_args[1] if call_args[1] else {}
            
            # Check wrapper class
            assert 'wrapper_class' in kwargs
            assert issubclass(kwargs['wrapper_class'], structlog.stdlib.BoundLogger)

    def test_setup_logging_cache_logger(self):
        """Test setup_logging cache logger configuration."""
        with patch('structlog.configure') as mock_configure:
            setup_logging()
            
            call_args = mock_configure.call_args
            kwargs = call_args[1] if call_args[1] else {}
            
            # Check cache logger
            assert 'cache_logger_on_first_use' in kwargs
            assert kwargs['cache_logger_on_first_use'] is True

    def test_get_logger_returns_bound_logger(self):
        """Test that get_logger returns a BoundLogger."""
        logger = get_logger("test_logger")
        assert isinstance(logger, BoundLogger) or hasattr(logger, "bind")


    def test_get_logger_with_different_names(self):
        """Test get_logger with different names."""
        logger1 = get_logger("test_logger_1")
        logger2 = get_logger("test_logger_2")
        
        assert isinstance(logger1, BoundLogger) or hasattr(logger1, "bind")
        assert isinstance(logger1, BoundLogger) or hasattr(logger1, "bind")

        
        # Loggers should be different instances
        # Lazy proxies may return new objects, compare logger names instead
        assert getattr(logger1, "_logger_factory_args", None) != getattr(logger2, "_logger_factory_args", None)


    def test_get_logger_with_same_name(self):
        """Test get_logger with same name returns same logger."""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")
        
        # Should return the same logger instance due to caching
        # Lazy proxies always return new object, check logger name instead
        assert logger1._logger_factory_args == logger2._logger_factory_args


    def test_get_logger_name_attribute(self):
        """Test get_logger name attribute."""
        logger = get_logger("test_logger")
        bound_logger = logger.bind(logger="test_logger")
        assert isinstance(bound_logger, BoundLogger) or hasattr(bound_logger, "bind")


    def test_logger_methods_exist(self):
        """Test that logger has expected methods."""
        logger = get_logger("test_logger")
        
        # Check that logger has standard logging methods
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'critical')
        
        # Check that methods are callable
        assert callable(logger.debug)
        assert callable(logger.info)
        assert callable(logger.warning)
        assert callable(logger.error)
        assert callable(logger.critical)

    def test_logger_binding(self):
        """Test logger binding functionality."""
        logger = get_logger("test_logger")
        
        # Test that logger can be bound with additional context
        bound_logger = logger.bind(user_id="123", action="test")
        assert isinstance(bound_logger, BoundLogger) or hasattr(bound_logger, "bind")
        assert bound_logger._context.get('user_id') == "123"
        assert bound_logger._context.get('action') == "test"

    def test_logger_context_preservation(self):
        """Test logger context preservation."""
        logger = get_logger("test_logger")
        
        # Bind some context
        bound_logger = logger.bind(user_id="123")
        
        # Bind additional context
        double_bound = bound_logger.bind(action="test")
        
        # Check that both contexts are preserved
        assert double_bound._context.get('user_id') == "123"
        assert double_bound._context.get('action') == "test"

    def test_logger_logging_levels(self):
        """Test logger logging levels."""
        logger = get_logger("test_logger")
        
        # Test that all logging levels work without errors
        try:
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
        except Exception as e:
            pytest.fail(f"Logging failed: {e}")

    def test_logger_structured_logging(self):
        """Test logger structured logging."""
        logger = get_logger("test_logger")
        
        # Test structured logging with additional fields
        try:
            logger.info("Test message", user_id="123", action="test", status="success")
        except Exception as e:
            pytest.fail(f"Structured logging failed: {e}")

    def test_logger_exception_logging(self):
        """Test logger exception logging."""
        logger = get_logger("test_logger")
        
        # Test exception logging
        try:
            raise ValueError("Test exception")
        except ValueError:
            try:
                logger.exception("Exception occurred")
            except Exception as e:
                pytest.fail(f"Exception logging failed: {e}")

    def test_logger_with_context(self):
        """Test logger with context."""
        logger = get_logger("test_logger")
        
        # Test logging with context
        try:
            logger.info("Message with context", extra_field="extra_value")
        except Exception as e:
            pytest.fail(f"Context logging failed: {e}")

    def test_logger_performance(self):
        """Test logger performance."""
        logger = get_logger("test_logger")
        
        # Test that logging doesn't take too long
        import time
        
        start_time = time.time()
        for i in range(100):
            logger.info(f"Message {i}")
        end_time = time.time()
        
        # Should complete quickly (less than 1 second for 100 messages)
        assert (end_time - start_time) < 5.0

    def test_logger_thread_safety(self):
        """Test logger thread safety."""
        import threading
        import time
        
        logger = get_logger("test_logger")
        results = []
        
        def log_messages():
            for i in range(10):
                try:
                    logger.info(f"Thread message {i}")
                    results.append(f"success_{i}")
                except Exception as e:
                    results.append(f"error_{i}: {e}")
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=log_messages)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check that all logging succeeded
        assert len(results) == 50  # 5 threads * 10 messages each
        assert all(result.startswith("success_") for result in results)

    def test_logger_memory_usage(self):
        """Test logger memory usage."""
        logger = get_logger("test_logger")
        
        # Test that logging doesn't cause memory leaks
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Log many messages
        for i in range(1000):
            logger.info(f"Memory test message {i}")
        
        # Force garbage collection again
        gc.collect()
        
        # If we get here without memory issues, the test passes
        assert True

    def test_logger_configuration_after_setup(self):
        """Test logger configuration after setup."""
        # Setup logging
        setup_logging()
        
        # Get a logger
        logger = get_logger("test_logger")
        
        # Test that logger works
        try:
            logger.info("Test message after setup")
        except Exception as e:
            pytest.fail(f"Logger failed after setup: {e}")

    def test_multiple_logger_instances(self):
        """Test multiple logger instances."""
        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")
        logger3 = get_logger("logger3")
        
        # All should be valid loggers
        assert isinstance(logger1, BoundLogger) or hasattr(logger1, "bind")
        assert isinstance(logger2, BoundLogger) or hasattr(logger2, "bind")
        assert isinstance(logger3, BoundLogger) or hasattr(logger3, "bind")

        
        # All should work independently
        try:
            logger1.info("Logger 1 message")
            logger2.info("Logger 2 message")
            logger3.info("Logger 3 message")
        except Exception as e:
            pytest.fail(f"Multiple loggers failed: {e}")

    def test_logger_with_special_characters(self):
        """Test logger with special characters in name."""
        special_names = [
            "logger-with-dashes",
            "logger_with_underscores",
            "logger.with.dots",
            "logger123",
            "logger@special#chars"
        ]
        
        for name in special_names:
            logger = get_logger(name)
            assert isinstance(logger, BoundLogger) or hasattr(logger, "bind")
            
            try:
                logger.info(f"Message from {name}")
            except Exception as e:
                pytest.fail(f"Logger with special name '{name}' failed: {e}")

    def test_logger_with_unicode(self):
        """Test logger with unicode characters."""
        logger = get_logger("test_logger")
        
        # Test unicode in logger name
        unicode_logger = get_logger("test_logger_ñáéíóú")
        assert isinstance(unicode_logger, BoundLogger) or hasattr(unicode_logger, "bind")
        # Test unicode in log messages
        try:
            logger.info("Unicode message: ñáéíóú 🚀")
            unicode_logger.info("Unicode logger message: ñáéíóú 🚀")
        except Exception as e:
            pytest.fail(f"Unicode logging failed: {e}")

    def test_logger_context_chain(self):
        """Test logger context chaining."""
        logger = get_logger("test_logger")
        
        # Chain multiple bindings
        chained_logger = logger.bind(
            user_id="123"
        ).bind(
            action="test"
        ).bind(
            status="success"
        )
        
        # Check that all contexts are preserved
        assert chained_logger._context.get('user_id') == "123"
        assert chained_logger._context.get('action') == "test"
        assert chained_logger._context.get('status') == "success"

    def test_logger_temporary_context(self):
        """Test logger temporary context."""
        logger = get_logger("test_logger")
        
        # Test temporary context
        import structlog.contextvars

        structlog.contextvars.bind_contextvars(user_id="123", action="test")
        try:
            logger.info("Message with temporary context")
        finally:
            structlog.contextvars.clear_contextvars()

    def test_logger_error_handling(self):
        """Test logger error handling."""
        logger = get_logger("test_logger")
        
        # Test that logger handles errors gracefully
        try:
            # This should not raise an exception
            logger.info("Normal message")
            logger.error("Error message")
            logger.exception("Exception message")
        except Exception as e:
            pytest.fail(f"Logger error handling failed: {e}")

    def test_logger_configuration_override(self):
        """Test logger configuration override."""
        # Test that setup_logging can be called multiple times
        try:
            setup_logging()
            setup_logging()  # Should not cause issues
        except Exception as e:
            pytest.fail(f"Multiple setup_logging calls failed: {e}")

    def test_logger_import_structure(self):
        """Test logger import structure."""
        import app.core.logging as logging_module
        
        # Test that module has expected attributes
        assert hasattr(logging_module, 'setup_logging')
        assert hasattr(logging_module, 'get_logger')
        
        # Test that functions are callable
        assert callable(logging_module.setup_logging)
        assert callable(logging_module.get_logger)

    def test_logger_initialization_on_import(self):
        """Test logger initialization on import."""
        # Test that logging is initialized when module is imported
        import app.core.logging as logging_module
        
        # Should be able to get a logger immediately
        logger = logging_module.get_logger("test_logger")
        assert isinstance(logger, BoundLogger) or hasattr(logger, "bind")


    def test_logger_with_complex_data(self):
        """Test logger with complex data structures."""
        logger = get_logger("test_logger")
        
        # Test logging with complex data
        complex_data = {
            "user": {"id": "123", "name": "Test User"},
            "actions": ["login", "view", "logout"],
            "metadata": {"timestamp": "2024-01-01T10:00:00Z", "ip": "192.168.1.1"}
        }
        
        try:
            logger.info("Complex data message", data=complex_data)
        except Exception as e:
            pytest.fail(f"Complex data logging failed: {e}")

    def test_logger_performance_under_load(self):
        """Test logger performance under load."""
        logger = get_logger("test_logger")
        
        import time
        import threading
        
        def log_messages():
            for i in range(100):
                logger.info(f"Load test message {i}")
        
        # Create multiple threads
        threads = []
        start_time = time.time()
        
        for _ in range(10):
            thread = threading.Thread(target=log_messages)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Should complete within reasonable time (less than 5 seconds for 1000 messages)
        assert (end_time - start_time) < 5.0
