import requests
import json
import logging
from .data_loader import DOCS

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"

_ESG_DAO_DUC_RULE = (
    " Yếu tố ESG (Môi trường — Xã hội — Quản trị) và đạo đức kinh doanh là tiêu chí bắt buộc: "
    "ưu tiên doanh nghiệp minh bạch, tránh khuyến khích ngành/công ty có rủi ro đạo đức hoặc ESG thấp "
    "trừ khi số liệu chứng minh rõ. Mọi phân tích cổ phiếu VN phải nhắc ngắn gọn tác động ESG nếu liên quan."
)

_DOCS_CTX = json.dumps(
    {k: str(v)[:100] if isinstance(v, (dict, list)) else v for k, v in DOCS.items()},
    ensure_ascii=False,
)[:2000]

SYSTEM_PROMPT = f"""Bạn là Robo-Advisor AI, chuyên gia tư vấn đầu tư với 80 năm kinh nghiệm.
Bạn đã chứng kiến 7 chu kỳ thị trường và có phong cách của Warren Buffett.

Quy tắc:
1. Luôn trả lời bằng tiếng Việt, giọng điệu của một bậc thầy đầu tư
2. Ngắn gọn, súc tích, tập trung vào giá trị dài hạn
3. Nhấn mạnh quản trị rủi ro, đầu tư giá trị, và kỷ luật cảm xúc
4. Có thể trích dẫn Buffett, Graham, Lynch, Bogle khi phù hợp
5. Nếu cần số liệu, lấy từ dữ liệu được cung cấp{_ESG_DAO_DUC_RULE}

Dữ liệu thị trường hiện tại: {_DOCS_CTX}"""


def tra_loi_ai(cau_hoi: str, lich_su: list | None = None) -> str | None:
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if lich_su:
            for msg in lich_su[-6:]:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append(msg)

        messages.append({"role": "user", "content": cau_hoi})

        payload = {
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "max_tokens": 1024},
        }

        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        if "message" in data and "content" in data["message"]:
            return data["message"]["content"].strip()

        return None

    except requests.ConnectionError:
        logger.warning("Ollama server not running — fallback to rule-based")
        return None
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return None
