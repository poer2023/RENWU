#!/usr/bin/env python3
"""
Test script for TaskWall v3.0 AI Services

Verifies that all AI services can be imported and basic functionality works.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all AI services can be imported"""
    print("Testing AI service imports...")
    
    try:
        from app.ai import (
            AIServiceBase, AIResult, AIError, AIOperationType,
            NLPService, ClassificationService, SimilarityService,
            PriorityService, DependencyService, WorkloadService,
            VectorDBManager, AIServiceAggregator
        )
        print("✓ All AI services imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_enums():
    """Test AI operation type enums"""
    print("Testing AI enums...")
    
    try:
        from app.ai.base import AIOperationType
        
        operations = [
            AIOperationType.PARSE,
            AIOperationType.CLASSIFY,
            AIOperationType.SIMILARITY,
            AIOperationType.PRIORITY,
            AIOperationType.DEPENDENCY,
            AIOperationType.WORKLOAD
        ]
        
        print(f"✓ AI operation types: {[op.value for op in operations]}")
        return True
    except Exception as e:
        print(f"✗ Enum test failed: {e}")
        return False

def test_model_imports():
    """Test model imports used by AI services"""
    print("Testing model imports...")
    
    try:
        from app.models import (
            Task, PriorityLevel, TaskStatus, DependencyType,
            TaskVector, AIFeedback, AILog, UserPreference
        )
        print("✓ All models imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Model import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic AI service functionality without database"""
    print("Testing basic AI service functionality...")
    
    try:
        from app.ai.base import AIResult, AIOperationType
        
        # Test AIResult creation
        result = AIResult(
            success=True,
            data={"test": "data"},
            confidence=0.8,
            reasoning=["test reasoning"],
            model_used="test"
        )
        
        result_dict = result.to_dict()
        assert result_dict["success"] == True
        assert result_dict["confidence"] == 0.8
        
        print("✓ Basic AI service structures working")
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("TaskWall v3.0 AI Services Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_enums,
        test_model_imports,
        test_basic_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! AI services are ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())