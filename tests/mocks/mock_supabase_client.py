"""
Mock Supabase client for testing purposes.

This module provides mock implementations of Supabase client functionality
for unit and integration testing without requiring actual database connections.
"""

from typing import Any, Dict, List
from src.infrastructure.config.supabase_config import SupabaseConfig


class MockSupabaseClient:
    """Mock Supabase client for testing and development.
    
    This mock simulates Supabase operations for testing purposes.
    In production, this is replaced with the actual Supabase client.
    """
    
    def __init__(self, config: SupabaseConfig):
        """Initialize mock client with configuration.
        
        Args:
            config: Supabase configuration (used for testing behavior)
        """
        self.config = config
        self._data = {}  # In-memory storage for testing
    
    async def insert_records(self, table_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock implementation of record insertion."""
        try:
            if table_name not in self._data:
                self._data[table_name] = []
            
            self._data[table_name].extend(records)
            return {'success': True, 'count': len(records)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def select_records(
        self, 
        table_name: str, 
        filters: Dict[str, Any] = None, 
        order_by: str = None, 
        limit: int = None
    ) -> Dict[str, Any]:
        """Mock implementation of record selection."""
        try:
            if table_name not in self._data:
                return {'success': True, 'data': []}
            
            records = self._data[table_name]
            
            # Apply filters
            if filters:
                filtered_records = []
                for record in records:
                    match = True
                    for key, value in filters.items():
                        if record.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered_records.append(record)
                records = filtered_records
            
            # Apply ordering
            if order_by and records:
                records = sorted(records, key=lambda x: x.get(order_by, 0))
            
            # Apply limit
            if limit:
                records = records[:limit]
            
            return {'success': True, 'data': records}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def select_distinct_documents(
        self, 
        table_name: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Mock implementation of distinct document selection."""
        try:
            if table_name not in self._data:
                return {'success': True, 'data': []}
            
            # Get unique document IDs
            document_ids = set()
            for record in self._data[table_name]:
                if 'document_id' in record:
                    document_ids.add(record['document_id'])
            
            # Apply pagination
            document_ids = list(document_ids)[offset:offset + limit]
            
            return {'success': True, 'data': document_ids}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def delete_records(self, table_name: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation of record deletion."""
        try:
            if table_name not in self._data:
                return {'success': True, 'count': 0}
            
            original_count = len(self._data[table_name])
            
            # Remove matching records
            remaining_records = []
            for record in self._data[table_name]:
                match = True
                for key, value in filters.items():
                    if record.get(key) != value:
                        match = False
                        break
                if not match:
                    remaining_records.append(record)
            
            self._data[table_name] = remaining_records
            deleted_count = original_count - len(remaining_records)
            
            return {'success': True, 'count': deleted_count}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def health_check(self, table_name: str) -> Dict[str, Any]:
        """Mock implementation of health check."""
        try:
            # Check if the configuration looks invalid (for testing purposes)
            if "invalid-url-that-does-not-exist" in self.config.url:
                return {'success': False, 'error': 'Invalid URL configuration'}
            
            # Simple check - just verify we can access the data structure
            if table_name not in self._data:
                self._data[table_name] = []
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def clear_data(self):
        """Clear all mock data (useful for test cleanup)."""
        self._data.clear()
    
    def get_data(self, table_name: str = None) -> Dict[str, Any]:
        """Get mock data for inspection (testing utility)."""
        if table_name:
            return self._data.get(table_name, [])
        return self._data.copy()