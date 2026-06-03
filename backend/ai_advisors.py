import asyncio
import aiohttp
import json
import logging
import os
from .data_loader import DOCS

logger = logging.getLogger(__name__)

def _get_docs_ctx():
    return json.dumps({k: str(v)[:100] if isinstance(v, (dict, list)) else v for k, v in DOCS.items()}, ensure_ascii=False)[:2000]
DOCS_CTX = _get_docs_ctx()

SYSTEM_PROMPTS = {
    "macro": "Bạn là chuyên gia KINH TẾ VĨ MÔ (Macro Advisor).\nNhiệm vụ: Phân tích bối cảnh vĩ mô ảnh hưởng đến khoản đầu tư.\nChuyên về: lãi suất, lạm phát, tỷ giá, GDP, chính sách tiền tệ, địa chính trị.\nPhong cách: Ngắn gọn, thực tế, tập trung vào tác động cụ thể đến nhà đầu tư cá nhân.\nLuôn kết luận bằng khuyến nghị rõ ràng: Nên/Nên tránh/Tăng/Giảm tỷ trọng.\nDữ liệu: " + _get_docs_ctx(),

    "technical": "Bạn là chuyên gia PHÂN TÍCH KỸ THUẬT (Technical Advisor).\nNhiệm vụ: Đánh giá xu hướng giá, tín hiệu mua/bán dựa trên kỹ thuật.\nChuyên về: RSI, MACD, Bollinger Bands, kháng cự/hỗ trợ, khối lượng, mô hình nến.\nPhong cách: Ngắn gọn, dùng số liệu cụ thể, tránh lý thuyết dài dòng.\nLuôn kết luận: Xu hướng ngắn hạn (1-4 tuần) và trung hạn (1-6 tháng) rõ ràng.\nDữ liệu: " + _get_docs_ctx(),

    "fundamental": "Bạn là chuyên gia PHÂN TÍCH CƠ BẢN (Fundamental Advisor).\nNhiệm vụ: Định giá doanh nghiệp dựa trên tài chính và tiềm năng.\nChuyên về: P/E, P/B, ROE, EPS, biên lợi nhuận, tăng trưởng doanh thu, dòng tiền.\nPhong cách: Giọng điệu của Benjamin Graham - tập trung vào biên an toàn và giá trị nội tại.\nLuôn kết luận: Định giá Đắt/Hợp lý/Rẻ kèm lý do cụ thể.\nDữ liệu: " + _get_docs_ctx(),

    "risk": "Bạn là chuyên gia QUẢN TRỊ RỦI RO (Risk Advisor).\nNhiệm vụ: Đánh giá rủi ro tiềm ẩn của quyết định đầu tư.\nChuyên về: drawdown, VaR, thanh khoản, rủi ro tập trung, rủi ro hệ thống, kịch bản xấu nhất.\nPhong cách: Thực tế, thận trọng, luôn có Plan B. Dùng giọng điệu của Nassim Taleb.\nLuôn kết luận: Đánh giá rủi ro (Thấp/Trung bình/Cao) + khuyến nghị giảm thiểu.\nDữ liệu: " + _get_docs_ctx(),
}

async def _call_ollama(session, prompt, question, timeout=30):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    payload = {"model": "qwen3:8b", "messages": messages, "stream": False, "options": {"temperature": 0.7, "max_tokens": 512}}
    try:
        async with session.post("http://localhost:11434/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status == 200:
                data = await r.json()
                return data.get("message", {}).get("content", "").strip()
    except Exception as e:
        logger.warning(f"Ollama error: {e}")
    return None

async def _call_openai(session, prompt, question, api_key, timeout=30):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "gpt-4o-mini", "messages": messages, "temperature": 0.7, "max_tokens": 512}
    try:
        async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status == 200:
                data = await r.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"OpenAI error: {e}")
    return None

async def _call_gemini(session, prompt, question, api_key, timeout=30):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": f"{prompt}\n\nCâu hỏi: {question}"}]}]}
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status == 200:
                data = await r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
    except Exception as e:
        logger.warning(f"Gemini error: {e}")
    return None

async def _run_advisors(session, question, api_backend, api_key):
    tasks = {}
    for role, sp in SYSTEM_PROMPTS.items():
        if api_backend == "openai":
            tasks[role] = _call_openai(session, sp, question, api_key)
        elif api_backend == "gemini":
            tasks[role] = _call_gemini(session, sp, question, api_key)
        else:
            tasks[role] = _call_ollama(session, sp, question)
    results = {}
    for role, task in tasks.items():
        try:
            results[role] = await task
        except Exception as e:
            logger.error(f"Advisor {role} failed: {e}")
            results[role] = None
    return results

def hoi_dong_ai_tu_van(cau_hoi):
    api_backend = os.environ.get("AI_BACKEND", "ollama").lower()
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""
    if api_backend != "ollama" and not api_key:
        api_backend = "ollama"
    try:
        results = asyncio.run(_run_advisors_async(cau_hoi, api_backend, api_key))
        if any(v for v in results.values()):
            return _format_combined(results)
    except Exception as e:
        logger.error(f"Async advisor failed: {e}")
    return None

async def _run_advisors_async(question, api_backend, api_key):
    async with aiohttp.ClientSession() as session:
        return await _run_advisors(session, question, api_backend, api_key)

LABELS = {"macro": "🏛️ VĨ MÔ", "technical": "📈 KỸ THUẬT", "fundamental": "📊 CƠ BẢN", "risk": "🛡️ RỦI RO"}

def _format_combined(results):
    lines = ["## 🤖 HỘI ĐỒNG 4 AI — PHÂN TÍCH ĐA CHIỀU\n"]
    for role in ["macro", "technical", "fundamental", "risk"]:
        content = results.get(role)
        if content:
            lines.append(f"### {LABELS[role]}")
            lines.append(content[:600])
            lines.append("")
    lines.append("---")
    lines.append("*Kết hợp từ 4 chuyên gia AI — công cụ mô phỏng & phân tích dữ liệu lịch sử, không phải khuyến nghị đầu tư.*")
    return "\n".join(lines)
