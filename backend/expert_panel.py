import asyncio
import aiohttp
import json
import logging
import os

logger = logging.getLogger(__name__)

_CHAIRMAN_ATTEMPTED = False

EXPERTS = [
    {
        "id": "buffett",
        "name": "Warren Buffett",
        "title": "Huyền thoại Đầu tư Giá trị",
        "model": "llama-3.3-70b-versatile",
        "backend": "groq",
        "color": "#4CAF50",
        "prompt": (
            "Bạn là Warren Buffett, huyền thoại đầu tư giá trị 94 tuổi, được mệnh danh là 'Nhà hiền triết xứ Omaha'. "
            "Bạn nổi tiếng với triết lý 'mua doanh nghiệp, không mua cổ phiếu' và 'biên an toàn' (margin of safety). "
            "Bạn ưu tiên các công ty có lợi thế cạnh tranh bền vững (moat), quản trị tốt, dòng tiền mạnh, và định giá hợp lý. "
            "Phong cách trả lời: dùng ẩn dụ đơn giản, giọng điệu khôn ngoan, thực tế, đôi khi hài hước khô khan. "
            "Luôn nhấn mạnh tầm quan trọng của tính kiên nhẫn và tư duy dài hạn (10-20 năm). "
            "Kết luận bằng khuyến nghị rõ ràng: CÓ MUA, KHÔNG MUA, hoặc CHỜ GIÁ TỐT HƠN."
        ),
    },
    {
        "id": "soros",
        "name": "George Soros",
        "title": "Bậc thầy Kinh tế Vĩ mô",
        "model": "gemini-2.0-flash",
        "backend": "gemini",
        "color": "#2196F3",
        "prompt": (
            "Bạn là George Soros, huyền thoại đầu cơ vĩ mô, người 'phá sản Ngân hàng Anh' năm 1992. "
            "Bạn nổi tiếng với lý thuyết 'tính phản thân' (reflexivity) — thị trường luôn bị bóp méo bởi nhận thức của người tham gia. "
            "Bạn phân tích dòng vốn toàn cầu, lãi suất, tỷ giá, chính sách tiền tệ, địa chính trị để tìm điểm mất cân bằng. "
            "Phong cách: sắc sảo, thực dụng, tập trung vào rủi ro hệ thống và điểm gãy (inflection point). "
            "Luôn kết luận: GỌI ĐỈNH/ĐÁY, GIỮ/THOÁT, kèm kịch bản nếu phân tích sai."
        ),
    },
    {
        "id": "lynch",
        "name": "Peter Lynch",
        "title": "Nhà đầu tư Tăng trưởng",
        "model": "llama-3.3-70b-versatile",
        "backend": "groq",
        "color": "#FF9800",
        "prompt": (
            "Bạn là Peter Lynch, huyền thoại quản lý quỹ Fidelity Magellan, người đạt lợi nhuận 29% mỗi năm trong 13 năm. "
            "Bạn nổi tiếng với triết lý 'mua những gì bạn biết' (invest in what you know) và phân loại cổ phiếu thành 6 nhóm: "
            "tăng trưởng chậm, tăng trưởng bền vững, tăng trưởng nhanh, chu kỳ, phục hồi, và giá trị tài sản. "
            "Bạn thích các công ty có PEG < 1, dòng tiền mạnh, và câu chuyện tăng trưởng dễ hiểu. "
            "Phong cách: nhiệt tình, dễ hiểu, dùng ví dụ đời thường, tập trung vào 'lợi thế cạnh tranh địa phương' (local advantage). "
            "Kết luận: MUA/THOÁT với lý do ngắn gọn từ 1-2 câu."
        ),
    },
    {
        "id": "dalio",
        "name": "Ray Dalio",
        "title": "Chiến lược gia Nguyên tắc",
        "model": "llama-3.3-70b-versatile",
        "backend": "groq",
        "color": "#9C27B0",
        "prompt": (
            "Bạn là Ray Dalio, nhà sáng lập Bridgewater Associates (quỹ hedge fund lớn nhất thế giới), "
            "tác giả cuốn 'Nguyên tắc' (Principles) và 'Trật tự Thế giới Mới' (The Changing World Order). "
            "Bạn nổi tiếng với mô hình 'Máy tính Kinh tế' (Economic Machine) và phân tích nợ-chu kỳ. "
            "Bạn nhìn thị trường qua lăng kính chu kỳ nợ ngắn hạn (7-10 năm), chu kỳ nợ dài hạn (50-75 năm), và chu kỳ thế giới (100+ năm). "
            "Phong cách: hệ thống, logic, dùng dữ liệu lịch sử, nhấn mạnh đa dạng hóa. "
            "Luôn kết luận: ĐÁNH GIÁ RỦI RO (1-10) + hành động đề xuất."
        ),
    },
    {
        "id": "graham",
        "name": "Benjamin Graham",
        "title": "Cha đẻ Phân tích Cơ bản",
        "model": "llama-3.3-70b-versatile",
        "backend": "groq",
        "color": "#795548",
        "prompt": (
            "Bạn là Benjamin Graham, cha đẻ của ngành phân tích cơ bản và đầu tư giá trị, "
            "tác giả 'Nhà đầu tư Thông minh' (The Intelligent Investor) và 'Phân tích Chứng khoán' (Security Analysis). "
            "Bạn là thầy của Warren Buffett và đặt nền móng cho triết lý đầu tư hiện đại. "
            "Bạn tập trung vào định giá nội tại, biên an toàn, và các chỉ số tài chính cốt lõi (P/E, P/B, current ratio, debt-to-equity). "
            "Phong cách: trang trọng, logic, chặt chẽ, dùng số liệu và tỷ lệ cụ thể. "
            "Bạn cảnh báo về đầu cơ và nhấn mạnh sự khác biệt giữa đầu tư và đầu cơ. "
            "Kết luận: ĐỊNH GIÁ (Rẻ/Hợp lý/Đắt) với lý do từ các chỉ số."
        ),
    },
    {
        "id": "munger",
        "name": "Charlie Munger",
        "title": "Nhà tư duy Đa chiều",
        "model": "llama-3.3-70b-versatile",
        "backend": "groq",
        "color": "#607D8B",
        "prompt": (
            "Bạn là Charlie Munger, phó chủ tịch Berkshire Hathaway và là một trong những nhà tư duy sắc sảo nhất Phố Wall. "
            "Bạn nổi tiếng với 'mạng lưới mô hình tư duy' (latticework of mental models) — dùng kiến thức từ tâm lý học, "
            "sinh học, vật lý, toán học, và lịch sử để đưa ra quyết định đầu tư. "
            "Bạn là chuyên gia về tâm lý học đầu tư — đặc biệt là '25 thiên kiến nhận thức' dẫn đến quyết định tồi. "
            "Phong cách: thẳng thắn, mỉa mai, hài hước cay độc, thường dùng nghịch lý và phản ví dụ. "
            "Câu cửa miệng: 'Nếu tôi biết tôi sẽ chết ở đâu, tôi sẽ không bao giờ đến đó.' "
            "Kết luận: CHỈ RA 1-2 SAI LẦM PHỔ BIẾN NHẤT nhà đầu tư dễ mắc phải trong tình huống này."
        ),
    },
]

CHAIRMAN_SYSTEM_PROMPT = (
    "Bạn là CHỦ TỊCH HỘI ĐỒNG CỐ VẤN ĐẦU TƯ — một nhà đầu tư thiên tài với 50 năm kinh nghiệm, "
    "từng làm việc với Warren Buffett, George Soros, Peter Lynch, Ray Dalio, Benjamin Graham, và Charlie Munger. "
    "Bạn có nhiệm vụ: lắng nghe ý kiến từ 6 chuyên gia hàng đầu thế giới, "
    "phân tích điểm mạnh/yếu của từng ý kiến, và CHỌN RA CÂU TRẢ LỜI TỐT NHẤT. "
    "\n\nQUY TẮC CHỦ TỌA:"
    "\n1. Đọc kỹ 6 ý kiến từ các chuyên gia"
    "\n2. Nhận xét ngắn gọn điểm mạnh của mỗi ý kiến (1 câu mỗi chuyên gia)"
    "\n3. CHỌN RA 1 CÂU TRẢ LỜI XUẤT SẮC NHẤT từ các chuyên gia"
    "\n4. Giải thích lý do vì sao chọn ý kiến đó (ưu điểm vượt trội so với các ý kiến còn lại)"
    "\n5. Đưa ra quyết định đầu tư CUỐI CÙNG, rõ ràng: MUA / BÁN / GIỮ / CHỜ, kèm lý do"
    "\n\nPhong cách: uy nghiêm, quyết đoán, dùng giọng điệu của 'người đã thấy tất cả'. "
    "Kết luận phải ngắn gọn, tối đa 3 câu, dễ hiểu, thực tế."
)


async def _call_openai(session, prompt, question, api_key, model="gpt-4o", timeout=45):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 1024}
    try:
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload, headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as r:
            if r.status == 200:
                data = await r.json()
                return data["choices"][0]["message"]["content"].strip()
            logger.warning(f"OpenAI {model} status {r.status}")
    except Exception as e:
        logger.warning(f"OpenAI {model} error: {e}")
    return None


async def _call_groq(session, prompt, question, api_key, model="llama-3.3-70b-versatile", timeout=45):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 1024}
    try:
        async with session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload, headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as r:
            if r.status == 200:
                data = await r.json()
                return data["choices"][0]["message"]["content"].strip()
            logger.warning(f"Groq {model} status {r.status}")
    except Exception as e:
        logger.warning(f"Groq {model} error: {e}")
    return None


async def _call_gemini(session, prompt, question, api_key, model="gemini-2.0-flash", timeout=45):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": f"{prompt}\n\nCâu hỏi: {question}"}]}]}
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status == 200:
                data = await r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            logger.warning(f"Gemini status {r.status}")
    except Exception as e:
        logger.warning(f"Gemini error: {e}")
    return None


async def _call_openrouter(session, prompt, question, api_key, model, timeout=60):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://robo-advisor.streamlit.app",
        "X-Title": "Robo-Advisor Expert Panel",
    }
    payload = {"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 1024}
    try:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload, headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as r:
            if r.status == 200:
                data = await r.json()
                return data["choices"][0]["message"]["content"].strip()
            logger.warning(f"OpenRouter {model} status {r.status}")
    except Exception as e:
        logger.warning(f"OpenRouter {model} error: {e}")
    return None


async def _call_expert(session, expert, question, api_keys):
    prompt = expert["prompt"]
    kwargs = {"prompt": prompt, "question": question}

    if expert["backend"] == "openai":
        api_key = api_keys.get("openai")
        if not api_key:
            return "❌ OPENAI_API_KEY chưa được cấu hình."
        kwargs["api_key"] = api_key
        kwargs["model"] = expert["model"]
        result = await _call_openai(session, **kwargs)

    elif expert["backend"] == "groq":
        api_key = api_keys.get("groq")
        if not api_key:
            return "❌ GROQ_API_KEY chưa được cấu hình.\n\nLấy key miễn phí tại https://console.groq.com/keys (không cần thẻ tín dụng)."
        kwargs["api_key"] = api_key
        kwargs["model"] = expert["model"]
        result = await _call_groq(session, **kwargs)

    elif expert["backend"] == "gemini":
        api_key = api_keys.get("gemini")
        if not api_key:
            return "❌ GEMINI_API_KEY chưa được cấu hình."
        kwargs["api_key"] = api_key
        kwargs["model"] = expert["model"]
        result = await _call_gemini(session, **kwargs)

    elif expert["backend"] == "openrouter":
        api_key = api_keys.get("openrouter")
        if not api_key:
            return "❌ OPENROUTER_API_KEY chưa được cấu hình.\n\nDùng OpenRouter (https://openrouter.ai) để truy cập Qwen, DeepSeek, Claude, và các model khác."
        kwargs["api_key"] = api_key
        kwargs["model"] = expert["model"]
        result = await _call_openrouter(session, **kwargs)

    else:
        result = None

    return result or f"⚠️ {expert['name']} không thể trả lời ngay lúc này."


async def _call_chairman(session, question, expert_results, api_key, api_keys):
    global _CHAIRMAN_ATTEMPTED
    _CHAIRMAN_ATTEMPTED = False

    reviews = []
    for expert, result in zip(EXPERTS, expert_results):
        reviews.append(f"=== {expert['name']} ({expert['title']}) ===\n{result}\n")

    context = "\n\n".join(reviews)
    prompt = f"{CHAIRMAN_SYSTEM_PROMPT}\n\nCÂU HỎI: {question}\n\nCÁC Ý KIẾN CHUYÊN GIA:\n{context}\n\nKẾT LUẬN CỦA CHỦ TỊCH:"

    messages = [{"role": "user", "content": prompt}]

    # Try Groq first (free, Llama 3.3 70B)
    groq_key = api_keys.get("groq")
    if groq_key:
        groq_headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
        groq_payload = {"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.5, "max_tokens": 1500}
        try:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=groq_payload, headers=groq_headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["choices"][0]["message"]["content"].strip()
                logger.warning(f"Chairman Groq status {r.status}")
        except Exception as e:
            logger.warning(f"Chairman Groq error: {e}")
        _CHAIRMAN_ATTEMPTED = True

    # Try OpenAI first (best for chairman role)
    openai_key = api_key or api_keys.get("openai")
    if openai_key:
        headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
        payload = {"model": "gpt-4o", "messages": messages, "temperature": 0.5, "max_tokens": 1500}
        try:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["choices"][0]["message"]["content"].strip()
                logger.warning(f"Chairman OpenAI status {r.status}")
        except Exception as e:
            logger.warning(f"Chairman OpenAI error: {e}")
        _CHAIRMAN_ATTEMPTED = True

    # Fallback: try OpenRouter
    or_key = api_keys.get("openrouter")
    if or_key and _CHAIRMAN_ATTEMPTED:
        or_headers = {
            "Authorization": f"Bearer {or_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://robo-advisor.streamlit.app",
            "X-Title": "Robo-Advisor Expert Panel",
        }
        or_payload = {
            "model": "openrouter/free",
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 1500,
        }
        try:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=or_payload, headers=or_headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["choices"][0]["message"]["content"].strip()
                logger.warning(f"Chairman OpenRouter status {r.status}")
        except Exception as e:
            logger.warning(f"Chairman OpenRouter error: {e}")

    return None


def hoi_dong_chuyen_gia(cau_hoi):
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")

    api_keys = {
        "openai": openai_key,
        "gemini": gemini_key,
        "openrouter": openrouter_key,
        "groq": groq_key,
    }

    try:
        results = asyncio.run(_run_expert_panel_async(cau_hoi, api_keys))
        return results
    except Exception as e:
        logger.error(f"Expert panel error: {e}")
        return None


async def _run_expert_panel_async(question, api_keys):
    async with aiohttp.ClientSession() as session:
        expert_tasks = []
        for exp in EXPERTS:
            task = _call_expert(session, exp, question, api_keys)
            expert_tasks.append(task)

        expert_results = await asyncio.gather(*expert_tasks)

        chairman_result = None
        chairman_key = api_keys.get("groq") or api_keys.get("openai")
        if chairman_key and any(r and "❌" not in r for r in expert_results):
            try:
                chairman_result = await _call_chairman(session, question, expert_results, chairman_key, api_keys)
            except Exception as e:
                logger.warning(f"Chairman failed: {e}")

    return {
        "experts": [{"id": e["id"], "name": e["name"], "title": e["title"], "color": e["color"], "response": r} for e, r in zip(EXPERTS, expert_results)],
        "chairman": chairman_result,
    }
