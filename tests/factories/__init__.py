"""
Test factories for creating test objects and mocks.

This package contains factory functions for creating test objects,
mocks, and configured instances for testing purposes.
"""

from .storage_factory import create_mock_storage_adapter, create_live_storage_adapter

__all__ = ['create_mock_storage_adapter', 'create_live_storage_adapter']