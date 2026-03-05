import json
import logging
from typing import List, Optional

from openai import OpenAI, AsyncOpenAI
from app.ai.classifier import BaseClassifier, ClassificationResult
from app.ai.prompts import build_classification_prompt, CLASSIFICATION_SYSTEM_PROMPT
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenAIClassifier(BaseClassifier):
    """Document classifier using OpenAI GPT models."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.AI_MODEL
        if not self.api_key:
            logger.warning("OpenAI API key not set.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.aclient = AsyncOpenAI(api_key=self.api_key)

    def classify(
        self,
        text: str,
        available_types: List[str],
        clienti_context: Optional[List[dict]] = None,
        skip_client_id: bool = False,
    ) -> ClassificationResult:
        """Classify a document synchronously."""
        prompt = build_classification_prompt(text, available_types, clienti_context, skip_client_id)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model if "gpt" in self.model else "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" },
                temperature=0.1
            )
            
            result_data = json.loads(response.choices[0].message.content)
            return ClassificationResult(
                tipo_documento=result_data.get("tipo_documento", "altro"),
                tipo_documento_raw=result_data.get("tipo_documento_raw", ""),
                confidence=result_data.get("confidence", 0.0),
                macro_categoria=result_data.get("macro_categoria", "altro"),
                anno_competenza=result_data.get("anno_competenza"),
                cliente_suggerito=result_data.get("cliente_suggerito"),
                codice_fiscale=result_data.get("codice_fiscale"),
                partita_iva=result_data.get("partita_iva"),
                contratto_suggerito=result_data.get("contratto_suggerito"),
                raw_response=result_data
            )
        except Exception as e:
            logger.error(f"OpenAI classification failed: {e}")
            return ClassificationResult(
                tipo_documento="altro",
                tipo_documento_raw=f"Error: {str(e)}",
                confidence=0.0
            )

    async def aclassify(
        self,
        text: str,
        available_types: List[str],
        clienti_context: Optional[List[dict]] = None,
        skip_client_id: bool = False,
    ) -> ClassificationResult:
        """Classify a document asynchronously."""
        prompt = build_classification_prompt(text, available_types, clienti_context, skip_client_id)
        
        try:
            response = await self.aclient.chat.completions.create(
                model=self.model if "gpt" in self.model else "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" },
                temperature=0.1
            )
            
            result_data = json.loads(response.choices[0].message.content)
            return ClassificationResult(
                tipo_documento=result_data.get("tipo_documento", "altro"),
                tipo_documento_raw=result_data.get("tipo_documento_raw", ""),
                confidence=result_data.get("confidence", 0.0),
                macro_categoria=result_data.get("macro_categoria", "altro"),
                anno_competenza=result_data.get("anno_competenza"),
                cliente_suggerito=result_data.get("cliente_suggerito"),
                codice_fiscale=result_data.get("codice_fiscale"),
                partita_iva=result_data.get("partita_iva"),
                contratto_suggerito=result_data.get("contratto_suggerito"),
                raw_response=result_data
            )
        except Exception as e:
            logger.error(f"OpenAI async classification failed: {e}")
            return ClassificationResult(
                tipo_documento="altro",
                tipo_documento_raw=f"Error: {str(e)}",
                confidence=0.0
            )
