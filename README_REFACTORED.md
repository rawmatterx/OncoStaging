# OncoStaging - Refactored Architecture

[![CI](https://github.com/rawmatterx/OncoStaging/actions/workflows/ci.yml/badge.svg)](https://github.com/rawmatterx/OncoStaging/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)


## 🚀 Technical Architecture Improvements

This document outlines the comprehensive refactoring of the OncoStaging application, implementing modern software engineering practices and improving code quality, maintainability, and reliability.

## 📁 New Project Structure

```
OncoStaging/
├── config.py                    # Configuration management
├── exceptions.py                # Custom exception classes
├── document_processor.py        # Document processing module
├── feature_extractor.py         # Medical feature extraction
├── staging_engine.py           # TNM staging algorithms
├── app_refactored.py           # Refactored main application (MVC)
├── tests/                      # Comprehensive test suite
│   ├── __init__.py
│   ├── test_document_processor.py
│   ├── test_feature_extractor.py
│   └── test_staging_engine.py
├── pytest.ini                 # Test configuration
├── requirements_updated.txt    # Updated dependencies
└── README_REFACTORED.md       # This documentation
```

## 🏗️ Architecture Improvements

### 1. **Modular Design**
- **DocumentProcessor**: Handles file validation, text extraction, and document processing
- **FeatureExtractor**: Extracts medical features with validation and confidence scoring
- **StagingEngine**: Implements TNM staging algorithms with cancer-specific stagers
- **Configuration Management**: Centralized configuration with environment variable support

### 2. **MVC Pattern Implementation**
- **Model**: Data classes (`MedicalFeatures`, `TNMStaging`) and business logic
- **View**: `OncoStagingView` class handling UI rendering and user interactions
- **Controller**: `OncoStagingController` coordinating between model and view

### 3. **Comprehensive Error Handling**
- Custom exception hierarchy for specific error types
- Graceful error recovery and user-friendly error messages
- Comprehensive logging throughout the application

### 4. **Input Validation & Security**
- File type and size validation
- Medical data range validation
- Input sanitization and security checks

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository and create a feature branch: `git checkout -b feature/awesome-feature`.
2. Ensure the test suite passes: `pytest`.
3. Run the linter (`flake8`) and security checks (`bandit`).
4. Commit your changes with clear messages and open a pull request.
5. The CI pipeline will run automatically. A PR is merged once checks pass and at least one review is approved.

Please read `CONTRIBUTING.md` (coming soon) for detailed guidelines.

---

## 🧪 Testing Framework

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Mock Data**: Realistic test scenarios with medical reports
- **Coverage Reporting**: HTML and terminal coverage reports

### Running Tests
```bash
# Install test dependencies
pip install -r requirements_updated.txt

# Run all tests with coverage
pytest
```

## 🔧 Configuration Management

### Environment Variables
```bash
export MAX_FILE_SIZE_MB=50
export LOG_LEVEL=INFO
export CACHE_ENABLED=true
```

## 🛡️ Security Enhancements

- File type validation, size limits, and content validation
- Input sanitization and medical data range checks

## 📊 Performance Optimizations

- File hash-based caching for processed documents
- Streamlit caching for expensive operations

## 🚀 Running the Refactored Application

```bash
pip install -r requirements_updated.txt
streamlit run app_refactored.py
```

## 🎯 Next Steps

- Add CI workflow (`ci.yml`) for automated testing and linting
- Implement caching and API endpoints
- Expand cancer type coverage and ML integration
