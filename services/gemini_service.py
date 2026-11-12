import json
import re
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types

from config import settings
from schemas.ai_analysis import AIAnalysisReport
from utils.logger import logger


FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-3.1-flash-lite",
]


class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.primary_model = settings.GEMINI_MODEL or "gemini-3.5-flash"
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> Optional[genai.Client]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return None
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key != "your_gemini_api_key_here")

    def _get_candidate_models(self) -> List[str]:
        models = [self.primary_model]
        for m in FALLBACK_MODELS:
            if m not in models:
                models.append(m)
        return models

    def generate_market_analysis(
        self,
        current_price: float,
        ticker_24h: Dict[str, Any],
        indicators: Dict[str, Any]
    ) -> AIAnalysisReport:
        """
        Request structured AI analysis and human-friendly forecast from Google Gemini.
        Tries primary model, then falls back to other Flash models if 404 or 503 occurs.
        """
        if not self.is_available():
            raise RuntimeError(
                "Gemini API kaliti sozlanmagan. Iltimos, .env faylida GEMINI_API_KEY ni ko'rsating."
            )

        prompt = f"""
Siz tajribali, professional va samimiy kripto tahlilchisiz. Oddiy odamlarga Bitcoin holatini juda tushunarli, aniq va jonli o'zbek tilida ('odam tilida') tushuntirib berasiz.

BOZOR MA'LUMOTLARI:
- Hozirgi BTC narxi: ${current_price:,.2f}
- 24s ichidagi eng yuqori: ${float(ticker_24h.get('high_price', 0)):,.2f}
- 24s ichidagi eng past: ${float(ticker_24h.get('low_price', 0)):,.2f}
- 24s narx o'zgarishi: {float(ticker_24h.get('price_change_percent', 0)):+.2f}%
- 24s savdo hajmi: {float(ticker_24h.get('volume', 0)):,.2f} BTC

TEXNIK INDIKATORLAR (Python hisoblagan):
- RSI (14): {indicators.get('rsi_14')}
- EMA 20: ${indicators.get('ema_20')} | EMA 50: ${indicators.get('ema_50')} | EMA 200: ${indicators.get('ema_200')}
- MACD: {indicators.get('macd')}
- Pivot darajalari (S/R): {indicators.get('support_resistance')}
- Volatillik: {indicators.get('volatility_pct')}%
- Hajm o'zgarishi: {indicators.get('volume_change_pct'):+.2f}%

TALABLAR:
1. 3 ta vaqt gorizonti uchun ehtimoliy oraliqlarni bering: '1h', '4h', va '24h'.
   - 1h (keyingi 1 soat) narx chegaralarini juda aniq belgilang (lower_price va upper_price).
2. 'human_explanation_uz' maydonida:
   - Aynan KEYINGI 1 SOAT ichida narx qanchaga ko'tarilishi yoki qanchagacha tushishi mumkinligini do'stona, samimiy va jonli o'zbek tilida tushuntiring.
   - Masalan: "Hozir narx $... atrofida. Keyingi 1 soatda ko'pi bilan $... gacha ko'tarilishi (+$...) yoki $... gacha tushishi (-$...) mumkin..." deb sabablarini oddiy tushuntiring (xaridorlar/sotuvchilar holati, RSI, hajm bo'yicha).
3. Javobingiz FAQAT to'g'ri JSON formatida bo'lsin. Hech qanday markdown yoki ortiqcha matn qo'shmang.

SCHEMA:
{{
  "current_price": {current_price},
  "timestamp": "{ticker_24h.get('symbol', 'BTCUSDT')}",
  "horizons": [
    {{
      "forecast_horizon": "1h",
      "market_direction": "bullish",
      "lower_price": {round(current_price * 0.997, 2)},
      "upper_price": {round(current_price * 1.003, 2)},
      "confidence": "medium",
      "reasoning": ["RSI darajasi", "Hajm o'zgarishi"],
      "risks": ["Kutilmagan tebranish"]
    }},
    {{
      "forecast_horizon": "4h",
      "market_direction": "neutral",
      "lower_price": {round(current_price * 0.993, 2)},
      "upper_price": {round(current_price * 1.006, 2)},
      "confidence": "medium",
      "reasoning": ["EMA 20/50 kesishuvi"],
      "risks": ["Qarshilik darajasi"]
    }},
    {{
      "forecast_horizon": "24h",
      "market_direction": "bullish",
      "lower_price": {round(current_price * 0.985, 2)},
      "upper_price": {round(current_price * 1.015, 2)},
      "confidence": "low",
      "reasoning": ["Umumiy trend"],
      "risks": ["Bozor yangiliklari"]
    }}
  ],
  "summary_uz": "Qisqa texnik xulosa.",
  "human_explanation_uz": "Odam tilidagi batafsil va tushunarli 1 soatlik prognoz."
}}
"""

        candidate_models = self._get_candidate_models()
        last_error = None

        for model in candidate_models:
            try:
                logger.info(f"Attempting AI market analysis with model: {model}")
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        response_mime_type="application/json",
                    )
                )

                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\n", "", raw_text)
                    raw_text = re.sub(r"\n```$", "", raw_text)

                parsed_data = json.loads(raw_text)
                report = AIAnalysisReport(**parsed_data)
                logger.info(f"Successfully generated AI report using {model}")
                return report

            except Exception as e:
                logger.warning(f"Model {model} failed: {e}. Trying next fallback...")
                last_error = e
                continue

        logger.error(f"All Gemini models failed: {last_error}")
        raise RuntimeError(f"Gemini AI tahlilini olishda xatolik yuz berdi: {last_error}")


gemini_service = GeminiService()
