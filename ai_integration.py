"""
AI Model Integration module for OncoStaging application.
Handles integration with OpenRouter API for Gemma and other models.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import httpx
import streamlit as st
from datetime import datetime

from config import ERROR_MESSAGES
from exceptions import OncoStagingError

logger = logging.getLogger(__name__)


class AIIntegrationError(OncoStagingError):
    """Raised when AI integration fails."""
    pass


@dataclass
class AIResponse:
    """Data class for AI model responses."""
    content: str
    model: str
    usage: Dict[str, int]
    response_time: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class OpenRouterClient:
    """Client for OpenRouter API integration."""
    
    # Available models
    MODELS = {
        "deepseek-chat": "deepseek/deepseek-chat-v3-0324:free",
        "gemma-7b": "google/gemma-7b-it:free",
        "gemma-2b": "google/gemma-2b-it:free",
        "llama-3-8b": "meta-llama/llama-3-8b-instruct:free",
        "mistral-7b": "mistralai/mistral-7b-instruct:free",
        "claude-3-haiku": "anthropic/claude-3-haiku",
        "gpt-3.5-turbo": "openai/gpt-3.5-turbo"
    }
    
    # Model-specific parameters
    MODEL_PARAMS = {
        "deepseek/deepseek-chat-v3-0324:free": {
            "max_tokens": 2048,
            "temperature": 0.7,
            "top_p": 0.95
        },
        "google/gemma-7b-it:free": {
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.95
        },
        "google/gemma-2b-it:free": {
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.95
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or "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"
        if not self.api_key:
            raise AIIntegrationError(
                "OpenRouter API key not found. Please set OPENROUTER_API_KEY environment variable."
            )
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://oncostaging.app",  # Optional
            "X-Title": "OncoStaging Medical Assistant"  # Optional
        }
        
        # Initialize HTTP client with timeout
        self.client = httpx.Client(timeout=30.0)
    
    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()
    
    def _get_model_params(self, model_id: str) -> Dict[str, Any]:
        """Get model-specific parameters."""
        return self.MODEL_PARAMS.get(model_id, {
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.95
        })
    
    def create_medical_prompt(self, context: str, query: str) -> str:
        """
        Create a medical-focused prompt for the AI model.
        
        Args:
            context: Medical report context
            query: User's question
            
        Returns:
            Formatted prompt
        """
        prompt = f"""You are a medical AI assistant. Please answer based on the following medical report and question.

Medical Report:
{context}

Question: {query}

Instructions:
1. Answer only based on the provided information
2. Explain medical terminology in simple language
3. Provide only confirmed information, do not assume
4. Be helpful and compassionate for the patient
5. Always remind that this is for informational purposes only

Answer:"""
        
        return prompt
    
    @st.cache_data(ttl=3600)
    def query_model(_self, 
                   prompt: str, 
                   model: str = "deepseek-chat",
                   system_prompt: Optional[str] = None,
                   **kwargs) -> AIResponse:
        """
        Query an AI model through OpenRouter.
        
        Args:
            prompt: The user prompt
            model: Model identifier (e.g., "gemma-7b")
            system_prompt: Optional system prompt
            **kwargs: Additional model parameters
            
        Returns:
            AIResponse object with model's response
            
        Raises:
            AIIntegrationError: If API call fails
        """
        start_time = time.time()
        
        try:
            # Get model ID
            model_id = _self.MODELS.get(model)
            if not model_id:
                raise AIIntegrationError(f"অপরিচিত মডেল: {model}")
            
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Get model parameters
            params = _self._get_model_params(model_id)
            params.update(kwargs)  # Allow override
            
            # Prepare request payload
            payload = {
                "model": model_id,
                "messages": messages,
                **params
            }
            
            logger.info(f"Querying model: {model_id}")
            
            # Make API request
            response = _self.client.post(
                f"{_self.base_url}/chat/completions",
                headers=_self.headers,
                json=payload
            )
            
            # Check for errors
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                raise AIIntegrationError(f"API Error ({response.status_code}): {error_msg}")
            
            # Parse response
            data = response.json()
            
            # Extract content
            content = data['choices'][0]['message']['content']
            usage = data.get('usage', {})
            
            response_time = time.time() - start_time
            
            ai_response = AIResponse(
                content=content,
                model=model_id,
                usage=usage,
                response_time=response_time,
                timestamp=datetime.now()
            )
            
            logger.info(f"Model response received in {response_time:.2f}s")
            return ai_response
            
        except httpx.TimeoutException:
            raise AIIntegrationError("API call timed out. Please try again.")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise AIIntegrationError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in AI query: {e}")
            raise AIIntegrationError(f"AI model error: {str(e)}")
    
    def analyze_medical_report(self, 
                             report_text: str,
                             extracted_features: Dict[str, Any],
                             staging_result: Dict[str, Any]) -> AIResponse:
        """
        Analyze medical report using AI model.
        
        Args:
            report_text: Original report text
            extracted_features: Extracted medical features
            staging_result: TNM staging results
            
        Returns:
            AI analysis response
        """
        system_prompt = """You are an experienced oncologist. Your role is to:
1. Analyze medical reports
2. Verify TNM staging
3. Provide clear explanations for patients
4. Provide general treatment information

Always remember: Remind patients to consult their doctor for final medical decisions."""
        
        prompt = f"""Please review the following medical report and analysis:

Report Summary:
- Cancer Type: {extracted_features.get('cancer_type', 'Unknown')}
- Tumor Size: {extracted_features.get('tumor_size_cm', 0)}cm
- Lymph Nodes: {extracted_features.get('lymph_nodes_involved', 0)}
- Metastasis: {'Yes' if extracted_features.get('distant_metastasis') else 'No'}

TNM Staging:
- T: {staging_result.get('T', 'Tx')}
- N: {staging_result.get('N', 'Nx')}
- M: {staging_result.get('M', 'Mx')}
- Stage: {staging_result.get('Stage', 'Unknown')}

Please:
1. Verify if this staging is correct
2. Explain in simple language for the patient
3. Provide information about possible treatment options
4. Recommend next steps"""
        
        return self.query_model(
            prompt=prompt,
            model="deepseek-chat",
            system_prompt=system_prompt,
            temperature=0.6  # Lower temperature for medical accuracy
        )
    
    def answer_patient_question(self,
                              question: str,
                              context: Dict[str, Any],
                              model: str = "deepseek-chat") -> AIResponse:
        """
        Answer patient questions about their report.
        
        Args:
            question: Patient's question
            context: Medical context (features, staging, etc.)
            model: AI model to use
            
        Returns:
            AI response
        """
        system_prompt = "You are a helpful medical AI assistant who answers patient questions. Use simple language and be compassionate."
        
        context_str = f"""
Cancer Type: {context.get('cancer_type', 'Unknown')}
Stage: {context.get('stage', 'Unknown')}
Treatment: {context.get('treatment', 'No information')}
"""
        
        prompt = self.create_medical_prompt(context_str, question)
        
        return self.query_model(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt
        )
    
    def generate_patient_report(self,
                              features: Dict[str, Any],
                              staging: Dict[str, Any],
                              language: str = "bn") -> AIResponse:
        """
        Generate a comprehensive patient report.
        
        Args:
            features: Extracted features
            staging: Staging results
            language: Report language (bn for Bengali, en for English)
            
        Returns:
            Generated report
        """
        lang_prompt = "in Bengali" if language == "bn" else "in English"
        
        prompt = f"""Create a comprehensive patient report based on the following information {lang_prompt}:

Patient Information:
- Cancer: {features.get('cancer_type')}
- Tumor: {features.get('tumor_size_cm')}cm
- TNM: T{staging.get('T')} N{staging.get('N')} M{staging.get('M')}
- Stage: {staging.get('Stage')}

Include in the report:
1. Diagnosis summary
2. Stage explanation
3. General treatment approaches
4. Next steps
5. Patient recommendations

Report format: Professional but easy to understand"""
        
        return self.query_model(
            prompt=prompt,
            model="deepseek-chat",
            temperature=0.5,
            max_tokens=1024
        )
    
    def get_model_list(self) -> List[Dict[str, str]]:
        """Get list of available models with details."""
        models = []
        for name, model_id in self.MODELS.items():
            models.append({
                "name": name,
                "model_id": model_id,
                "free": ":free" in model_id,
                "provider": model_id.split("/")[0]
            })
        return models
    
    def check_api_status(self) -> Tuple[bool, str]:
        """
        Check if OpenRouter API is accessible.
        
        Returns:
            Tuple of (is_available, message)
        """
        try:
            response = self.client.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=5.0
            )
            
            if response.status_code == 200:
                return True, "API is active and working"
            else:
                return False, f"API error: {response.status_code}"
                
        except Exception as e:
            return False, f"Connection error: {str(e)}"


class MedicalAIAssistant:
    """High-level medical AI assistant using OpenRouter."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the medical AI assistant."""
        self.client = OpenRouterClient(api_key)
        self.conversation_history: List[Dict[str, Any]] = []
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_treatment_recommendations(self,
                                    cancer_type: str,
                                    stage: str,
                                    additional_info: Optional[Dict] = None) -> str:
        """
        Get AI-powered treatment recommendations.
        
        Args:
            cancer_type: Type of cancer
            stage: Cancer stage
            additional_info: Additional medical information
            
        Returns:
            Treatment recommendations
        """
        prompt = f"""
For {cancer_type} cancer Stage {stage}, according to the latest treatment guidelines:

1. What is the first-line treatment?
2. What are the possible side effects?
3. What is the success rate?
4. Provide lifestyle recommendations

Follow NCCN and international guidelines.
"""
        
        response = self.client.query_model(
            prompt=prompt,
            model="deepseek-chat",
            temperature=0.3  # Low temperature for factual accuracy
        )
        
        self.add_to_history("assistant", response.content)
        return response.content
    
    def explain_medical_terms(self, terms: List[str], context: str = "") -> Dict[str, str]:
        """
        Explain medical terms in simple language.
        
        Args:
            terms: List of medical terms
            context: Optional context
            
        Returns:
            Dictionary of term explanations
        """
        explanations = {}
        
        for term in terms:
            prompt = f"""
Provide a simple English explanation of the medical term '{term}'.
{f'Context: {context}' if context else ''}

Include in the explanation:
- Simple definition
- Why it's important
- What it means for the patient
"""
            
            response = self.client.query_model(
                prompt=prompt,
                model="deepseek-chat",  # Use deepseek for consistency
                max_tokens=200
            )
            
            explanations[term] = response.content
        
        return explanations
    
    def generate_qa_pairs(self, medical_context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate common Q&A pairs based on medical context.
        
        Args:
            medical_context: Medical report context
            
        Returns:
            List of Q&A pairs
        """
        prompt = f"""
Based on the following medical context, create 5 common questions and answers:

Cancer: {medical_context.get('cancer_type')}
Stage: {medical_context.get('stage')}

Answer in JSON format:
[{{"question": "Question", "answer": "Answer"}}, ...]
"""
        
        response = self.client.query_model(
            prompt=prompt,
            model="deepseek-chat",
            temperature=0.7
        )
        
        try:
            # Parse JSON response
            qa_pairs = json.loads(response.content)
            return qa_pairs
        except json.JSONDecodeError:
            logger.error("Failed to parse Q&A JSON response")
            return []
