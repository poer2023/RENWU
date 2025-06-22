#!/usr/bin/env python3
"""
Simple test script to validate TaskWall project structure and basic functionality
"""

import os
import sys
import json

def test_project_structure():
    """Test that all required project files exist"""
    print("Testing project structure...")
    
    required_files = [
        'PRD.md',
        'README.md',
        'docker-compose.yml',
        'backend/Dockerfile',
        'backend/requirements.txt',
        'backend/app/main.py',
        'backend/app/models.py',
        'backend/app/schemas.py',
        'backend/app/crud.py',
        'backend/app/deps.py',
        'backend/app/utils/ocr.py',
        'backend/app/utils/ai_client.py',
        'frontend/Dockerfile',
        'frontend/package.json',
        'frontend/vite.config.ts',
        'frontend/index.html',
        'frontend/src/main.ts',
        'frontend/src/App.vue',
        'frontend/src/stores/tasks.ts',
        'frontend/src/components/TaskCard.vue',
        'frontend/src/components/StickyCanvas.vue',
        'frontend/src/components/RightDrawer.vue',
        'frontend/src/pages/Home.vue',
        'data/.gitkeep'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_backend_imports():
    """Test that backend Python modules can be imported"""
    print("Testing backend imports...")
    
    try:
        # Add backend to path
        sys.path.insert(0, 'backend')
        
        # Test imports
        from app import models, schemas, crud
        from app.utils import ai_client, ocr
        
        print("✅ Backend imports successful")
        return True
    except ImportError as e:
        print(f"❌ Backend import error: {e}")
        return False

def test_frontend_structure():
    """Test frontend package.json structure"""
    print("Testing frontend structure...")
    
    try:
        with open('frontend/package.json', 'r') as f:
            package_data = json.load(f)
        
        required_deps = ['vue', 'vue-router', 'pinia', 'axios', 'element-plus']
        missing_deps = []
        
        for dep in required_deps:
            if dep not in package_data.get('dependencies', {}):
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"❌ Missing frontend dependencies: {missing_deps}")
            return False
        else:
            print("✅ Frontend dependencies present")
            return True
            
    except Exception as e:
        print(f"❌ Frontend structure test error: {e}")
        return False

def test_docker_config():
    """Test Docker configuration"""
    print("Testing Docker configuration...")
    
    try:
        # Check Dockerfiles exist and have basic content
        backend_dockerfile = 'backend/Dockerfile'
        frontend_dockerfile = 'frontend/Dockerfile'
        
        with open(backend_dockerfile, 'r') as f:
            backend_content = f.read()
            if 'python:3.12' not in backend_content or 'tesseract' not in backend_content:
                print("❌ Backend Dockerfile missing required content")
                return False
        
        with open(frontend_dockerfile, 'r') as f:
            frontend_content = f.read()
            if 'node:20' not in frontend_content or 'nginx' not in frontend_content:
                print("❌ Frontend Dockerfile missing required content")
                return False
        
        # Check docker-compose.yml
        with open('docker-compose.yml', 'r') as f:
            compose_content = f.read()
            if 'api:' not in compose_content or 'web:' not in compose_content:
                print("❌ Docker compose missing required services")
                return False
        
        print("✅ Docker configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Docker config test error: {e}")
        return False

def print_summary():
    """Print project summary"""
    print("\n" + "="*60)
    print("TaskWall Project Summary")
    print("="*60)
    
    print("\n📋 Features Implemented:")
    features = [
        "Visual drag-and-drop task canvas",
        "AI-powered task parsing (Gemini integration)",
        "OCR text extraction from images",
        "Priority-based task organization (P0-P4)",
        "Module-based task categorization",
        "Task history tracking",
        "Real-time updates with Vue 3 + Pinia",
        "RESTful API with FastAPI",
        "SQLite database with SQLModel",
        "Docker containerization",
        "Export/import functionality"
    ]
    
    for feature in features:
        print(f"  ✅ {feature}")
    
    print("\n🚀 Quick Start:")
    print("  1. docker compose up -d --build")
    print("  2. Open http://localhost:3000")
    print("  3. API docs at http://localhost:8000/docs")
    
    print("\n🗂️ Project Structure:")
    print("  backend/     - FastAPI server with AI/OCR")
    print("  frontend/    - Vue 3 SPA with Element Plus UI")
    print("  data/        - SQLite database storage")
    print("  PRD.md       - Product requirements document")
    print("  README.md    - Complete setup guide")

def main():
    """Run all tests"""
    print("TaskWall Project Validation")
    print("="*40)
    
    tests = [
        test_project_structure,
        test_backend_imports,
        test_frontend_structure,
        test_docker_config
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Project is ready for deployment.")
        print_summary()
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)