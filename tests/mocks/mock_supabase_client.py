"""
Mock Supabase client for testing purposes.

This module provides mock implementations of Supabase client functionality
for unit and integration testing without requiring actual database connections.
"""

from typing import Any, Dict, List
from src.infrastructure.config.supabase_config import SupabaseConfig


class MockSupabaseResponse:
    """Mock response object that mimics Supabase response structure."""
    
    def __init__(self, data=None, count=None, error=None):
        self.data = data
        self.count = count
        self.error = error


class MockSupabaseTable:
    """Mock table object that mimics Supabase table operations."""
    
    def __init__(self, table_name: str, storage: dict):
        self.table_name = table_name
        self.storage = storage
        self._query_filters = {}
        self._query_order = None
        self._query_limit = None
        self._query_select = "*"
    
    def select(self, columns="*", count=None):
        """Mock select operation."""
        self._query_select = columns
        self._query_count = count
        return self
    
    def insert(self, records):
        """Mock insert operation."""
        if self.table_name not in self.storage:
            self.storage[self.table_name] = []
        
        if isinstance(records, dict):
            records = [records]
        
        self.storage[self.table_name].extend(records)
        # Store the records for later execution
        self._insert_records = records
        return self
    
    def eq(self, column, value):
        """Mock equality filter."""
        self._query_filters[column] = value
        return self
    
    def order(self, column, desc=False):
        """Mock order operation."""
        self._query_order = (column, desc)
        return self
    
    def limit(self, count):
        """Mock limit operation."""
        self._query_limit = count
        return self
    
    def delete(self):
        """Mock delete operation."""
        return self
    
    def execute(self):
        """Execute the query and return results."""
        # Handle insert operations
        if hasattr(self, '_insert_records'):
            return MockSupabaseResponse(data=self._insert_records)
        
        if self.table_name not in self.storage:
            return MockSupabaseResponse(data=[])
        
        records = self.storage[self.table_name][:]
        
        # Apply filters
        for column, value in self._query_filters.items():
            if '->' in column:  # JSON query like 'metadata->>document_id'
                json_path = column.split('->>')
                if len(json_path) == 2:
                    field, key = json_path
                    records = [r for r in records if r.get(field, {}).get(key) == value]
            else:
                records = [r for r in records if r.get(column) == value]
        
        # Apply ordering
        if self._query_order:
            column, desc = self._query_order
            records = sorted(records, key=lambda x: x.get(column, 0), reverse=desc)
        
        # Apply limit
        if self._query_limit:
            records = records[:self._query_limit]
        
        # For delete operations, remove the records
        if hasattr(self, '_is_delete'):
            original_count = len(self.storage[self.table_name])
            # Remove matching records
            remaining = []
            for record in self.storage[self.table_name]:
                should_delete = True
                for column, value in self._query_filters.items():
                    if '->' in column:
                        json_path = column.split('->>')
                        if len(json_path) == 2:
                            field, key = json_path
                            if record.get(field, {}).get(key) != value:
                                should_delete = False
                                break
                    else:
                        if record.get(column) != value:
                            should_delete = False
                            break
                if not should_delete:
                    remaining.append(record)
            
            deleted_records = [r for r in self.storage[self.table_name] if r not in remaining]
            self.storage[self.table_name] = remaining
            return MockSupabaseResponse(data=deleted_records)
        
        # For count queries
        if self._query_select == "count" or hasattr(self, '_query_count') and self._query_count:
            return MockSupabaseResponse(data=[], count=len(records))
        
        return MockSupabaseResponse(data=records)
    
    def delete(self):
        """Mark this as a delete operation."""
        self._is_delete = True
        return self


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
    
    def table(self, table_name: str):
        """Get a table interface."""
        return MockSupabaseTable(table_name, self._data)

    
    def clear_data(self):
        """Clear all mock data (useful for test cleanup)."""
        self._data.clear()
    
    def get_data(self, table_name: str = None) -> Dict[str, Any]:
        """Get mock data for inspection (testing utility)."""
        if table_name:
            return self._data.get(table_name, [])
        return self._data.copy()