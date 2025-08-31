# OncoStaging - Next.js Application

A modern, AI-powered cancer staging assistant built with Next.js, TypeScript, and Tailwind CSS.

## 🚀 Features

- **Advanced OCR Processing**: Extract text from PDF, DOCX, and image files
- **AI-Powered Analysis**: Intelligent medical feature extraction
- **TNM Staging**: Automated cancer staging calculation
- **Interactive Q&A**: Ask questions about your report
- **Modern UI**: Sleek, responsive design with smooth animations
- **Real-time Processing**: Live progress tracking and feedback

## 🛠️ Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI primitives
- **Animations**: Framer Motion
- **OCR**: Tesseract.js
- **PDF Processing**: PDF.js and pdf-parse
- **Document Processing**: Mammoth.js for DOCX files

## 📦 Installation

```bash
# Clone the repository
git clone <repository-url>
cd oncostaging-app

# Install dependencies
npm install

# Run development server
npm run dev
```

## 🏥 Core Functionality

### Document Processing
- Supports PDF, DOCX, and image files
- Advanced OCR with preprocessing
- Text extraction and validation

### Medical Feature Extraction
- Cancer type identification
- Tumor size measurement
- Lymph node involvement
- Metastasis detection
- Confidence scoring

### TNM Staging
- Automated staging calculation
- Support for multiple cancer types:
  - Gallbladder
  - Esophageal
  - Breast
  - Lung
  - Colorectal
  - Head and Neck

### AI Integration
- Question answering system
- Clinical explanations
- Treatment information
- Patient-friendly language

## 🎨 Design Features

- **Responsive Design**: Works on all device sizes
- **Smooth Animations**: Framer Motion for fluid interactions
- **Modern UI**: Clean, medical-grade interface
- **Accessibility**: ARIA compliant components
- **Dark Mode Ready**: Built-in theme support

## 📱 Usage

1. **Upload**: Drag and drop or select your PET/CT report
2. **Process**: Automatic OCR and feature extraction
3. **Review**: View TNM staging and extracted features
4. **Interact**: Ask questions about your report
5. **Download**: Export your analysis report

## ⚠️ Important Notice

This application is for informational purposes only and should not replace professional medical consultation. Always consult with qualified healthcare professionals for medical decisions.

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file:

```bash
# Optional: AI API keys for enhanced analysis
OPENROUTER_API_KEY=your_api_key_here
GOOGLE_VISION_API_KEY=your_google_vision_key
```

### Deployment

```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🧪 Development

```bash
# Run development server
npm run dev

# Run type checking
npm run type-check

# Run linting
npm run lint
```

## 📄 License

MIT License - see LICENSE file for details.