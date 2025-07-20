from transformers import pipeline
from typing import Optional
import torch

class MedGemmaFeatureExtractor:
    """
    Uses the MedGemma 4B IT model to summarize medical reports or provide staging suggestions.
    """
    def __init__(self, device: Optional[str] = None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.pipe = pipeline(
            "image-text-to-text",
            model="google/medgemma-4b-it",
            torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
            device=self.device
        )

    def summarize_report(self, report_text: str, system_prompt: Optional[str] = None, max_new_tokens: int = 256) -> str:
        """
        Summarize a medical report using MedGemma.
        Args:
            report_text: The raw text content of the medical report.
            system_prompt: Optional system prompt to guide the model (e.g., "You are an expert oncologist.")
            max_new_tokens: Maximum number of tokens to generate.
        Returns:
            str: Model-generated summary or staging suggestion.
        """
        if not system_prompt:
            system_prompt = "You are an expert oncologist. Summarize the following report and suggest likely cancer stage if possible."
        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": report_text}]}
        ]
        output = self.pipe(text=messages, max_new_tokens=max_new_tokens)
        return output[0]["generated_text"][-1]["content"]
