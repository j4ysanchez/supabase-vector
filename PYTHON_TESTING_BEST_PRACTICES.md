# Python Testing Best Practices: Mock Organization

## The Problem We Fixed

Initially, the `MockSupabaseClient` was defined in the production code file (`src/adapters/secondary/supabase/supabase_storage_adapter.py`). This is an **anti-pattern** that violates several principles:

### ❌ **What Was Wrong:**

1. **Mixing Production and Test Code**: Mock objects belong in test directories, not production code
2. **Violates Single Responsibility**: Production files should only contain production logic
3. **Deployment Bloat**: Mock code gets deployed to production unnecessarily
4. **Maintenance Issues**: Changes to mocks affect production files
5. **Confusing Architecture**: Developers might accidentally use mocks in production

## ✅ **Proper Python Testing Structure**

### **Standard Directory Layout:**
```
project/
├── src/                          # Production code
│   └── adapters/
│       └── supabase_storage_adapter.py
├── tests/                        # All test-related code
│   ├── mocks/                    # Mock implementations
│   │   ├── __init__.py
│   │   └── mock_supabase_client.py
│   ├── factories/                # Test object factories
│   │   ├── __init__.py
│   │   └── storage_factory.py
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── fixtures/                 # Test data/fixtures
```

### **Key Principles:**

1. **Separation of Concerns**: Production code only contains production logic
2. **Test Code Organization**: Mocks, factories, and utilities in dedicated test directories
3. **Dependency Injection**: Use factories to inject mocks into adapters
4. **Clear Boundaries**: Production code should work with real dependencies by default

## **Implementation Details**

### **1. Mock in Test Directory**
```python
# tests/mocks/mock_supabase_client.py
class MockSupabaseClient:
    """Mock Supabase client for testing purposes."""
    
    def __init__(self, config: SupabaseConfig):
        self.config = config
        self._data = {}  # In-memory storage for testing
    
    async def insert_records(self, table_name: str, records: List[Dict[str, Any]]):
        # Mock implementation
        pass
```

### **2. Factory for Test Object Creation**
```python
# tests/factories/storage_factory.py
def create_mock_storage_adapter(url: str, service_key: str, table_name: str):
    """Create a storage adapter with mock client."""
    config = SupabaseConfig(url=url, service_key=service_key, table_name=table_name)
    adapter = SupabaseStorageAdapter(config)
    adapter._client = MockSupabaseClient(config)  # Inject mock
    return adapter
```

### **3. Clean Production Code**
```python
# src/adapters/secondary/supabase/supabase_storage_adapter.py
class SupabaseStorageAdapter(StoragePort):
    async def _get_client(self):
        """Get or create the Supabase client."""
        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self._config.url, self._config.service_key)
            except ImportError:
                raise StorageError("Supabase client not available. Install with: pip install supabase")
        return self._client
```

### **4. Test Usage**
```python
# tests/unit/test_storage_adapter.py
@pytest.fixture
def adapter():
    """Create adapter with mock client."""
    from tests.factories.storage_factory import create_mock_storage_adapter
    return create_mock_storage_adapter("https://test.supabase.co", "test-key", "test_table")
```

## **Comparison with Java**

### **Java Testing Structure:**
```
src/
├── main/java/                    # Production code
│   └── com/example/adapters/
└── test/java/                    # Test code
    ├── com/example/adapters/
    │   └── SupabaseStorageAdapterTest.java
    └── mocks/
        └── MockSupabaseClient.java
```

### **Python Testing Structure:**
```
src/                              # Production code
├── adapters/
│   └── supabase_storage_adapter.py
tests/                            # Test code
├── mocks/
│   └── mock_supabase_client.py
├── factories/
│   └── storage_factory.py
└── unit/
    └── test_supabase_storage_adapter.py
```

**Key Similarities:**
- Both separate production and test code completely
- Both use dedicated directories for mocks and test utilities
- Both inject dependencies rather than hardcoding them

**Python Advantages:**
- More flexible factory pattern with functions
- Dynamic imports allow optional dependencies
- Pytest fixtures provide powerful dependency injection

## **Benefits of This Approach**

### **1. Clean Architecture**
- Production code focuses solely on business logic
- Clear separation between real and mock implementations
- Easy to understand what's production vs. test code

### **2. Maintainability**
- Changes to mocks don't affect production files
- Test utilities are organized and reusable
- Easy to add new mock implementations

### **3. Deployment Safety**
- No test code in production deployments
- Smaller production artifacts
- No risk of accidentally using test code in production

### **4. Testing Flexibility**
- Easy to create different mock configurations
- Factories allow parameterized test setups
- Can easily switch between mock and live testing

## **Common Anti-Patterns to Avoid**

### ❌ **Don't Do This:**
```python
# Production file with embedded mock
class ProductionAdapter:
    def _get_client(self):
        if self.testing:
            return MockClient()  # ❌ Mock in production code
        return RealClient()
```

### ❌ **Don't Do This:**
```python
# Mock in production module
class MockClient:  # ❌ Mock in production file
    pass

class ProductionAdapter:
    pass
```

### ✅ **Do This Instead:**
```python
# Production file - clean
class ProductionAdapter:
    def _get_client(self):
        return RealClient()

# Test factory - separate
def create_test_adapter():
    adapter = ProductionAdapter()
    adapter._client = MockClient()  # Inject mock
    return adapter
```

## **Testing Strategy Summary**

1. **Unit Tests**: Use mocks for all external dependencies
2. **Integration Tests**: Use mocks for complex/expensive dependencies
3. **Live Tests**: Use real dependencies for end-to-end validation
4. **Factories**: Provide easy ways to create test objects with appropriate mocking

This approach ensures clean, maintainable, and professional Python code that follows industry best practices similar to Java and other enterprise languages.