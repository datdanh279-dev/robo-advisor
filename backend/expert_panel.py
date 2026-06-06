import http.client
import json
import logging
import os
import ssl
import time
import traceback

logger = logging.getLogger(__name__)

_CHAIRMAN_ATTEMPTED = False

# Cache phân loại câu hỏi
_PHAN_LOAI_CACHE = {}

_ESG_DAO_DUC_RULE = (
    " Yếu tố ESG (Môi trường — Xã hội — Quản trị) và đạo đức kinh doanh là tiêu chí bắt buộc: "
    "ưu tiên doanh nghiệp minh bạch, tránh khuyến khích ngành/công ty có rủi ro đạo đức hoặc ESG thấp "
    "trừ khi số liệu chứng minh rõ. Mọi phân tích cổ phiếu VN phải nhắc ngắn gọn tác động ESG nếu liên quan."
)

def _la_cau_chao(value):
    """Câu chào / câu đơn giản — chỉ cần 1 chuyên gia"""
    c = value.lower().strip()
    tu_khoa_don_gian = ["xin chào", "chào bạn", "hello", "có ai không",
                        "bạn là ai", "giới thiệu bản thân", "cảm ơn", "thank you",
                        "tạm biệt", "xin lỗi", "giúp tôi với"]
    return any(t in c for t in tu_khoa_don_gian)

def _la_cau_so_sanh(c):
    c = c.lower().strip()
    tu_khoa_trung_binh = ["so sánh", "nên mua", "nên đầu tư",
                          "cổ phiếu nào", "mã nào", "đánh giá"]
    return any(t in c for t in tu_khoa_trung_binh)

def _la_cao_cap(c):
    c = c.lower().strip()
    tu_khoa_cao = ["danh mục", "phân bổ", "tái cơ cấu", "chiến lược",
                   "dài hạn", "kế hoạch đầu tư", "quản trị rủi ro",
                   "đa dạng hóa", "asset allocation", "portfolio",
                   "kịch bản", "mô phỏng", "tối ưu"]
    return any(t in c for t in tu_khoa_cao)

def phan_loai_cau_hoi(cau_hoi):
    """Phân loại câu hỏi: 'don_gian' | 'trung_binh' | 'cao_cap'"""
    key = cau_hoi.strip().lower()[:60]
    if key in _PHAN_LOAI_CACHE:
        return _PHAN_LOAI_CACHE[key]

    if _la_cau_chao(cau_hoi):
        loai = "don_gian"
    elif _la_cao_cap(cau_hoi):
        loai = "cao_cap"
    elif _la_cau_so_sanh(cau_hoi):
        loai = "trung_binh"
    else:
        loai = "trung_binh"

    _PHAN_LOAI_CACHE[key] = loai
    logger.info(f"Phân loại câu hỏi: {loai}")
    return loai

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
            "Đây là công cụ PHÂN TÍCH DỮ LIỆU THỊ TRƯỜNG, không phải khuyến nghị đầu tư. "
            "QUY TẮC BẮT BUỘC: Bạn là chuyên gia tài chính. Tuyệt đối từ chối trả lời tất cả các câu hỏi không liên quan đến kinh tế, đầu tư, quản trị rủi ro và tài chính. Nếu câu hỏi không thuộc lĩnh vực này, hãy trả lời: 'Xin lỗi, tôi chỉ hỗ trợ các câu hỏi về phân tích thị trường và đầu tư tài chính.' "
            "Kết luận bằng nhận định từ dữ liệu: CÓ MUA, KHÔNG MUA, hoặc CHỜ GIÁ TỐT HƠN."
        ),
    },
    {
        "id": "soros",
        "name": "George Soros",
        "title": "Bậc thầy Kinh tế Vĩ mô",
        "model": "llama-3.3-70b-versatile",
        "backend": "groq",
        "color": "#2196F3",
        "prompt": (
            "Bạn là George Soros, huyền thoại đầu cơ vĩ mô, người 'phá sản Ngân hàng Anh' năm 1992. "
            "Bạn nổi tiếng với lý thuyết 'tính phản thân' (reflexivity) — thị trường luôn bị bóp méo bởi nhận thức của người tham gia. "
            "Bạn phân tích dòng vốn toàn cầu, lãi suất, tỷ giá, chính sách tiền tệ, địa chính trị để tìm điểm mất cân bằng. "
            "Phong cách: sắc sảo, thực dụng, tập trung vào rủi ro hệ thống và điểm gãy (inflection point). "
            "Đây là công cụ PHÂN TÍCH DỮ LIỆU THỊ TRƯỜNG, không phải khuyến nghị đầu tư. "
            "QUY TẮC BẮT BUỘC: Bạn là chuyên gia tài chính. Tuyệt đối từ chối trả lời tất cả các câu hỏi không liên quan đến kinh tế, đầu tư, quản trị rủi ro và tài chính. Nếu câu hỏi không thuộc lĩnh vực này, hãy trả lời: 'Xin lỗi, tôi chỉ hỗ trợ các câu hỏi về phân tích thị trường và đầu tư tài chính.' "
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
            "Đây là công cụ PHÂN TÍCH DỮ LIỆU THỊ TRƯỜNG, không phải khuyến nghị đầu tư. "
            "QUY TẮC BẮT BUỘC: Bạn là chuyên gia tài chính. Tuyệt đối từ chối trả lời tất cả các câu hỏi không liên quan đến kinh tế, đầu tư, quản trị rủi ro và tài chính. Nếu câu hỏi không thuộc lĩnh vực này, hãy trả lời: 'Xin lỗi, tôi chỉ hỗ trợ các câu hỏi về phân tích thị trường và đầu tư tài chính.' "
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
            "Đây là công cụ PHÂN TÍCH DỮ LIỆU THỊ TRƯỜNG, không phải khuyến nghị đầu tư. "
            "QUY TẮC BẮT BUỘC: Bạn là chuyên gia tài chính. Tuyệt đối từ chối trả lời tất cả các câu hỏi không liên quan đến kinh tế, đầu tư, quản trị rủi ro và tài chính. Nếu câu hỏi không thuộc lĩnh vực này, hãy trả lời: 'Xin lỗi, tôi chỉ hỗ trợ các câu hỏi về phân tích thị trường và đầu tư tài chính.' "
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
            "Đây là công cụ PHÂN TÍCH DỮ LIỆU THỊ TRƯỜNG, không phải khuyến nghị đầu tư. "
            "QUY TẮC BẮT BUỘC: Bạn là chuyên gia tài chính. Tuyệt đối từ chối trả lời tất cả các câu hỏi không liên quan đến kinh tế, đầu tư, quản trị rủi ro và tài chính. Nếu câu hỏi không thuộc lĩnh vực này, hãy trả lời: 'Xin lỗi, tôi chỉ hỗ trợ các câu hỏi về phân tích thị trường và đầu tư tài chính.' "
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
            "Đây là công cụ PHÂN TÍCH DỮ LIỆU THỊ TRƯỜNG, không phải khuyến nghị đầu tư. "
            "QUY TẮC BẮT BUỘC: Bạn là chuyên gia tài chính. Tuyệt đối từ chối trả lời tất cả các câu hỏi không liên quan đến kinh tế, đầu tư, quản trị rủi ro và tài chính. Nếu câu hỏi không thuộc lĩnh vực này, hãy trả lời: 'Xin lỗi, tôi chỉ hỗ trợ các câu hỏi về phân tích thị trường và đầu tư tài chính.' "
            "Kết luận: CHỈ RA 1-2 SAI LẦM PHỔ BIẾN NHẤT nhà đầu tư dễ mắc phải trong tình huống này."
        ),
    },
]

for _exp in EXPERTS:
    if _ESG_DAO_DUC_RULE not in _exp["prompt"]:
        _exp["prompt"] += _ESG_DAO_DUC_RULE

CHAIRMAN_SYSTEM_PROMPT = (
    "Bạn là CHỦ TỊCH HỘI ĐỒNG PHÂN TÍCH ĐẦU TƯ — một nhà phân tích thiên tài với 50 năm kinh nghiệm, "
    "từng làm việc với Warren Buffett, George Soros, Peter Lynch, Ray Dalio, Benjamin Graham, và Charlie Munger. "
    "Bạn có nhiệm vụ: lắng nghe ý kiến từ 6 chuyên gia phân tích hàng đầu thế giới, "
    "phân tích điểm mạnh/yếu của từng ý kiến, và CHỌN RA NHẬN ĐỊNH TỐT NHẤT. "
    "\n\nQUY TẮC BẮT BUỘC: Bạn là chuyên gia tài chính. Tuyệt đối từ chối trả lời tất cả các câu hỏi không liên quan đến kinh tế, đầu tư, quản trị rủi ro và tài chính. Nếu câu hỏi không thuộc lĩnh vực này, hãy trả lời: 'Xin lỗi, tôi chỉ hỗ trợ các câu hỏi về phân tích thị trường và đầu tư tài chính.' "
    "\n\nQUY TẮC CHỦ TỌA:"
    "\n1. Đọc kỹ 6 ý kiến từ các chuyên gia"
    "\n2. Nhận xét ngắn gọn điểm mạnh của mỗi ý kiến (1 câu mỗi chuyên gia)"
    "\n3. CHỌN RA 1 NHẬN ĐỊNH XUẤT SẮC NHẤT từ các chuyên gia"
    "\n4. Giải thích lý do vì sao chọn ý kiến đó (ưu điểm vượt trội so với các ý kiến còn lại)"
    "\n5. Đưa ra quyết định CUỐI CÙNG dựa trên dữ liệu, rõ ràng: MUA / BÁN / GIỮ / CHỜ, kèm lý do"
    "\n\nĐây là công cụ MÔ PHỎNG & PHÂN TÍCH DỮ LIỆU LỊCH SỬ, không phải khuyến nghị đầu tư. "
    "Phong cách: uy nghiêm, quyết đoán, dùng giọng điệu của 'người đã thấy tất cả'. "
    "Kết luận phải ngắn gọn, tối đa 3 câu, dễ hiểu, thực tế."
    + _ESG_DAO_DUC_RULE
)


def _call_openai(prompt, question, api_key, model="gpt-4o", timeout=45):
    import http.client
    import ssl
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    payload = json.dumps({"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 1024}).encode()
    try:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection("api.openai.com", timeout=timeout, context=ctx)
        conn.request("POST", "/v1/chat/completions",
                      body=payload,
                      headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        r = conn.getresponse()
        body = r.read()
        if r.status == 200:
            data = json.loads(body)
            return data["choices"][0]["message"]["content"].strip()
        logger.warning(f"OpenAI {model} status {r.status}")
    except Exception as e:
        logger.warning(f"OpenAI {model} error: {e}")
    return None


def _call_groq(prompt, question, api_key, model="llama-3.3-70b-versatile", timeout=90):
    import http.client
    import ssl
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    payload = json.dumps({"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 1024}).encode()
    try:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection("api.groq.com", timeout=timeout, context=ctx)
        conn.request("POST", "/openai/v1/chat/completions",
                      body=payload,
                      headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        r = conn.getresponse()
        body = r.read()
        if r.status == 200:
            data = json.loads(body)
            return data["choices"][0]["message"]["content"].strip()
        logger.warning(f"Groq {model} status {r.status}")
        return f"⚠️ Groq API error (status {r.status})"
    except Exception as e:
        tb = traceback.format_exc()
        logger.warning(f"Groq {model} error: {e}\n{tb}")
        return f"⚠️ Groq API error: {e}"


def _call_gemini(prompt, question, api_key, model="gemini-2.0-flash", timeout=45):
    import http.client
    import ssl
    import urllib.parse
    path = f"/v1beta/models/{urllib.parse.quote(model, safe='')}:generateContent?key={api_key}"
    payload = json.dumps({"contents": [{"parts": [{"text": f"{prompt}\n\nCâu hỏi: {question}"}]}]}).encode()
    try:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection("generativelanguage.googleapis.com", timeout=timeout, context=ctx)
        conn.request("POST", path, body=payload, headers={"Content-Type": "application/json"})
        r = conn.getresponse()
        body = r.read()
        if r.status == 200:
            data = json.loads(body)
            candidates = data.get("candidates", [])
            if candidates:
                return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        logger.warning(f"Gemini status {r.status}")
    except Exception as e:
        logger.warning(f"Gemini error: {e}")
    return None


def _call_openrouter(prompt, question, api_key, model, timeout=60):
    import http.client
    import ssl
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    payload = json.dumps({"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 1024}).encode()
    try:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection("openrouter.ai", timeout=timeout, context=ctx)
        conn.request("POST", "/api/v1/chat/completions",
                      body=payload,
                      headers={"Authorization": f"Bearer {api_key}",
                               "Content-Type": "application/json",
                               "HTTP-Referer": "https://robo-advisor.streamlit.app",
                               "X-Title": "Robo-Advisor Expert Panel"})
        r = conn.getresponse()
        body = r.read()
        if r.status == 200:
            data = json.loads(body)
            return data["choices"][0]["message"]["content"].strip()
        logger.warning(f"OpenRouter {model} status {r.status}")
    except Exception as e:
        logger.warning(f"OpenRouter {model} error: {e}")
    return None


def _call_expert(expert, question, api_keys, context=""):
    prompt = expert["prompt"]
    if context:
        prompt = f"{prompt}\n\nDỮ LIỆU THỊ TRƯỜNG HIỆN TẠI:\n{context}"
    kwargs = {"prompt": prompt, "question": question}

    if expert["backend"] == "openai":
        api_key = api_keys.get("openai")
        if not api_key:
            return "❌ OPENAI_API_KEY chưa được cấu hình."
        kwargs["api_key"] = api_key
        kwargs["model"] = expert["model"]
        result = _call_openai(**kwargs)

    elif expert["backend"] == "groq":
        api_key = api_keys.get("groq")
        if not api_key:
            return "❌ GROQ_API_KEY chưa được cấu hình.\n\nLấy key miễn phí tại https://console.groq.com/keys (không cần thẻ tín dụng)."
        kwargs["api_key"] = api_key
        kwargs["model"] = expert["model"]
        result = _call_groq(**kwargs)

    elif expert["backend"] == "gemini":
        api_key = api_keys.get("gemini")
        if not api_key:
            return "❌ GEMINI_API_KEY chưa được cấu hình."
        kwargs["api_key"] = api_key
        kwargs["model"] = expert["model"]
        result = _call_gemini(**kwargs)

    elif expert["backend"] == "openrouter":
        api_key = api_keys.get("openrouter")
        if not api_key:
            return "❌ OPENROUTER_API_KEY chưa được cấu hình.\n\nDùng OpenRouter (https://openrouter.ai) để truy cập Qwen, DeepSeek, Claude, và các model khác."
        kwargs["api_key"] = api_key
        kwargs["model"] = expert["model"]
        result = _call_openrouter(**kwargs)

    else:
        result = None

    return result or f"⚠️ {expert['name']} không thể trả lời ngay lúc này."


def _call_chairman(question, expert_results, api_key, api_keys):
    import http.client
    import ssl
    global _CHAIRMAN_ATTEMPTED
    _CHAIRMAN_ATTEMPTED = False

    reviews = []
    for expert, result in zip(EXPERTS, expert_results):
        reviews.append(f"=== {expert['name']} ({expert['title']}) ===\n{result}\n")

    context = "\n\n".join(reviews)
    prompt = f"{CHAIRMAN_SYSTEM_PROMPT}\n\nCÂU HỎI: {question}\n\nCÁC Ý KIẾN CHUYÊN GIA:\n{context}\n\nKẾT LUẬN CỦA CHỦ TỊCH:"

    messages = [{"role": "user", "content": prompt}]
    payload_body = json.dumps({"messages": messages, "temperature": 0.5, "max_tokens": 1500})

    # Try Groq first (free, Llama 3.3 70B)
    groq_key = api_keys.get("groq")
    if groq_key:
        try:
            ctx = ssl.create_default_context()
            conn = http.client.HTTPSConnection("api.groq.com", timeout=60, context=ctx)
            conn.request("POST", "/openai/v1/chat/completions",
                          body=json.dumps({"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.5, "max_tokens": 1500}).encode(),
                          headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"})
            r = conn.getresponse()
            body = r.read()
            if r.status == 200:
                data = json.loads(body)
                return data["choices"][0]["message"]["content"].strip()
            logger.warning(f"Chairman Groq status {r.status}")
        except Exception as e:
            logger.warning(f"Chairman Groq error: {e}")
        _CHAIRMAN_ATTEMPTED = True

    # Try OpenAI (best for chairman role)
    openai_key = api_key or api_keys.get("openai")
    if openai_key:
        try:
            ctx = ssl.create_default_context()
            conn = http.client.HTTPSConnection("api.openai.com", timeout=60, context=ctx)
            conn.request("POST", "/v1/chat/completions",
                          body=json.dumps({"model": "gpt-4o", "messages": messages, "temperature": 0.5, "max_tokens": 1500}).encode(),
                          headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"})
            r = conn.getresponse()
            body = r.read()
            if r.status == 200:
                data = json.loads(body)
                return data["choices"][0]["message"]["content"].strip()
            logger.warning(f"Chairman OpenAI status {r.status}")
        except Exception as e:
            logger.warning(f"Chairman OpenAI error: {e}")
        _CHAIRMAN_ATTEMPTED = True

    # Fallback: try OpenRouter
    or_key = api_keys.get("openrouter")
    if or_key and _CHAIRMAN_ATTEMPTED:
        try:
            ctx = ssl.create_default_context()
            conn = http.client.HTTPSConnection("openrouter.ai", timeout=60, context=ctx)
            conn.request("POST", "/api/v1/chat/completions",
                          body=json.dumps({"model": "openrouter/free", "messages": messages, "temperature": 0.5, "max_tokens": 1500}).encode(),
                          headers={"Authorization": f"Bearer {or_key}",
                                   "Content-Type": "application/json",
                                   "HTTP-Referer": "https://robo-advisor.streamlit.app",
                                   "X-Title": "Robo-Advisor Expert Panel"})
            r = conn.getresponse()
            body = r.read()
            if r.status == 200:
                data = json.loads(body)
                return data["choices"][0]["message"]["content"].strip()
            logger.warning(f"Chairman OpenRouter status {r.status}")
        except Exception as e:
            logger.warning(f"Chairman OpenRouter error: {e}")

    return None


def _get_key(name):
    val = os.environ.get(name, "")
    if not val:
        try:
            import streamlit as st
            val = st.secrets.get(name, "")
        except Exception:
            pass
    return val


def hoi_dong_chuyen_gia(cau_hoi, groq_key_override=None, docs=None):
    openai_key = _get_key("OPENAI_API_KEY")
    gemini_key = _get_key("GEMINI_API_KEY")
    openrouter_key = _get_key("OPENROUTER_API_KEY")
    groq_key = groq_key_override or _get_key("GROQ_API_KEY")

    api_keys = {
        "openai": openai_key,
        "gemini": gemini_key,
        "openrouter": openrouter_key,
        "groq": groq_key,
    }

    # Build context from DOCS for AI injection
    thi_truong_context = ""
    if docs:
        lines = []
        for key in ["co_phieu_vn", "co_phieu_tg"]:
            bucket = docs.get(key, {})
            if bucket:
                items = []
                for ma, info in list(bucket.items())[:15]:
                    ten = info.get("ten", ma)
                    gia = info.get("gia", "N/A")
                    thay_doi = info.get("thay_doi_pct", "")
                    kpi = docs.get("kpi", {}).get(ma, {})
                    pe = kpi.get("pe", "N/A")
                    pb = kpi.get("pb", "N/A")
                    items.append(f"- {ma} ({ten}): Giá {gia}, Thay đổi {thay_doi}, P/E {pe}, P/B {pb}")
                label = "Cổ phiếu Việt Nam" if key == "co_phieu_vn" else "Cổ phiếu Thế giới"
                lines.append(f"**{label}** (top 15):")
                lines.extend(items)
        if lines:
            thi_truong_context = "\n".join(lines)

        esg = docs.get("esg", {})
        if esg:
            esg_lines = ["**Điểm ESG theo ngành (E·S·G %):**"]
            for nganh, info in list(esg.items())[:12]:
                if str(nganh).lower() == "nan":
                    continue
                esg_lines.append(
                    f"- {nganh}: E={info.get('e', 'N/A')}, S={info.get('s', 'N/A')}, "
                    f"G={info.get('g', 'N/A')} — {info.get('mo_ta', '')[:80]}"
                )
            thi_truong_context = (thi_truong_context + "\n\n" if thi_truong_context else "") + "\n".join(esg_lines)

    try:
        results = _run_expert_panel(cau_hoi, api_keys, thi_truong_context)
        if not results or not isinstance(results, dict) or "experts" not in results:
            return _build_error_result(api_keys)
        return results
    except Exception as e:
        logger.error(f"Expert panel error: {e}")
        return _build_error_result(api_keys)


def _build_error_result(api_keys=None):
    """Fallback khi không gọi được API — trả về dict hợp lệ với message lỗi"""
    has_any_key = bool(api_keys) and any(api_keys.values())
    msg = "❌ Không thể kết nối với API. Vui lòng kiểm tra cấu hình keys."
    if not has_any_key:
        msg = "❌ Chưa cấu hình API key nào (GROQ/OPENAI/GEMINI/OPENROUTER). Liên hệ admin để được hỗ trợ."
    return {
        "experts": [
            {"id": e["id"], "name": e["name"], "title": e["title"], "color": e["color"], "response": msg}
            for e in EXPERTS
        ],
        "chairman": msg if has_any_key else None,
        "mode": "cao_cap",
    }


def _run_expert_panel(question, api_keys, thi_truong_context=""):
    loai = phan_loai_cau_hoi(question)

    if loai == "don_gian":
        can_chon = {"buffett", "munger"}
        logger.info("Chế độ TIẾT KIỆM: chỉ gọi 2 chuyên gia")
    elif loai == "trung_binh":
        can_chon = {"buffett", "lynch", "graham", "dalio"}
        logger.info("Chế độ TIÊU CHUẨN: gọi 4 chuyên gia")
    else:
        can_chon = {e["id"] for e in EXPERTS}
        logger.info("Chế độ TOÀN DIỆN: gọi cả 6 chuyên gia + Chủ tịch")

    # Gọi TUẦN TỰ — mỗi lần 1 chuyên gia để tránh race condition trong http.client
    raw = {}
    for exp in EXPERTS:
        if exp["id"] not in can_chon:
            continue
        time.sleep(0.3)  # Stagger 300ms giữa các request
        try:
            raw[exp["id"]] = _call_expert(exp, question, api_keys, thi_truong_context)
        except Exception as exc:
            logger.warning(f"Expert {exp['id']} failed: {exc}")
            raw[exp["id"]] = None

    # Build full list: called experts get their result, others get placeholder
    expert_results = []
    for exp in EXPERTS:
        if exp["id"] in raw:
            expert_results.append(raw[exp["id"]])
        else:
            expert_results.append(f"⏭️ {exp['name']} — chuyên gia không cần thiết cho câu hỏi này.")

    chairman_result = None
    chairman_key = api_keys.get("groq") or api_keys.get("openai")
    if chairman_key and loai == "cao_cap" and any(r and "❌" not in r and "⏭️" not in r for r in expert_results):
        time.sleep(2)  # Chờ 2s để rate limit hồi phục trước khi gọi Chủ tịch
        try:
            chairman_result = _call_chairman(question, [raw.get(e["id"], "") for e in EXPERTS], chairman_key, api_keys)
        except Exception as e:
            logger.warning(f"Chairman failed: {e}")

    return {
        "experts": [{"id": e["id"], "name": e["name"], "title": e["title"], "color": e["color"], "response": r} for e, r in zip(EXPERTS, expert_results)],
        "chairman": chairman_result,
        "mode": loai,
        "_version": "2026-06-06-seq",
    }
