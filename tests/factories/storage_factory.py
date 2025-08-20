"""
Factory functions for creating storage adapters in tests.

This module provides factory functions to create storage adapters
with appropriate mocking for different testing scenarios.
"""

from src.adapters.secondary.supabase.supabase_storage_adapter import SupabaseStorageAdapter
from src.infrastructure.config.supabase_config import SupabaseConfig
from tests.mocks.mock_supabase_client import MockSupabaseClient


def create_mock_storage_adapter(
    url: str = "https://test.supabase.co",
    service_key: str = "test-key",
    table_name: str = "test_documents"
) -> SupabaseStorageAdapter:
    """Create a storage adapter with a mock Supabase client.
    
    Args:
        url: Mock Supabase URL
        service_key: Mock service key
        table_name: Mock table name
        
    Returns:
        SupabaseStorageAdapter: Adapter configured with mock client
    """
    config = SupabaseConfig(
        url=url,
        service_key=service_key,
        table_name=table_name,
        timeout=30,
        max_retries=3
    )
    
    adapter = SupabaseStorageAdapter(config)
    # Inject the mock client directly
    adapter._client = MockSupabaseClient(config)
    
    return adapter


def create_live_storage_adapter(config: SupabaseConfig) -> SupabaseStorageAdapter:
    """Create a storage adapter for live testing.
    
    Args:
        config: Real Supabase configuration
        
    Returns:
        SupabaseStorageAdapter: Adapter configured for live database
    """
    return SupabaseStorageAdapter(config)