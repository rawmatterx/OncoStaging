# OncoStaging AI Integration Guide

## 🤖 OpenRouter Integration

OncoStaging এখন OpenRouter API এর মাধ্যমে বিভিন্ন AI model (Gemma, LLaMA, Mistral ইত্যাদি) সাথে integrate করা হয়েছে।

## 🚀 সেটআপ

### 1. API Key পান

1. [OpenRouter](https://openrouter.ai) এ যান
2. একটি একাউন্ট তৈরি করুন
3. [API Keys](https://openrouter.ai/keys) পেজ থেকে key generate করুন

### 2. Environment Variable সেট করুন

```bash
# .env ফাইল তৈরি করুন
cp .env.example .env

# আপনার API key যোগ করুন
OPENROUTER_API_KEY=your_api_key_here
```

### 3. Dependencies ইনস্টল করুন

```bash
pip install -r requirements_updated.txt
```

## 📊 Features

### AI-Powered Analysis
- **Medical Report Analysis**: রিপোর্ট বিশ্লেষণ এবং validation
- **Treatment Recommendations**: AI-based চিকিৎসা পরামর্শ
- **Q&A Support**: রোগীর প্রশ্নের উত্তর
- **Report Generation**: Comprehensive patient reports

### Supported Models
- **Google Gemma** (7B, 2B) - Free
- **Meta LLaMA 3** (8B) - Free
- **Mistral** (7B) - Free
- **Claude 3 Haiku** - Paid
- **GPT-3.5 Turbo** - Paid

## 🔧 Usage

### Basic Usage

```python
from ai_integration import MedicalAIAssistant

# Initialize
assistant = MedicalAIAssistant()

# Get treatment recommendations
recommendations = assistant.get_treatment_recommendations(
    cancer_type="breast",
    stage="II"
)

# Answer patient questions
answer = assistant.client.answer_patient_question(
    "What does Stage II mean?",
    context={"cancer_type": "breast", "stage": "II"}
)
```

### In Streamlit App

```bash
# Run the refactored app with AI support
streamlit run app_refactored.py
```

## 🛡️ Security & Privacy

- API keys কখনো commit করবেন না
- Patient data locally process হয়
- AI responses medical advice নয়, শুধু information

## 💡 Tips

1. **Free Models**: শুরুতে free models (Gemma, LLaMA) ব্যবহার করুন
2. **Rate Limits**: Free tier এ rate limits আছে
3. **Response Quality**: Medical accuracy এর জন্য temperature কম রাখুন
4. **Caching**: Responses automatically cache হয়

## 🐛 Troubleshooting

### API Key Error
```
AIIntegrationError: OpenRouter API key না পাওয়া গেছে
```
**সমাধান**: `.env` ফাইলে `OPENROUTER_API_KEY` সেট করুন

### Network Error
```
AIIntegrationError: নেটওয়ার্ক ত্রুটি
```
**সমাধান**: Internet connection এবং API status চেক করুন

### Model Not Available
```
AIIntegrationError: অপরিচিত মডেল
```
**সমাধান**: Supported model list থেকে model নির্বাচন করুন

## 📚 API Documentation

বিস্তারিত API documentation:
- [OpenRouter Docs](https://openrouter.ai/docs)
- [Model List](https://openrouter.ai/models)
- [Pricing](https://openrouter.ai/pricing)

## 🤝 Contributing

AI integration improve করতে:
1. নতুন models যোগ করুন
2. Better prompts লিখুন
3. Error handling improve করুন
4. Medical accuracy বাড়ান
