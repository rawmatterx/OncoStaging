# OncoStaging - Refactored Architecture

## Overview

OncoStaging is a cancer staging chatbot application that has been comprehensively refactored to implement modern software engineering best practices. The application processes PET/CT medical reports and provides TNM staging information for various cancer types.

## Architecture Improvements

### 🏗️ **Modular Design**
The monolithic codebase has been split into focused modules:

- **`config.py`** - Centralized configuration management
- **`exceptions.py`** - Custom exception classes for granular error handling
- **`document_processor.py`** - File validation and text extraction
- **`feature_extractor.py`** - Medical feature extraction with validation
- **`staging_engine.py`** - TNM staging algorithms
- **`app_refactored.py`** - MVC pattern implementation

### 🎯 **Key Features**

- **MVC Architecture**: Clear separation of concerns with Controller, View, and Model layers
- **Comprehensive Error Handling**: Custom exceptions with detailed error messages
- **Input Validation**: File type, size, and content validation with security checks
- **Configuration Management**: Environment variable support for flexible deployment
- **Testing Framework**: 66+ unit and integration tests with pytest
- **Performance Optimization**: Caching support and streaming capabilities
- **Security Enhancements**: Input sanitization and file validation

## Supported Cancer Types

- Gallbladder Cancer
- Esophageal Cancer  
- Breast Cancer
- Lung Cancer
- Colorectal Cancer
- Head and Neck Cancer

## Installation & Setup

```bash
# Clone the repository
git clone https://github.com/rawmatterx/OncoStaging.git
cd OncoStaging

# Install dependencies
pip install -r requirements_updated.txt

# Run the refactored application
streamlit run app_refactored.py
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

## Configuration

Set environment variables for customization:

```bash
export MAX_FILE_SIZE_MB=50
export LOG_LEVEL=INFO
export CACHE_ENABLED=true
```

## Technical Improvements Summary

### ✅ **Code Organization**
- Split monolithic files into focused modules
- Implemented proper class-based architecture
- Added abstract base classes for extensibility

### ✅ **Error Handling & Validation**
- Custom exception hierarchy
- Comprehensive input validation
- Graceful error recovery

### ✅ **Testing & Quality**
- 66+ automated tests with 97% pass rate
- Unit and integration test coverage
- Pytest configuration and CI/CD ready

### ✅ **Performance & Security**
- File validation and sanitization
- Caching support for improved performance
- Security-first file handling

### ✅ **User Experience**
- Enhanced UI with confidence scoring
- Better error messages and feedback
- Progress indicators and loading states

## Migration from Original Code

The refactored application maintains backward compatibility while providing enhanced functionality. Users can:

1. Continue using the original `cancer_chatbot_app.py` 
2. Switch to the improved `app_refactored.py` for better performance and features
3. Gradually migrate custom integrations to use the new modular APIs

## Contributing

The modular architecture makes it easy to:
- Add new cancer types by implementing the `CancerStager` interface
- Extend feature extraction with new medical patterns
- Add new document formats by extending `DocumentProcessor`
- Improve staging algorithms with updated medical guidelines

---

**⚠️ Medical Disclaimer**: This application is for educational and research purposes only. Always consult qualified medical professionals for clinical decisions.