"""
Tests for app/utils/serialization.py
"""
import pytest
from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel
from app.utils.serialization import safe_serialize, safe_model_dump


class MockModel(BaseModel):
    """Test model for serialization tests"""
    name: str
    value: int
    optional_field: str = None


class MockNestedModel(BaseModel):
    """Test nested model for serialization tests"""
    test_model: MockModel
    description: str


class MockRecursiveModel(BaseModel):
    """Test model that can cause recursion"""
    name: str
    parent: 'MockRecursiveModel' = None


class TestSafeSerialize:
    """Test cases for safe_serialize function"""
    
    def test_serialize_pydantic_model(self):
        """Test serializing a Pydantic model"""
        model = MockModel(name="test", value=42, optional_field="optional")
        result = safe_serialize(model)
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
        assert result["optional_field"] == "optional"
    
    def test_serialize_datetime(self):
        """Test serializing datetime objects"""
        dt = datetime(2023, 1, 1, 12, 30, 45)
        result = safe_serialize(dt)
        assert result == "2023-01-01T12:30:45"
    
    def test_serialize_list(self):
        """Test serializing lists"""
        data = [1, 2, 3, "string", MockModel(name="test", value=1)]
        result = safe_serialize(data)
        assert isinstance(result, list)
        assert result[0] == 1
        assert result[1] == 2
        assert result[2] == 3
        assert result[3] == "string"
        assert isinstance(result[4], dict)
        assert result[4]["name"] == "test"
        assert result[4]["value"] == 1
    
    def test_serialize_tuple(self):
        """Test serializing tuples"""
        data = (1, 2, 3, "string")
        result = safe_serialize(data)
        assert isinstance(result, list)  # Tuples become lists
        assert result == [1, 2, 3, "string"]
    
    def test_serialize_dict(self):
        """Test serializing dictionaries"""
        data = {
            "string": "value",
            "number": 42,
            "model": MockModel(name="test", value=1),
            "datetime": datetime(2023, 1, 1)
        }
        result = safe_serialize(data)
        assert isinstance(result, dict)
        assert result["string"] == "value"
        assert result["number"] == 42
        assert isinstance(result["model"], dict)
        assert result["model"]["name"] == "test"
        assert result["datetime"] == "2023-01-01T00:00:00"
    
    def test_serialize_nested_structures(self):
        """Test serializing nested structures"""
        data = {
            "models": [
                MockModel(name="model1", value=1),
                MockModel(name="model2", value=2)
            ],
            "timestamps": [
                datetime(2023, 1, 1),
                datetime(2023, 1, 2)
            ],
            "nested": {
                "inner": MockModel(name="inner", value=3)
            }
        }
        result = safe_serialize(data)
        assert isinstance(result, dict)
        assert len(result["models"]) == 2
        assert isinstance(result["models"][0], dict)
        assert result["models"][0]["name"] == "model1"
        assert len(result["timestamps"]) == 2
        assert result["timestamps"][0] == "2023-01-01T00:00:00"
        assert isinstance(result["nested"]["inner"], dict)
        assert result["nested"]["inner"]["name"] == "inner"
    
    def test_serialize_object_with_dict(self):
        """Test serializing object with __dict__ attribute"""
        class TestObject:
            def __init__(self):
                self.name = "test"
                self.value = 42
        
        obj = TestObject()
        result = safe_serialize(obj)
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
    
    def test_serialize_primitive_types(self):
        """Test serializing primitive types"""
        assert safe_serialize("string") == "string"
        assert safe_serialize(42) == 42
        assert safe_serialize(3.14) == 3.14
        assert safe_serialize(True) is True
        assert safe_serialize(None) is None
    
    def test_serialize_none(self):
        """Test serializing None"""
        result = safe_serialize(None)
        assert result is None
    
    def test_serialize_empty_structures(self):
        """Test serializing empty structures"""
        assert safe_serialize([]) == []
        assert safe_serialize({}) == {}
        assert safe_serialize(()) == []
    
    def test_serialize_mixed_types(self):
        """Test serializing mixed types in complex structure"""
        data = {
            "string": "test",
            "number": 42,
            "boolean": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "model": MockModel(name="test", value=1),
            "datetime": datetime(2023, 1, 1)
        }
        result = safe_serialize(data)
        assert isinstance(result, dict)
        assert result["string"] == "test"
        assert result["number"] == 42
        assert result["boolean"] is True
        assert result["none"] is None
        assert result["list"] == [1, 2, 3]
        assert result["dict"] == {"key": "value"}
        assert isinstance(result["model"], dict)
        assert result["datetime"] == "2023-01-01T00:00:00"


class TestSafeModelDump:
    """Test cases for safe_model_dump function"""
    
    def test_model_dump_pydantic_model(self):
        """Test dumping a Pydantic model with model_dump method"""
        model = MockModel(name="test", value=42, optional_field="optional")
        result = safe_model_dump(model)
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
        assert result["optional_field"] == "optional"
    
    def test_model_dump_pydantic_model_with_kwargs(self):
        """Test dumping a Pydantic model with kwargs"""
        model = MockModel(name="test", value=42, optional_field="optional")
        result = safe_model_dump(model, exclude={"optional_field"})
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
        assert "optional_field" not in result
    
    def test_model_dump_legacy_dict_method(self):
        """Test dumping a model with legacy dict method"""
        class LegacyModel:
            def __init__(self):
                self.name = "test"
                self.value = 42
            
            def dict(self, **kwargs):
                return {"name": self.name, "value": self.value}
        
        model = LegacyModel()
        result = safe_model_dump(model)
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
    
    def test_model_dump_dict(self):
        """Test dumping a dictionary"""
        data = {"key": "value", "number": 42}
        result = safe_model_dump(data)
        assert result == data
        assert result is data  # Should return the same object
    
    def test_model_dump_object_with_dict(self):
        """Test dumping an object with __dict__ attribute"""
        class TestObject:
            def __init__(self):
                self.name = "test"
                self.value = 42
        
        obj = TestObject()
        result = safe_model_dump(obj)
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
    
    def test_model_dump_other_object(self):
        """Test dumping other types of objects"""
        # Test with a simple object that can be converted to dict
        result = safe_model_dump(42)
        assert result == {"value": 42}
        
        result = safe_model_dump("string")
        assert result == {"value": "string"}
        
        result = safe_model_dump([1, 2, 3])
        assert result == {"value": [1, 2, 3]}
    
    def test_model_dump_none(self):
        """Test dumping None"""
        result = safe_model_dump(None)
        assert result == {"value": None}
    
    def test_model_dump_nested_model(self):
        """Test dumping nested Pydantic models"""
        inner_model = MockModel(name="inner", value=1)
        outer_model = MockNestedModel(test_model=inner_model, description="nested")
        result = safe_model_dump(outer_model)
        assert isinstance(result, dict)
        assert result["description"] == "nested"
        assert isinstance(result["test_model"], dict)
        assert result["test_model"]["name"] == "inner"
        assert result["test_model"]["value"] == 1
    
    def test_model_dump_with_exclude_kwargs(self):
        """Test dumping with exclude kwargs"""
        model = MockModel(name="test", value=42, optional_field="optional")
        result = safe_model_dump(model, exclude={"optional_field"})
        assert "name" in result
        assert "value" in result
        assert "optional_field" not in result
    
    def test_model_dump_with_include_kwargs(self):
        """Test dumping with include kwargs"""
        model = MockModel(name="test", value=42, optional_field="optional")
        result = safe_model_dump(model, include={"name"})
        assert "name" in result
        assert result["name"] == "test"
        assert "value" not in result
        assert "optional_field" not in result
    
    def test_model_dump_with_by_alias_kwargs(self):
        """Test dumping with by_alias kwargs"""
        model = MockModel(name="test", value=42, optional_field="optional")
        result = safe_model_dump(model, by_alias=True)
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
    
    def test_model_dump_error_handling(self):
        """Test that safe_model_dump handles errors gracefully"""
        # Test with an object that doesn't have model_dump or dict methods
        class ProblematicObject:
            def __init__(self):
                self.name = "test"
                # This will cause an error if we try to call dict() on it
        
        obj = ProblematicObject()
        # This should not raise an exception
        result = safe_model_dump(obj)
        assert isinstance(result, dict)
        assert result["name"] == "test"


class TestSerializationIntegration:
    """Integration tests for serialization functions"""
    
    def test_safe_serialize_with_safe_model_dump(self):
        """Test that safe_serialize uses safe_model_dump for Pydantic models"""
        model = MockModel(name="test", value=42)
        result = safe_serialize(model)
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
    
    def test_complex_nested_serialization(self):
        """Test serializing complex nested structures"""
        data = {
            "models": [
                MockModel(name="model1", value=1),
                MockModel(name="model2", value=2)
            ],
            "timestamps": [
                datetime(2023, 1, 1),
                datetime(2023, 1, 2)
            ],
            "nested": {
                "inner": MockNestedModel(
                    test_model=MockModel(name="inner", value=3),
                    description="nested description"
                )
            },
            "primitives": {
                "string": "test",
                "number": 42,
                "boolean": True,
                "none": None
            }
        }
        result = safe_serialize(data)
        assert isinstance(result, dict)
        assert len(result["models"]) == 2
        assert isinstance(result["models"][0], dict)
        assert result["models"][0]["name"] == "model1"
        assert len(result["timestamps"]) == 2
        assert result["timestamps"][0] == "2023-01-01T00:00:00"
        assert isinstance(result["nested"]["inner"], dict)
        assert result["nested"]["inner"]["description"] == "nested description"
        assert isinstance(result["nested"]["inner"]["test_model"], dict)
        assert result["nested"]["inner"]["test_model"]["name"] == "inner"
        assert result["primitives"]["string"] == "test"
        assert result["primitives"]["number"] == 42
        assert result["primitives"]["boolean"] is True
        assert result["primitives"]["none"] is None
    
    def test_serialization_preserves_data_types(self):
        """Test that serialization preserves appropriate data types"""
        data = {
            "string": "test",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"key": "value"}
        }
        result = safe_serialize(data)
        assert isinstance(result["string"], str)
        assert isinstance(result["integer"], int)
        assert isinstance(result["float"], float)
        assert isinstance(result["boolean"], bool)
        assert result["none"] is None
        assert isinstance(result["list"], list)
        assert isinstance(result["dict"], dict)
