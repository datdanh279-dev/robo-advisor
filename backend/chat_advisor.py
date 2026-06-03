import random
from .data_loader import DOCS

MO_DAU = (
    "\"Đầu tư không phải là trò chơi IQ cao. Khi bạn có chỉ số thông minh bình thường, "
    "tất cả những gì bạn cần là khả năng kiểm soát cảm xúc.\"\n"
    "— \U0001f3b5 **Warren Buffett, huyền thoại đầu tư 94 tuổi**\n\n"
    "\U0001f4bc **80 NĂM KINH NGHIỆM — GÓC NHÌN CHUYÊN GIA**\n"
    "Tôi đã chứng kiến **7 chu kỳ tăng-giảm** của thị trường chứng khoán thế giới: "
    "từ khủng hoảng 1987, bong bóng dot-com 2000, khủng hoảng tài chính 2008, "
    "COVID-19 2020, đến chu kỳ hiện tại. Tôi đã sống qua **3 cuộc suy thoái** "
    "và chứng kiến **5 lần VN-Index mất 30%+**.\n\n"
    "\"Thị trường chứng khoán là công cụ chuyển tiền từ người thiếu kiên nhẫn "
    "sang người kiên nhẫn.\"\n\n"
    "\U0001f4a1 **TRIẾT LÝ ĐẦU TƯ CỦA TÔI**\n"
    "1. **Giá trị thực** — Mua doanh nghiệp, không mua cổ phiếu\n"
    "2. **Biên an toàn** — Mua dưới giá trị nội tại ít nhất 30%\n"
    "3. **Kiên nhẫn** — Thời gian là bạn, không phải kẻ thù\n"
    "4. **Đa dạng hóa** — Phân bổ tài sản quyết định 90% thành công\n\n"
    "\u2695\ufe0f Tôi đã tư vấn cho hơn **10.000 nhà đầu tư Việt Nam** và giúp họ xây dựng "
    "danh mục vượt qua mọi thăng trầm của thị trường. Hãy hỏi tôi bất cứ điều gì!\n\n"
)

HOI_DAP = {
    "xin chào": (
        f"{MO_DAU}"
        "Chào bạn! Tôi là **Robo-Advisor** — cỗ máy tư vấn đầu tư với kho dữ liệu "
        "80 năm thăng trầm của thị trường tài chính toàn cầu.\n\n"
        "Bạn muốn hỏi gì về:\n"
        "\U0001f4c8 **Cổ phiếu VN** — HPG, VCB, FPT, VNM, ACB, SSI, MWG, MBB...\n"
        "\U0001f30d **Cổ phiếu thế giới** — AAPL, MSFT, NVDA, TSLA, Samsung, Nestlé...\n"
        "\U0001f947 **Vàng** — vàng SJC, vàng thế giới, xu hướng giá\n"
        "\U0001f3e0 **Bất động sản** — thị trường nhà đất, cổ phiếu BĐS\n"
        "\U0001f9fe **Kinh tế vĩ mô** — lãi suất, lạm phát, tỷ giá\n"
        "\U0001f4b0 **Chiến lược** — đầu tư giá trị, tăng trưởng, cổ tức\n\n"
        "Hãy hỏi tôi bất cứ điều gì!"
    ),
    "cảm ơn": (
        "\"Hãy mua khi người khác sợ hãi và bán khi người khác tham lam.\"\n"
        "Rất vui được đồng hành cùng bạn trên hành trình đầu tư. "
        "Hãy nhớ: Thời gian là bạn của nhà đầu tư dài hạn. "
        "Quay lại bất cứ khi nào bạn cần!"
    ),
    "tạm biệt": (
        "\"Thị trường chứng khoán là công cụ chuyển tiền từ người thiếu kiên nhẫn "
        "sang người kiên nhẫn.\"\n\n"
        "Tạm biệt! Chúc bạn luôn giữ vững kỷ luật và thành công trên con đường đầu tư. "
        "Hãy nhớ: Đa dạng hóa là bữa trưa miễn phí duy nhất trong tài chính."
    ),
}

DIEM_NHAN_CO_PHIEU = {
    "hpg": (
        "\U0001f3ed **PHÂN TÍCH CỔ PHIẾU {ten} — {nganh}**\n\n"
        "{ten} là **tập đoàn thép số 1 Việt Nam**, chiếm 30% thị phần thép xây dựng và 25% thép HRC. "
        "Tôi đã theo dõi HPG từ những ngày đầu niêm yết và chứng kiến nó vượt qua 3 chu kỳ giá thép.\n\n"
        "\u2705 **ĐIỂM NHẤN ĐẦU TƯ**\n"
        "• **Dung Quất 2** nâng công suất 7→14 triệu tấn — doanh thu gấp đôi từ 2027\n"
        "• Giá thép thế giới phục hồi nhờ Trung Quốc kích cầu BĐS\n"
        "• Đầu tư công giải ngân mạnh — cao tốc Bắc-Nam, sân bay Long Thành\n"
        "• Biên lợi nhuận cải thiện nhờ giá than coke giảm\n"
    ),
    "vcb": (
        "\U0001f3e6 **PHÂN TÍCH CỔ PHIẾU {ten} — {nganh}**\n\n"
        "{ten} — \"cổ phiếu vua\" ngành ngân hàng. Tôi từng chứng kiến VCB vượt qua 3 cuộc khủng hoảng.\n\n"
        "\u2705 **ĐIỂM NHẤN ĐẦU TƯ**\n"
        "• **Chất lượng tài sản tốt nhất ngành** — nợ xấu <1%, khối ngoại mua ròng\n"
        "• **CASA ~32%** — chi phí vốn rẻ nhất hệ thống\n"
        "• Tăng trưởng tín dụng 15-18%/năm, ổn định\n"
        "• ROE 22-25% — sinh lời vượt trội so với trung bình ngành (~16%)\n"
    ),
    "fpt": (
        "\U0001f4bb **PHÂN TÍCH CỔ PHIẾU {ten} — {nganh}**\n\n"
        "{ten} là đại diện công nghệ Việt Nam duy nhất có tầm vóc quốc tế. "
        "Trong 10 năm, cổ phiếu này đã **tăng 15 lần**.\n\n"
        "\u2705 **ĐIỂM NHẤN ĐẦU TƯ**\n"
        "• **Xuất khẩu phần mềm** tăng 25-30%/năm — Nhật Bản, Mỹ, EU\n"
        "• **Chuyển đổi số** nội địa bùng nổ — doanh thu cloud, AI\n"
        "• Cổ tức 20% tiền mặt đều đặn — dòng tiền ổn định\n"
        "• **Duy nhất** trong chuỗi cung ứng công nghệ toàn cầu từ VN\n"
    ),
    "vnm": (
        "\U0001f95b **PHÂN TÍCH CỔ PHIẾU {ten} — {nganh}**\n\n"
        "{ten} là **cổ phiếu phòng thủ số 1 Việt Nam** — thị phần sữa nước ~55%.\n\n"
        "\u2705 **ĐIỂM NHẤN ĐẦU TƯ**\n"
        "• **Thương hiệu quốc dân** — 99% người Việt biết Vinamilk\n"
        "• Biên lợi nhuận gộp ~45% — sức mạnh định giá vượt trội\n"
        "• Cổ tức tiền mặt **~35-40%** (~2.800đ/CP) — yield cao\n"
        "• Ít nợ (D/E thấp) — bảng cân đối lành mạnh nhất thị trường\n"
    ),
    "ssi": (
        "\U0001f3e9 **PHÂN TÍCH CỔ PHIẾU {ten} — {nganh}**\n\n"
        "{ten} là **công ty chứng khoán lớn nhất VN**, chiếm 12-14% thị phần môi giới.\n\n"
        "\u2705 **ĐIỂM NHẤN ĐẦU TƯ**\n"
        "• **\"Cuốc và xẻng\"** trong cơn sốt vàng chứng khoán\n"
        "• Hưởng lợi kép: KH mới → phí giao dịch → cho vay margin\n"
        "• Định giá hấp dẫn khi VN-Index còn dư địa tăng\n"
        "• Room ngoại cao — được khối ngoại ưa chuộng\n"
    ),
    "acb": (
        "\U0001f3e6 **PHÂN TÍCH CỔ PHIẾU {ten} — {nganh}**\n\n"
        "{ten} là ngân hàng bán lẻ hàng đầu với quản trị rủi ro xuất sắc.\n\n"
        "\u2705 **ĐIỂM NHẤN ĐẦU TƯ**\n"
        "• **PE thấp nhất** ngân hàng TMCP — đang quá rẻ so với chất lượng\n"
        "• ROE 22% — ngang VCB nhưng giá chỉ bằng 1/2\n"
        "• Tỷ lệ an toàn vốn (CAR) >12% — vững chắc\n"
        "• NIM 4.5% — hiệu quả sinh lời tốt\n"
    ),
    "mwg": (
        "\U0001f6cd\ufe0f **PHÂN TÍCH CỔ PHIẾU {ten} — {nganh}**\n\n"
        "{ten} — nhà bán lẻ số 1 với TGDD, ĐMX, Bách Hóa Xanh.\n\n"
        "\u2705 **ĐIỂM NHẤN ĐẦU TƯ**\n"
        "• **Câu chuyện turnaround** — BHX kỳ vọng hòa vốn 2026\n"
        "• TGDD + ĐMX tạo dòng tiền ổn định\n"
        "• Nếu BHX thành công → giá CP có thể tăng gấp đôi\n"
        "• PE hiện tại đã phản ánh rủi ro — upside lớn\n"
    ),
    "mbb": (
        "\U0001f3e6 **PHÂN TÍCH CỔ PHIẾU {ten} — {nganh}**\n\n"
        "{ten} là ngân hàng có tốc độ tăng trưởng nhanh nhất 5 năm qua.\n\n"
        "\u2705 **ĐIỂM NHẤN ĐẦU TƯ**\n"
        "• **Tăng trưởng lợi nhuận** 20-25%/năm — dẫn đầu ngành\n"
        "• Hệ sinh thái MB — ngân hàng số, bảo hiểm, chứng khoán\n"
        "• PE ~6.6 — định giá rẻ nhất ngân hàng TMCP\n"
        "• Tỷ lệ CASA cải thiện — chi phí vốn giảm\n"
    ),
    "msn": (
        "\U0001f3ed **PHÂN TÍCH CỔ PHIẾU {ten} — {nganh}**\n\n"
        "{ten} — tập đoàn hàng tiêu dùng với hệ sinh thái đa ngành.\n\n"
        "\u2705 **ĐIỂM NHẤN ĐẦU TƯ**\n"
        "• **WinCommerce (WinMart) đã có lãi** — bước ngoặt lịch sử\n"
        "• Mảng gia vị (Chin-su, Nam Ngư) — thị phần >50%\n"
        "• Mảng khai khoáng (Techgen) — hưởng lợi giá than\n"
        "• Tái cấu trúc mạnh mẽ — tiềm năng tăng gấp 3 lần\n"
    ),
}

THI_TRUONG_ANALYSIS = {
    "thị trường": (
        f"{MO_DAU}"
        "\U0001f4c8 **TỔNG QUAN THỊ TRƯỜNG VIỆT NAM**\n\n"
        "VN-Index đang ở vùng **1.280 điểm**, PE ~13.5. So với các nước trong khu vực "
        "(Thái Lan 16x, Indonesia 15x, Philippines 14x), thị trường Việt Nam đang được "
        "định giá thấp hơn 15-20%.\n\n"
        "\U0001f4c5 **KỊCH BẢN NGẮN HẠN (1-3 tháng)**\n"
        "• Tích lũy trong biên độ 1.250-1.300\n"
        "• Thanh khoản thấp — dòng tiền chờ tín hiệu rõ ràng\n"
        "• Khối ngoại vẫn bán ròng — áp lực tỷ giá\n\n"
        "\U0001f4c5 **KỊCH BẢN TRUNG HẠN (6-12 tháng)**\n"
        "• Kỳ vọng lãi suất giảm → dòng tiền vào chứng khoán\n"
        "• Câu chuyện nâng hạng FTSE Russell → +5 tỷ USD từ ETF\n"
        "• Mục tiêu: **1.350 - 1.400 điểm**\n\n"
        "\U0001f4c5 **KỊCH BẢN DÀI HẠN (2-5 năm)**\n"
        "• Việt Nam là điểm đến FDI hàng đầu Đông Nam Á\n"
        "• Tầng lớp trung lưu tăng nhanh → tiêu dùng tăng trưởng\n"
        "• Mục tiêu: **1.600 - 2.000 điểm** (tương đương PE 15-17x)\n\n"
        "\U0001f50d **NHẬN ĐỊNH CHUYÊN GIA**\n"
        "\"Thị trường chứng khoán là nơi duy nhất mà người ta chạy ra cửa khi có đám cháy — "
        "thay vì mang vòi nước vào dập lửa.\"\n\n"
        "Lời khuyên của tôi: **Đừng cố bắt đáy**. Hãy DCA hàng tháng vào các cổ phiếu "
        "blue-chip như VCB, FPT, HPG khi thị trường điều chỉnh."
    ),
    "vàng": (
        f"{MO_DAU}"
        "\U0001f947 **PHÂN TÍCH THỊ TRƯỜNG VÀNG TOÀN DIỆN**\n\n"
        "Vàng luôn là nơi trú ẩn an toàn trong 5.000 năm lịch sử loài người. "
        "Từ thời Ai Cập cổ đại đến nay, vàng vẫn giữ giá trị.\n\n"
        "\U0001f4b5 **VÀNG THẾ GIỚI (XAU/USD)**\n"
        "• Giá hiện tại: **~2.350 USD/oz**\n"
        "• Hỗ trợ: 2.200 USD (đáy tháng 2/2026)\n"
        "• Kháng cự: 2.450 USD (đỉnh lịch sử)\n"
        "• Dự báo 6-12 tháng: **2.500-2.800 USD** (Fed hạ lãi suất)\n\n"
        "\U0001f1fb\U0001f1f3 **VÀNG SJC TRONG NƯỚC**\n"
        "• Mua vào: ~79,8 triệu/lượng\n"
        "• Bán ra: ~81,0 triệu/lượng\n"
        "• Chênh lệch mua-bán: 1,2 triệu — rất cao so với thế giới\n\n"
        "\U0001f4b0 **CHIẾN LƯỢC ĐẦU TƯ VÀNG**\n"
        "• Tỷ trọng danh mục: 5-15% tùy khẩu vị\n"
        "• **Không mua đuổi** khi giá đang ở đỉnh lịch sử\n"
        "• Chờ điều chỉnh về 75-76 triệu/lượng để mua\n"
        "• Ưu tiên vàng SJC thay vì vàng nhẫn (thanh khoản cao hơn)\n\n"
        "\U0001f50d **NHẬN ĐỊNH**\n"
        "\"Vàng là tiền tệ của sự sợ hãi.\" Khi kinh tế bất ổn, vàng tăng giá. "
        "Tuy nhiên, trong dài hạn 10-20 năm, cổ phiếu luôn vượt trội hơn vàng. "
        "Hãy nhớ: vàng để phòng vệ, cổ phiếu để làm giàu."
    ),
    "bất động sản": (
        f"{MO_DAU}"
        "\U0001f3fe **PHÂN TÍCH THỊ TRƯỜNG BẤT ĐỘNG SẢN VIỆT NAM**\n\n"
        "Thị trường BĐS đã chạm đáy 2023-2024 và đang phục hồi chậm. "
        "Tôi đã chứng kiến 3 chu kỳ bùng nổ và đổ vỡ của BĐS Việt Nam — "
        "năm 2008, 2011, và 2023. Lần nào cũng vậy: \"Mua khi người khác sợ hãi, bán khi người khác tham lam.\"\n\n"
        "\U0001f4c8 **PHÂN KHÚC NỔI BẬT**\n"
        "✅ **Chung cư Hà Nội**: Tăng 15-20% — hạ tầng metro, cầu vượt\n"
        "✅ **Đất nền vùng ven TP.HCM**: Bình Dương, Đồng Nai, Long An\n"
        "✅ **BĐS công nghiệp**: KCN phía Bắc (Bắc Ninh, Hải Phòng) và Đồng Nai\n\n"
        "\U0001f3e6 **CỔ PHIẾU BĐS ĐÁNG QUAN TÂM**\n"
        "• **VIC** (Vingroup): Đầu tàu, đa dạng lĩnh vực (BĐS, xe VinFast, giáo dục)\n"
        "• **KDH** (Khang Điền): Quỹ đất sạch 600ha tại TP.HCM\n"
        "• **DIG** (DIC Corp): Hưởng lợi từ hạ tầng cao tốc\n"
        "• **NLG** (Nam Long): Phân khúc trung cấp, thanh khoản tốt\n\n"
        "\U0001f50d **NHẬN ĐỊNH**\n"
        "BĐS đang ở vùng đáy và là cơ hội cho người có tiền mặt. Nhưng hãy chọn "
        "cổ phiếu BĐS thay vì mua trực tiếp — tính thanh khoản cao hơn, dễ quản lý rủi ro hơn."
    ),
    "trái phiếu": (
        f"{MO_DAU}"
        "\U0001f4dc **PHÂN TÍCH THỊ TRƯỜNG TRÁI PHIẾU**\n\n"
        "Trái phiếu là kênh đầu tư an toàn nhất cho nhà đầu tư bảo thủ. "
        "\"Lợi nhuận tốt nhất đến từ giấc ngủ ngon.\"\n\n"
        "\U0001f3db\ufe0f **TRÁI PHIẾU CHÍNH PHỦ** — AN TOÀN TUYỆT ĐỐI\n"
        "• Kỳ hạn 10 năm: **7,05%/năm**\n"
        "• Kỳ hạn 5 năm: **5,8%/năm**\n"
        "• Kỳ hạn 2 năm: **4,5%/năm**\n\n"
        "\U0001f3e6 **TRÁI PHIẾU DOANH NGHIỆP** — RỦI RO CAO HƠN\n"
        "• Ngân hàng thương mại: 6,5-7,5%/năm\n"
        "• Bất động sản tốp đầu: 9-11%/năm\n"
        "• Năng lượng: 10-12%/năm\n\n"
        "\u26a0\ufe0f **LƯU Ý QUAN TRỌNG**\n"
        "Chỉ mua trái phiếu doanh nghiệp của các công ty:\n"
        "1. Có tài sản đảm bảo (bất động sản, cổ phiếu)\n"
        "2. Được xếp hạng tín nhiệm từ FiinGroup hoặc S&P\n"
        "3. Có lịch sử trả nợ tốt\n\n"
        "\U0001f50d **NHẬN ĐỊNH**\n"
        "Trái phiếu nên chiếm 20-50% danh mục của nhà đầu tư bảo thủ. "
        "\"Đừng bao giờ mạo hiểm số tiền bạn cần để kiếm số tiền bạn không cần.\""
    ),
    "tiền điện tử": (
        f"{MO_DAU}"
        "\u20bf **PHÂN TÍCH THỊ TRƯỜNG TIỀN ĐIỆN TỬ**\n\n"
        "Bitcoin đã hoàn tất halving tháng 4/2024. Trong lịch sử, 12-18 tháng sau halving "
        "thường là đỉnh chu kỳ. Hãy nhìn lại:\n"
        "• 2012 → 2013: +8.000%\n"
        "• 2016 → 2017: +2.000%\n"
        "• 2020 → 2021: +400%\n"
        "• 2024 → 2025: ??\n\n"
        "\U0001f4b5 **BITCOIN (BTC)**\n"
        "• Giá: ~67.000 USD\n"
        "• Hỗ trợ: 58.000-60.000 USD\n"
        "• Kháng cự: 72.000-74.000 USD\n\n"
        "\U0001f539 **ETHEREUM (ETH)**\n"
        "• Giá: ~3.500 USD\n"
        "• Hỗ trợ: 2.800-3.000 USD\n"
        "• Kháng cự: 3.800-4.000 USD\n\n"
        "\U0001f4b0 **CHIẾN LƯỢC ĐẦU TƯ**\n"
        "• Chỉ dành 5-10% tổng tài sản\n"
        "• **Chỉ mua BTC và ETH** — altcoin quá rủi ro\n"
        "• DCA hàng tuần — đừng cố timing\n"
        "• **Tuyệt đối không dùng margin**\n\n"
        "\U0001f50d **NHẬN ĐỊNH**\n"
        "\"Crypto là cuộc cách mạng nhưng cũng là canh bạc lớn nhất thế giới.\" "
        "Nếu bạn không thể chịu mất 50% số tiền đầu tư, đừng tham gia."
    ),
    "kinh tế": (
        f"{MO_DAU}"
        "\U0001f4c8 **KINH TẾ VĨ MÔ VIỆT NAM 2026**\n\n"
        "\"Trong kinh tế, không có gì là chắc chắn ngoại trừ sự không chắc chắn.\"\n\n"
        "\U0001f4ca **CÁC CHỈ SỐ CHÍNH**\n"
        "• GDP: **6,5-7%** — ổn định, cao thứ 2 ASEAN sau Philippines\n"
        "• Lạm phát: **3,0-3,5%** — trong tầm kiểm soát\n"
        "• Lãi suất điều hành: **4,5%** — mặt bằng thấp\n"
        "• FDI giải ngân: **25 tỷ USD** — kỷ lục\n"
        "• Xuất siêu: **15 tỷ USD**\n"
        "• Dự trữ ngoại hối: **~100 tỷ USD**\n\n"
        "\U0001f50d **TÁC ĐỘNG ĐẾN ĐẦU TƯ**\n"
        "• Lãi suất thấp: tích cực cho cổ phiếu và BĐS\n"
        "• FDI mạnh: tích cực cho BĐS khu công nghiệp\n"
        "• Đầu tư công: tích cực cho thép, xây dựng\n"
        "• Tỷ giá áp lực: theo dõi chỉ số DXY\n\n"
        "Việt Nam vẫn là điểm sáng trong bức tranh toàn cầu đầy bất ổn."
    ),
    "cổ tức": (
        f"{MO_DAU}"
        "\U0001f4b0 **CỔ TỨC CÁC CÔNG TY VIỆT NAM**\n\n"
        "\"Cổ tức là bằng chứng cho thấy công ty thực sự có lợi nhuận.\"\n\n"
        "\U0001f3e6 **NGÂN HÀNG**\n"
        "• VCB: 20% tiền mặt + 25% cổ phiếu → yield ~2%\n"
        "• ACB: 30% tiền mặt → yield ~5%*\n"
        "• MBB: 15% tiền mặt + 20% cổ phiếu → yield ~3,5%\n\n"
        "\U0001f3ed **SẢN XUẤT & THỰC PHẨM**\n"
        "• VNM: 35-40% tiền mặt (~2.800đ/cp) → yield **~3,9%**\n"
        "• FPT: 20% tiền mặt → yield **~1,7%**\n"
        "• HPG: 10% tiền mặt + 20% cổ phiếu → yield ~2%\n\n"
        "\U0001f50d **LỜI KHUYÊN**\n"
        "Mua trước ngày giao dịch không hưởng quyền (GDKHQ) 1-2 tháng. "
        "Cổ tức tiền mặt mang lại dòng thu nhập đều đặn, rất phù hợp cho người về hưu."
    ),
    "đầu tư": (
        f"{MO_DAU}"
        "\U0001f4da **NGUYÊN TẮC ĐẦU TƯ — TỪ MỘT NGƯỜI ĐÃ TRẢI QUA 7 CHU KỲ THỊ TRƯỜNG**\n\n"
        "\"Nguyên tắc số 1: Đừng bao giờ mất tiền. Nguyên tắc số 2: Đừng bao giờ quên nguyên tắc số 1.\" "
        "— Warren Buffett\n\n"
        "\U0001f4a1 **7 NGUYÊN TẮC VÀNG**\n\n"
        "1️⃣ **Xác định khẩu vị rủi ro**: Biết mình là ai trước khi đầu tư\n"
        "2️⃣ **Đa dạng hóa**: Đừng bỏ tất cả trứng vào một giỏ\n"
        "3️⃣ **Đầu tư dài hạn**: Time in market > Timing the market\n"
        "4️⃣ **DCA**: Mua định kỳ đều đặn, không cố bắt đáy\n"
        "5️⃣ **Quỹ khẩn cấp**: Luôn có 6 tháng chi tiêu trước khi đầu tư\n"
        "6️⃣ **Phân bổ tài sản**: Tỷ lệ cổ phiếu/trái phiếu/vàng phù hợp tuổi\n"
        "7️⃣ **Tái cân bằng**: Điều chỉnh danh mục định kỳ\n\n"
        "\U0001f50d **LỜI CUỐI**\n"
        "Đầu tư không phải là đua tốc độ, mà là marathon. "
        "Người chiến thắng là người kiên nhẫn và kỷ luật nhất."
    ),
    "phân tích kỹ thuật": (
        f"{MO_DAU}"
        "\U0001f4d0 **PHÂN TÍCH KỸ THUẬT NÂNG CAO**\n\n"
        "\"Kỹ thuật không dự đoán được tương lai, nhưng nó giúp bạn quản lý rủi ro.\"\n\n"
        "\U0001f535 **CHỈ BÁO XU HƯỚNG**\n"
        "• **MA20/MA50**: Giá trên MA20 → xu hướng ngắn hạn tăng\n"
        "• **MA100/MA200**: Giá trên MA200 → xu hướng dài hạn tăng\n"
        "• **Golden Cross**: MA50 cắt lên MA200 = TÍN HIỆU MUA MẠNH\n"
        "• **Death Cross**: MA50 cắt xuống MA200 = TÍN HIỆU BÁN\n\n"
        "\U0001f7e2 **CHỈ BÁO ĐỘNG LƯỢNG**\n"
        "• **RSI (14)**: <30 quá bán → mua; >70 quá mua → bán\n"
        "• **MACD**: Đường MACD cắt lên Signal = MUA; cắt xuống = BÁN\n"
        "• **Stochastic**: %K <20 oversold; >80 overbought\n\n"
        "\U0001f7e1 **CHỈ BÁO BIẾN ĐỘNG**\n"
        "• **Bollinger Bands (20,2)**: Giá chạm dải dưới → oversold; chạm dải trên → overbought\n"
        "• **ATR**: Đo lường biến động — ATR cao = biến động mạnh\n\n"
        "\U0001f50d **MẸO THỰC CHIẾN**\n"
        "Không dùng một chỉ báo duy nhất. Kết hợp ít nhất 3 chỉ báo trước khi ra quyết định. "
        "\"Kỹ thuật là nghệ thuật đọc bản đồ, nhưng bạn vẫn cần la bàn — đó là phân tích cơ bản.\""
    ),
    "thuế": (
        f"{MO_DAU}"
        "\U0001f4cb **THUẾ VÀ CHI PHÍ ĐẦU TƯ TẠI VIỆT NAM**\n\n"
        "\"Trên đời này chỉ có hai điều chắc chắn: cái chết và thuế.\" — Benjamin Franklin\n\n"
        "\U0001f4c4 **THUẾ CHỨNG KHOÁN**\n"
        "• Chuyển nhượng: **0,1%** giá trị giao dịch\n"
        "• Cổ tức tiền mặt: **5%**\n"
        "• Thu nhập từ trái phiếu: **5%**\n"
        "• Chênh lệch mua bán CK: **0,1%** (đã bao gồm phí)\n\n"
        "\U0001f3e0 **THUẾ BẤT ĐỘNG SẢN**\n"
        "• Trước bạ: **0,5%**\n"
        "• Thuế chuyển nhượng: **2%** giá bán\n"
        "• VAT: **10%** (nếu kinh doanh)\n\n"
        "\U0001f947 **THUẾ VÀNG**\n"
        "• Hiện chưa bị đánh thuế thu nhập cá nhân — đây là lợi thế!"
    ),
    "so sánh": (
        f"{MO_DAU}"
        "\U0001f9d1\u200d\U0001f4bc **SO SÁNH CỔ PHIẾU — LỜI KHUYÊN TỪ CHUYÊN GIA**\n\n"
        "\"Đừng bao giờ đầu tư vào một công ty mà bạn không hiểu.\" — Warren Buffett\n\n"
        "Khi so sánh hai cổ phiếu, hãy đặt câu hỏi:\n\n"
        "\U0001f4ac **1. Ngành nào có triển vọng hơn?**\n"
        "• Ngân hàng (VCB vs ACB vs MBB): Tăng trưởng tín dụng + NIM\n"
        "• Thép (HPG vs NKG vs HSG): Giá thép + công suất\n"
        "• Công nghệ (FPT vs CMG): Hợp đồng XK + nhân lực\n\n"
        "\U0001f4ac **2. Định giá nào hấp dẫn hơn?**\n"
        "• PE < PEG < 1 → định giá rẻ\n"
        "• ROE > 15% + PE < 15 → cơ hội\n\n"
        "\U0001f4ac **3. Chất lượng quản trị?**\n"
        "• Cổ tức đều → dòng tiền thật\n"
        "• Room ngoại cao → được quốc tế công nhận\n\n"
        "\U0001f50d **VÍ DỤ: VCB vs ACB**\n"
        "• VCB: PE 15.2, ROE 24%, chất lượng tốt nhất, giá cao\n"
        "• ACB: PE 8.5, ROE 22%, rẻ hơn 45%, tăng trưởng tương đương\n"
        "→ ACB hấp dẫn hơn về mặt định giá, VCB an toàn hơn.\n\n"
        "\"Mua cổ phiếu tốt với giá hợp lý, không mua cổ phiếu trung bình với giá rẻ.\""
    ),
    "bitcoin": (
        f"{MO_DAU}"
        "\u20bf **BITCOIN — TỔNG QUAN NHANH**\n\n"
        "• Giá: ~$67,000-72,000\n"
        "• Vốn hóa: ~$1,300 tỷ\n"
        "• Halving gần nhất: Tháng 4/2024\n\n"
        "\U0001f447 Hỏi \"phân tích bitcoin\" để xem phân tích CHI TIẾT!"
    ),
    "vang_nhanh": (
        f"{MO_DAU}"
        "\U0001f947 **VÀNG — TỔNG QUAN NHANH**\n\n"
        "• Vàng SJC: ~78-80 triệu VNĐ/lượng\n"
        "• Vàng thế giới: ~$2,350-2,400/oz\n\n"
        "\U0001f447 Hỏi \"phân tích vàng\" để xem phân tích CHI TIẾT!"
    ),
}

CAU_TRA_LOI_MAC_DINH = [
    f"{MO_DAU}"
    "Tôi có thể phân tích chi tiết **cổ phiếu** từ kho dữ liệu hơn 200 mã trên thị trường:\n"
    "\U0001f1fb\U0001f1f3 **VN:** HPG, VCB, FPT, VNM, ACB, SSI, MWG, MBB, MSN, VIC...\n"
    "\U0001f30d **Thế giới:** AAPL, MSFT, NVDA, TSLA, Samsung, Nestlé, Tencent...\n"
    "\u20bf **Crypto:** Bitcoin, Ethereum — phân tích chu kỳ halving, kỹ thuật\n"
    "\U0001f947 **Vàng:** SJC, XAU/USD — phân tích kỹ thuật, vĩ mô\n\n"
    "Chỉ cần hỏi tên mã, tôi sẽ cho bạn:\n"
    "\u2705 Phân tích định giá (PE, EPS, ROE)\n"
    "\u2705 Vùng mua/bán dựa trên kỹ thuật (RSI, MACD, Bollinger)\n"
    "\u2705 Luận điểm đầu tư & rủi ro\n"
    "\u2705 Phân tích tài chính chuyên sâu\n"
    "\u2705 Góc nhìn vĩ mô & bối cảnh thị trường\n\n"
    "Bạn muốn phân tích mã nào?",

    f"{MO_DAU}"
    "\U0001f4ac **Hãy hỏi tôi bất cứ điều gì về đầu tư!**\n\n"
    "Tôi đã sống qua 7 chu kỳ thị trường, chứng kiến những cuộc khủng hoảng 2008, 2011, 2020, 2023. "
    "Tôi hiểu nỗi sợ của nhà đầu tư khi thấy danh mục giảm 30% và cảm giác hưng phấn khi tăng gấp đôi.\n\n"
    "\U0001f447 **Thử hỏi tôi:**\n"
    "• \"Phân tích HPG\" — phân tích chi tiết một cổ phiếu\n"
    "• \"So sánh VCB và ACB\" — so sánh hai cổ phiếu\n"
    "• \"Phân tích Bitcoin\" — chu kỳ halving, kỹ thuật BTC\n"
    "• \"Phân tích vàng\" — giá SJC, XAU, chiến lược\n"
    "• \"Thị trường hôm nay\" — tổng quan VN-Index\n"
    "• \"Đầu tư 10 triệu\" — chiến lược cho người mới\n\n"
    "Tôi ở đây để chia sẻ kiến thức 80 năm kinh nghiệm! 🎯",

    f"{MO_DAU}"
    "\"Hãy mua cổ phiếu như bạn mua một cửa hàng tạp hóa — "
    "bạn sẽ không mua nó nếu chủ cửa hàng nói rằng nó sẽ đóng cửa vào năm sau.\"\n\n"
    "Tôi chuyên phân tích:\n"
    "\U0001f4c8 Định giá doanh nghiệp theo phương pháp Graham & Dodd\n"
    "\U0001f4ca Phân tích kỹ thuật với RSI, MACD, Bollinger Bands\n"
    "\u20bf Chu kỳ Bitcoin & Crypto — halving, on-chain metrics\n"
    "\U0001f947 Phân tích thị trường vàng — SJC, XAU/USD, chiến lược\n"
    "\U0001f3db\ufe0f Chiến lược phân bổ tài sản theo tuổi và mục tiêu\n"
    "\U0001f30d Kinh tế vĩ mô và tác động đến thị trường Việt Nam\n\n"
    "Bạn cần tôi phân tích gì hôm nay? Hãy hỏi ngay! 🚀",
]

def _build_stock_info():
    info = {}
    db = DOCS.get("co_phieu_vn", {})
    if not db:
        return info
    for ma, d in db.items():
        ma_lower = ma.lower()
        gia = d.get("gia", 0) or 0
        gc = max(int(gia * 1.2 / 1000) * 1000, gia + 1000)
        gt = max(int(gia * 0.8 / 1000) * 1000, 1000)
        if gt >= gia:
            gt = max(int(gia * 0.8), 1000)
        von_hoa = d.get("von_hoa", 0) or 0
        gia_int = int(gia) if gia else 0
        cp_luu_hanh = int(von_hoa * 1e9 / gia_int) if gia_int > 0 and von_hoa > 0 else 0
        info[ma_lower] = {
            "ten": d.get("ten", ma) or ma,
            "nganh": d.get("nganh", "") or "",
            "gia": gia_int,
            "gia_cao": gc,
            "gia_thap": gt,
            "pe": d.get("pe", 0) or 0,
            "pb": d.get("pb", 0) or 0,
            "eps": d.get("eps", 0) or 0,
            "roe": d.get("roe", 0) or 0,
            "roic": d.get("roic", 0) or 0,
            "von_hoa": von_hoa,
            "von_csh": d.get("von_csh", 0) or 0,
            "no_vay": d.get("no_vay", 0) or 0,
            "de_ratio": d.get("de_ratio", 0) or 0,
            "ebitda": d.get("ebitda", 0) or 0,
            "dt_2025": d.get("dt_2025", 0) or 0,
            "lnst_2025": d.get("lnst_2025", 0) or 0,
            "bien_ln": d.get("bien_ln", 0) or 0,
            "co_tuc_d": d.get("co_tuc_d", 0) or 0,
            "co_tuc_pct": d.get("co_tuc_pct", 0) or 0,
            "pct_ngoai": d.get("pct_ngoai", 0) or 0,
            "insider_pct": d.get("insider_pct", 0) or 0,
            "chu_tich": d.get("chu_tich", "") or "",
            "esg_score": d.get("esg_score", "") or "",
            "dao_duc": d.get("dao_duc", "") or "",
            "san": d.get("san", "") or "",
            "tin_hieu": d.get("tin_hieu", "") or "",
            "khoi_luong_tb": "",
            "cp_luu_hanh": cp_luu_hanh,
        }
    return info

STOCK_INFO = _build_stock_info()

def _build_world_stock_info():
    info = {}
    db = DOCS.get("co_phieu_tg", {})
    if not db:
        return info
    for ma, d in db.items():
        ma_lower = ma.lower().replace(".ax", "").replace(".tw", "")
        gia = d.get("gia", 0) or 0
        gc = round(gia * 1.2, 2)
        gt = round(gia * 0.8, 2)
        if gt >= gia:
            gt = round(gia * 0.8, 2)
        info[ma_lower] = {
            "ten": d.get("ten", ma) or ma,
            "nganh": d.get("nganh", "") or "",
            "gia": gia,
            "gia_cao": gc,
            "gia_thap": gt,
            "pe": d.get("pe", 0) or 0,
            "roe": d.get("roe", 0) or 0,
            "von_hoa": d.get("von_hoa", 0) or 0,
            "san": d.get("san", "") or "",
            "tin_hieu": d.get("tin_hieu", "") or "",
        }
    return info

WORLD_STOCK_INFO = _build_world_stock_info()

COMMON_NAMES_MAP = {
    "samsung": "005930", "apple": "aapl", "microsoft": "msft", "google": "googl",
    "alphabet": "googl", "amazon": "amzn", "meta": "meta", "facebook": "meta",
    "nvidia": "nvda", "tesla": "tsla", "netflix": "nflx", "disney": "dis",
    "visa": "v", "mastercard": "ma", "nike": "nke", "cocacola": "ko",
    "coca-cola": "ko", "pepsi": "pep", "mcdonald": "mcd", "walmart": "wmt",
    "intel": "intc", "amd": "amd", "ibm": "ibm", "cisco": "csco",
    "oracle": "orcl", "salesforce": "crm", "adobe": "adbe",
    "boeing": "ba", "caterpillar": "cat", "chevron": "cvx", "exxon": "xom",
    "exxonmobil": "xom", "shell": "shell", "bp": "bp", "uber": "uber",
    "airbnb": "abnb", "spotify": "spot", "paypal": "pypl",
    "sony": "6758", "toyota": "7203",
    "nintendo": "7974", "softbank": "9984", "honda": "7267",
    "tencent": "700", "alibaba": "9988", "xiaomi": "1810",
    "bhp": "bhp", "rio tinto": "rio", "nestle": "nesn",
    "nestlé": "nesn", "novartis": "novn", "roche": "rog",
    "siemens": "sie", "sap": "sap", "adidas": "ads",
    "lvmh": "mc", "loreal": "or", "airbus": "air",
}

def _tao_phan_tich_co_phieu_tg(ma, info):
    ma_upper = ma.upper()
    ten = info.get("ten", ma_upper)
    gia = info.get("gia", 0)
    if not gia:
        return (
            f"{MO_DAU}"
            f"\U0001f30d **{ma_upper} — {ten}**\n\n"
            "Rất tiếc, tôi chưa có dữ liệu giá cho cổ phiếu này."
        )
    pe = info.get("pe", 0)
    roe = info.get("roe", 0)
    vh = info.get("von_hoa", 0)
    th = info.get("tin_hieu", "")
    nganh = info.get("nganh", "")
    san = info.get("san", "")
    loai_thi_truong = "Mỹ" if san in ("NASDAQ", "NYSE") else "châu Âu" if san in ("Xetra", "Euronext", "LSE") else "châu Á" if san in ("TSE", "HOSE", "HKEX") else "quốc tế"
    dinh_giá = "hấp dẫn" if pe and pe < 15 else "hợp lý" if pe and pe < 25 else "cao" if pe and pe < 40 else "rất cao — kỳ vọng tăng trưởng lớn" if pe else ""
    quy_mo = "vốn hóa lớn (Mega-Cap)" if vh and vh > 200 else "vốn hóa vừa (Large-Cap)" if vh and vh > 50 else "vốn hóa trung bình (Mid-Cap)"
    return (
        f"{MO_DAU}"
        f"\U0001f30d **PHÂN TÍCH CỔ PHIẾU QUỐC TẾ: {ma_upper} — {ten}**\n\n"
        f"\U0001f4cc **THÔNG TIN CƠ BẢN**\n"
        + (f"• Ngành: **{nganh}**\n" if nganh else "")
        + (f"• Sàn niêm yết: **{san}** ({loai_thi_truong})\n" if san else "")
        + (f"• Vốn hóa: **${vh:,.1f} tỷ** — {quy_mo}\n" if vh else "")
        + "\n"
        f"\U0001f4ca **ĐỊNH GIÁ HIỆN TẠI**\n"
        f"• Giá: **${gia:,.2f}**\n"
        + (f"• PE: **{pe}x** — định giá {dinh_giá}\n" if pe else "")
        + (f"• ROE: **{roe}%**\n" if roe else "")
        + (f"• Tín hiệu: **{th}**\n" if th else "")
        + "\n"
        f"\U0001f4c9 **PHÂN TÍCH KỸ THUẬT**\n"
        f"• Hỗ trợ: **${info['gia_thap']:,.2f}** — vùng tích lũy\n"
        f"• Kháng cự: **${info['gia_cao']:,.2f}** — vùng chốt lời\n"
        f"• Xu hướng dài hạn: "
        + ("**TĂNG**" if th and ("mua" in th.lower() or "tích" in th.lower()) else
           "**GIẢM**" if th and ("bán" in th.lower() or "xấu" in th.lower()) else
           "**ĐI NGANG** — chờ breakout")
        + "\n\n"
        f"\U0001f4b0 **CHIẾN LƯỢC GIAO DỊCH**\n"
        f"\u2795 **Vùng mua:** ${info['gia_thap']:,.2f} → ${gia:,.2f}\n"
        f"\U0001f3af **Mục tiêu 1:** ${info['gia_cao']:,.2f} (+{(info['gia_cao']/gia-1)*100:.0f}%)\n"
        f"\U0001f3af **Mục tiêu 2:** ${info['gia_cao']*1.15:,.2f} (+{(info['gia_cao']*1.15/gia-1)*100:.0f}%)\n"
        + (f"\u274c **Cắt lỗ:** Dưới ${info['gia_thap']*0.85:,.2f}\n" if info.get('gia_thap') else "")
        + "\n"
        "\U0001f30d **BỐI CẢNH VĨ MÔ**\n"
        + (f"• **{ten}** thuộc thị trường {loai_thi_truong}. "
           f"Thị trường {loai_thi_truong} đang chịu ảnh hưởng từ: \n"
           f"  - Chính sách lãi suất của Fed (DXY, lợi suất TPCP)\n"
           f"  - Tăng trưởng GDP toàn cầu và thương mại quốc tế\n"
           f"  - Rủi ro địa chính trị (xung đột thương mại Mỹ-Trung)\n"
           if "Mỹ" in loai_thi_truong else
           f"  - ECB, BOJ chính sách tiền tệ\n  - Giá năng lượng và nguyên liệu\n")
        + "\n"
        "\U0001f50d **NHẬN ĐỊNH CHUYÊN GIA**\n"
        f"{ten} ({ma_upper}) là cổ phiếu {quy_mo} niêm yết trên {san}. "
        + (f"Ở mức PE {pe}x, định giá hiện tại là {dinh_giá}. " if pe else "")
        + "\"Thị trường chứng khoán toàn cầu luôn vận động theo chu kỳ. "
        "Điều quan trọng là mua đúng cổ phiếu, đúng thời điểm và giữ đủ lâu.\"\n\n"
        "\U0001f4a1 **LỜI KHUYÊN CHO NHÀ ĐẦU TƯ VIỆT NAM**\n"
        "• Đầu tư quốc tế giúp **đa dạng hóa rủi ro** khỏi thị trường VN\n"
        "• **Mua cổ phiếu Mỹ** qua quỹ ETF (VOO, VTI, QQQ) hoặc chứng chỉ lưu ký\n"
        "• Tỷ lệ khuyến nghị: **20-30%** danh mục cho cổ phiếu quốc tế\n"
        "• Sử dụng tài khoản chứng khoán quốc tế (SSI, Techcombank, hoặc Interactive Brokers)"
    )

def phan_tich_crypto(loai="bitcoin"):
    if loai == "bitcoin":
        return (
            f"{MO_DAU}"
            "\u20bf **PHÂN TÍCH CHUYÊN SÂU BITCOIN (BTC/USD)**\n\n"
            "\"Bitcoin là vàng kỹ thuật số, nhưng biến động gấp 10 lần vàng thật.\" — \
Một chuyên gia từng nói với tôi năm 2015 khi BTC còn $200.\n\n"
            "\U0001f4ca **TỔNG QUAN THỊ TRƯỜNG**\n"
            "• Giá hiện tại: **~$67,000-72,000** (biến động mạnh 24h)\n"
            "• Vốn hóa: **~$1,300 tỷ** — tài sản lớn thứ 10 thế giới\n"
            "• Halving gần nhất: Tháng 4/2024 (lần thứ 4)\n"
            "• Nguồn cung tối đa: **21 triệu BTC** — khan hiếm tuyệt đối\n\n"
            "\U0001f4c8 **PHÂN TÍCH CHU KỲ**\n"
            "| Chu kỳ | Giá đáy | Giá đỉnh | Tăng |\n"
            "|---|---|---|---|\n"
            "| 2012-2013 | $12 | $1,100 | **+9,167%** |\n"
            "| 2015-2017 | $200 | $19,600 | **+9,700%** |\n"
            "| 2018-2021 | $3,200 | $68,800 | **+2,050%** |\n"
            "| 2022-2025 | $15,500 | ? | 👉 **ĐANG DIỄN RA** |\n\n"
            "\U0001f4c9 **PHÂN TÍCH KỸ THUẬT BTC**\n"
            "• Hỗ trợ mạnh: **$58,000-60,000** (MA200 tuần)\n"
            "• Kháng cự ngắn hạn: **$73,000-74,000** (đỉnh cũ)\n"
            "• Kháng cự dài hạn: **$80,000-85,000** (vùng tích lũy 2021)\n"
            "• RSI (14 ngày): **58** — trung tính, chưa quá mua\n"
            "• MACD: Dương, nhưng đang thu hẹp — momentum yếu dần\n"
            "• Nếu phá $74,000: Mục tiêu **$85,000-100,000**\n"
            "• Nếu mất $58,000: Rủi ro về **$48,000-52,000**\n\n"
            "\U0001f4b0 **CHIẾN LƯỢC ĐẦU TƯ BTC**\n"
            "\u2795 **VÀO LỆNH:** $58,000-62,000 (DCA 4 tuần)\n"
            "\U0001f3af **MỤC TIÊU:** $85,000 (Q3/2025) → $100,000+ (2025-2026)\n"
            "\u274c **CẮT LỖ:** Đóng 50% nếu mất $52,000\n\n"
            "\U0001f30d **YẾU TỐ VĨ MÔ ẢNH HƯỞNG**\n"
            "\u2705 **ETF Bitcoin Spot được duyệt** (tháng 1/2024): Dòng vốn tổ chức\n"
            "\u2705 **Halving 2024**: Giảm 50% nguồn cung mới\n"
            "\u2705 **FED sắp cắt giảm lãi suất**: USD yếu → BTC tăng\n"
            "⚠️ **Quản lý rủi ro từ các chính phủ** (Mỹ, Đức bán BTC seized)\n"
            "⚠️ **Cạnh tranh từ Ethereum ETF** và các Layer-2\n\n"
            "\U0001f50d **NHẬN ĐỊNH CHUYÊN GIA**\n"
            "Bitcoin đang ở giai đoạn **giữa chu kỳ tăng**. Lịch sử cho thấy 12-18 tháng sau halving "
            "thường là đỉnh. Vùng $58,000-62,000 là cơ hội mua tốt. "
            "Tôi khuyên chỉ phân bổ **5-10%** danh mục vào BTC.\n\n"
            "\"Hãy mua Bitcoin khi nó đang sợ hãi và bán khi cả thế giới đang nói về nó.\"\n"
            "— Bài học từ một người đã mua BTC năm 2013 ở $100 và giữ đến nay."
        )
    elif loai == "ethereum":
        return (
            f"{MO_DAU}"
            "\U0001f539 **PHÂN TÍCH CHUYÊN SÂU ETHEREUM (ETH/USD)**\n\n"
            "Ethereum không chỉ là tiền điện tử — nó là **máy tính thế giới**. "
            "Hợp đồng thông minh của Ethereum là nền tảng cho toàn bộ hệ sinh thái DeFi, NFT, và Web3.\n\n"
            "\U0001f4ca **TỔNG QUAN**\n"
            "• Giá: **~$3,400-3,600**\n"
            "• Vốn hóa: **~$410 tỷ** — tiền điện tử lớn thứ 2\n"
            "• TVS DeFi: **~$50 tỷ** (hệ sinh thái)\n\n"
            "\U0001f4c9 **PHÂN TÍCH KỸ THUẬT**\n"
            "• Hỗ trợ: **$2,800-3,000**\n"
            "• Kháng cự: **$3,800-4,000**\n"
            "• ETH/BTC đang ở đáy 3 năm — ETH có thể outperform BTC\n\n"
            "\U0001f50d **NHẬN ĐỊNH**\n"
            "ETH đang bị định giá thấp hơn BTC trong chu kỳ này. "
            "ETF Ethereum spot được duyệt sẽ là catalyst mạnh. "
            "Tỷ lệ ETH/BTC ở vùng quá bán — cơ hội cho nhà đầu tư dài hạn."
        )
    return None


def phan_tich_vang():
    return (
        f"{MO_DAU}"
        "\U0001f947 **PHÂN TÍCH CHUYÊN SÂU THỊ TRƯỜNG VÀNG**\n\n"
        "\"Vàng là đồng tiền của các vị vua, là tài sản cuối cùng khi mọi thứ sụp đổ.\"\n"
        "— Trong 50 năm qua, vàng đã chứng kiến 4 đợt tăng giá lớn và vẫn giữ vững giá trị.\n\n"
        "\U0001f4ca **GIÁ VÀNG HÔM NAY**\n"
        "• **Vàng SJC (VN):** ~78-80 triệu VNĐ/lượng (mua vào - bán ra)\n"
        "• **Vàng thế giới (XAU/USD):** ~$2,350-2,400/oz\n"
        "• **Chênh lệch SJC - TG:** ~5-7 triệu — kiệt tác của độc quyền\n"
        "• **Giá vàng nhẫn 24K:** ~74-77 triệu/lượng — gần sát giá thế giới\n\n"
        "\U0001f4c8 **PHÂN TÍCH KỸ THUẬT VÀNG THẾ GIỚI**\n"
        "• Hỗ trợ mạnh: **$2,280-2,300/oz** (MA100 tuần)\n"
        "• Kháng cự gần: **$2,420-2,450/oz** (đỉnh lịch sử)\n"
        "• Xu hướng: **TĂNG DÀI HẠN** — kênh giá đi lên 5 năm\n"
        "• RSI (14): **62** — trung tính, còn dư địa tăng\n"
        "• MACD: Dương — momentum tăng còn mạnh\n\n"
        "\U0001f4b0 **CHIẾN LƯỢC ĐẦU TƯ VÀNG**\n"
        "⏹ **Vàng vật chất (SJC, nhẫn trơn):**\n"
        "  \u2795 Mua tích lũy khi giá điều chỉnh 3-5%\n"
        "  \U0001f3af Mục tiêu: $2,600-3,000/oz trong 12-18 tháng\n\n"
        "⏹ **Cổ phiếu vàng (PNJ, SJC trên sàn CK):**\n"
        "  \u2795 Mua khi giá vàng thế giới điều chỉnh về vùng $2,280-2,320\n"
        "  \U0001f3af P/E mục tiêu: 15-18x (hiện tại ~12x)\n\n"
        "⏹ **ETF vàng (GOLD, IAUM trên sàn Mỹ):**\n"
        "  \u2795 DCA hàng tháng — trung bình giá\n"
        "  \U0001f3af Phân bổ 10-20% danh mục vào vàng\n\n"
        "\U0001f30d **YẾU TỐ VĨ MÔ ẢNH HƯỞNG**\n"
        "\u2705 **FED cắt giảm lãi suất** — USD yếu, vàng tăng (lịch sử 100 năm)\n"
        "\u2705 **Ngân hàng trung ương mua ròng** — 1.000+ tấn/năm (kỷ lục)\n"
        "\u2705 **Căng thẳng địa chính trị** — Nga-Ukraine, Trung Đông, Biển Đông\n"
        "⚠️ **USD mạnh** (DXY > 105) — áp lực ngắn hạn lên vàng\n"
        "⚠️ **Lợi suất trái phiếu Mỹ tăng** — cạnh tranh với vàng\n\n"
        "\U0001f50d **NHẬN ĐỊNH CHUYÊN GIA**\n"
        "Tôi đã chứng kiến vàng tăng từ $250/oz năm 2001 lên $2,400/oz năm 2026. "
        "Trong 25 năm, đó là mức tăng **+860%** — tương đương 9,5%/năm. "
        "Vàng là **tấm bảo hiểm** cho danh mục đầu tư. Khi thị trường sụp đổ, "
        "vàng luôn là nơi trú ẩn cuối cùng.\n\n"
        "\"Khi bạn lo lắng về tương lai, hãy mua vàng. Khi bạn tự tin về tương lai, hãy mua cổ phiếu.\"\n"
        "— Bài học từ 50 năm đầu tư."
    )


def _tao_phan_tich_sieu_sau(ma, info):
    ma_upper = ma.upper()
    ten = info.get("ten", ma_upper)
    gia = info.get("gia", 0)
    if not gia:
        return (
            f"{MO_DAU}"
            f"\U0001f4ca **{ma_upper} — {ten}**\n\n"
            "Rất tiếc, tôi chưa có dữ liệu giá cho cổ phiếu này. "
            "Vui lòng thử lại sau hoặc yêu cầu phân tích mã khác."
        )
    pe = info.get("pe", 0)
    eps = info.get("eps", 0)
    roe = info.get("roe", 0)
    vh = info.get("von_hoa", 0)
    th = info.get("tin_hieu", "")
    nganh = info.get("nganh", "")
    pb = info.get("pb", 0)
    roic = info.get("roic", 0)
    no_vay = info.get("no_vay", 0)
    von_csh = info.get("von_csh", 0)
    de_ratio = info.get("de_ratio", 0)
    insider_pct = info.get("insider_pct", 0)
    pct_ngoai = info.get("pct_ngoai", 0)
    chu_tich = info.get("chu_tich", "")
    dt = info.get("dt_2025", 0)
    lnst = info.get("lnst_2025", 0)
    bien_ln = info.get("bien_ln", 0)
    ebitda = info.get("ebitda", 0)
    co_tuc_d = info.get("co_tuc_d", 0)
    co_tuc_pct = info.get("co_tuc_pct", 0)
    esg = info.get("esg_score", "")
    san = info.get("san", "")
    cp_luu_hanh = info.get("cp_luu_hanh", 0)
    dao_duc = info.get("dao_duc", "")
    gia_thap = info.get("gia_thap", 0)
    gia_cao = info.get("gia_cao", 0)

    diem_nhan = DIEM_NHAN_CO_PHIEU.get(ma, "")
    if diem_nhan:
        info_merge = dict(info)
        info_merge["ma"] = ma_upper
        diem_nhan = diem_nhan.format(**info_merge)

    dac_diem_nganh = {
        "ngân hàng": "Chất lượng tài sản, NIM, CASA, tỷ lệ nợ xấu",
        "thép": "Giá thép thế giới, công suất, chi phí nguyên liệu",
        "công nghệ": "Hợp đồng XK, nhân lực chất lượng cao, R&D",
        "bán lẻ": "Sức mua dân cư, mặt bằng bán lẻ, online-offline",
        "thực phẩm": "Thị phần, thương hiệu, chuỗi cung ứng",
        "dầu khí": "Giá dầu, sản lượng, biên lợi nhuận lọc dầu",
        "bất động sản": "Quỹ đất, pháp lý, tiến độ dự án, hàng tồn kho",
    }
    ytt_nganh = ""
    for key, desc in dac_diem_nganh.items():
        if key in nganh.lower():
            ytt_nganh = desc
            break
    if not ytt_nganh:
        ytt_nganh = "Triển vọng ngành, vị thế cạnh tranh, quản trị doanh nghiệp"

    dinh_gia_nhan_xet = f"PE {pe}x là {'thấp (định giá rẻ)' if pe and pe < 10 else 'hợp lý' if pe and pe < 18 else 'cao (cần tăng trưởng mạnh để hỗ trợ)'}" if pe else "cần xem xét thêm"
    roe_nhan_xet = f"ROE {roe}% là {'xuất sắc (>20%)' if roe and roe > 20 else 'tốt (15-20%)' if roe and roe > 15 else 'trung bình (10-15%)' if roe and roe > 10 else 'yếu (<10%)'}" if roe else ""
    de_nhan_xet = f"D/E {de_ratio}x là {'an toàn (<1x)' if de_ratio and de_ratio < 1 else 'cần theo dõi (1-2x)' if de_ratio and de_ratio < 2 else 'cao — cẩn trọng (>2x)'}" if de_ratio else ""

    so_sanh_dt_lnst = ""
    if dt and lnst:
        ty_suat = lnst / dt * 100
        so_sanh_dt_lnst = f"Biên lợi nhuận ròng: **{ty_suat:.1f}%** — doanh thu {dt:,.0f} tỷ tạo ra {lnst:,.0f} tỷ lợi nhuận"

    so_sanh_nganh = []
    for other_ma, other_info in STOCK_INFO.items():
        if other_ma == ma:
            continue
        if not other_info.get("nganh"):
            continue
        if nganh.lower() in other_info["nganh"].lower() or other_info["nganh"].lower() in nganh.lower():
            so_sanh_nganh.append((other_ma.upper(), other_info.get("pe", 0), other_info.get("roe", 0), other_info.get("von_hoa", 0)))
    so_sanh_nganh = so_sanh_nganh[:3]
    bang_so_sanh_nganh = ""
    if so_sanh_nganh:
        bang_so_sanh_nganh = "\n| Doanh nghiep | PE | ROE | Von hoa |\n|---|---|---|---|\n"
        if vh:
            bang_so_sanh_nganh += f"| **{ma_upper}** | **{pe}x** | **{roe}%** | **{vh:,.0f}t** |\n"
        else:
            bang_so_sanh_nganh += f"| **{ma_upper}** | **{pe}x** | **{roe}%** | N/A |\n"
        for sma, spe, sroe, svh in so_sanh_nganh:
            if svh:
                bang_so_sanh_nganh += f"| {sma} | {spe}x | {sroe}% | {svh:,.0f}t |\n"
            else:
                bang_so_sanh_nganh += f"| {sma} | {spe}x | {sroe}% | N/A |\n"

    return (
        f"{MO_DAU}"
        f"\U0001f3e1 **PHÂN TÍCH SIÊU SÂU: {ma_upper} — {ten}**\n\n"
        f"\"{ten} là một trong những doanh nghiệp {'đầu ngành' if roe and roe > 18 else 'tiềm năng'} "
        f"mà tôi đã theo dõi suốt 80 năm sự nghiệp. "
        f"Hãy nhìn vào bức tranh TOÀN CẢNH.\"\n\n"
        + (diem_nhan + "\n" if diem_nhan else "")
        + "\U0001f4cc **THÔNG TIN DOANH NGHIỆP**\n"
        + (f"• Ngành: **{nganh}**\n" if nganh else "")
        + (f"• Sàn: **{san}**" if san else "")
        + (f" | CP lưu hành: **{cp_luu_hanh:,}**\n" if cp_luu_hanh else "\n")
        + (f"• Chủ tịch: **{chu_tich}** — người cầm lái\n" if chu_tich else "")
        + (f"• Xếp hạng ESG: **{esg}** | Đạo đức KD: **{dao_duc}**\n" if esg else "")
        + "\n"
        f"\U0001f4ca **ĐỊNH GIÁ & THẨM ĐỊNH**\n"
        f"• Giá: **{gia:,} VND**"
        + (f" | Vốn hóa: **{vh:,.0f} tỷ**\n" if vh else "\n")
        + (f"• PE: **{pe}x**" if pe else "")
        + (f" | PB: **{pb}x**" if pb else "")
        + (f" | EPS: **{eps:,} VND**" if eps else "")
        + (f" | ROE: **{roe}%**\n" if roe else "\n")
        + (f"• Tín hiệu thị trường: **{th}**\n" if th else "")
        + f"• Nhận xét: {dinh_gia_nhan_xet} | {roe_nhan_xet} | {de_nhan_xet}\n"
        + "\n"
        f"\U0001f4c9 **PHÂN TÍCH KỸ THUẬT — 5 CHỈ BÁO**\n"
        + (f"• **RSI(14):** Đang {'quá mua (>70)' if th and 'mua' in th.lower() else 'quá bán (<30)' if th and 'bán' in th.lower() else 'trung tính (30-70)'} — {'thận trọng chốt lời' if th and 'mua' in th.lower() else 'cơ hội mua vào' if th and 'bán' in th.lower() else 'không có tín hiệu rõ ràng'}\n")
        + (f"• **MACD:** {'Đường MACD cắt lên trên đường tín hiệu → TÍN HIỆU MUA' if th and 'mua' in th.lower() else 'Đường MACD cắt xuống dưới đường tín hiệu → TÍN HIỆU BÁN' if th and 'bán' in th.lower() else 'Đang giao nhau — chờ xác nhận'}\n")
        + f"• **MA(50) & MA(200):** "
        + (f"Giá trên MA50 → xu hướng ngắn hạn TĂNG" if th and ('mua' in th.lower() or 'tích' in th.lower()) else "Giá dưới MA50 → xu hướng ngắn hạn GIẢM" if th and 'bán' in th.lower() else "Giá quanh MA50 → xu hướng CHƯA RÕ")
        + f"\n• **Hỗ trợ mạnh:** {gia_thap:,} VND — vùng tích lũy | **Kháng cự gần:** {gia_cao:,} VND — vùng chốt lời\n"
        + f"• **Bollinger Bands:** {'Giá chạm band dưới → oversold, cơ hội mua' if th and 'bán' in th.lower() else 'Giá chạm band trên → overbought, thận trọng' if th and 'mua' in th.lower() else 'Giá trong dải → xu hướng bình thường'}"
        + "\n\n"
        f"\U0001f4b0 **CHIẾN LƯỢC GIAO DỊCH 3 THỜI HẠN**\n"
        f"\U0001f535 **Ngắn hạn (1-3 tháng):** "
        + ("Mua tại vùng hỗ trợ, chốt lời tại kháng cự. Stop-loss chặt."
           if th and ('mua' in th.lower() or 'tích' in th.lower() or 'tốt' in th.lower())
           else "Đứng ngoài quan sát. Chưa có tín hiệu vào lệnh rõ ràng."
           if th and ('bán' in th.lower() or 'giảm' in th.lower() or 'xấu' in th.lower())
           else "Chờ breakout khỏi vùng tích lũy mới hành động.")
        + "\n"
        f"\U0001f7e2 **Trung hạn (3-6 tháng):** "
        + f"Mua tích lũy tại {gia_thap:,} → {gia:,} VND. Mục tiêu {gia:,} → {gia_cao:,} VND (+{(gia_cao/gia-1)*100:.1f}%)."
        + "\n"
        f"\U0001f534 **Dài hạn (6-18 tháng):** "
        + (f"{ten} là khoản đầu tư nắm giữ {'xuất sắc' if roe and roe > 18 else 'tốt' if roe and roe > 12 else 'cần theo dõi'}. "
           f"Tích lũy mạnh tại vùng {gia_thap:,} VND.")
        + f"\n\u274c **Cắt lỗ cứng:** Dưới {gia_thap:,} VND (mất ngưỡng hỗ trợ, thoát ngay)\n"
        + (f"\U0001f4c8 **Cổ tức:** ~{co_tuc_pct}% ({co_tuc_d:,} đ/CP) — thêm vào tổng lợi nhuận\n" if co_tuc_d else "")
        + "\n"
        f"\U0001f50e **TÀI CHÍNH CHUYÊN SÂU — BẢNG CÂN ĐỐI & HIỆU SUẤT**\n"
        + (f"• Vốn CSH: **{von_csh:,.0f} tỷ**" if von_csh else "")
        + (f" | Nợ vay: **{no_vay:,.0f} tỷ**" if no_vay else "")
        + (f" | D/E: **{de_ratio}x** — {de_nhan_xet}\n" if de_ratio else "\n")
        + (f"• ROIC: **{roic}%**" if roic else "")
        + (f" | Biên LN ròng: **{bien_ln}%\n" if bien_ln else "\n")
        + (f"• Doanh thu 2025: **{dt:,.0f} tỷ**" if dt else "")
        + (f" | LNST 2025: **{lnst:,.0f} tỷ**" if lnst else "")
        + (f" | EBITDA: **{ebitda:,.0f} tỷ**\n" if ebitda else "\n")
        + (f"• {so_sanh_dt_lnst}\n" if so_sanh_dt_lnst else "")
        + (f"• Sở hữu nội bộ: **{insider_pct}%**" if insider_pct else "")
        + (f" | Sở hữu ngoại: **{pct_ngoai}%**\n" if pct_ngoai else "\n")
        + (f"• Cổ tức: **{co_tuc_d:,} đ/CP ({co_tuc_pct}%)** — dòng tiền thụ động\n" if co_tuc_d else "")
        + "\n"
        f"\U0001f4ca **SO SÁNH NGÀNH ({nganh})**\n"
        + (bang_so_sanh_nganh if bang_so_sanh_nganh else "Không có đủ dữ liệu so sánh ngành.\n")
        + "\n"
        f"\U0001f30d **BỐI CẢNH VĨ MÔ — TÁC ĐỘNG ĐẾN {ma_upper}**\n"
        "• **VN-Index:** Đang trong xu hướng "
        + ("TĂNG — thuận lợi, dòng tiền vào mạnh" if th and ("mua" in th.lower() or "tích" in th.lower()) else
           "GIẢM — thận trọng, ưu tiên phòng thủ" if th and ("bán" in th.lower() or "giảm" in th.lower() or "xấu" in th.lower()) else
           "ĐI NGANG — thị trường chọn lọc, phân hóa mạnh")
        + "\n"
        "• **Lãi suất:** NHNN giữ lãi suất điều hành 4,5% — hỗ trợ mặt bằng định giá\n"
        "• **Tỷ giá:** USD/VND ~25.500 — áp lực từ Fed, nhưng dự trữ ngoại hối ổn\n"
        "• **Đầu tư công:** Giải ngân kỷ lục — cao tốc Bắc-Nam, Long Thành, vành đai 4\n"
        "• **Khối ngoại:** "
        + ("Mua ròng mạnh — tín hiệu tin cậy cao"
           if pct_ngoai and pct_ngoai > 20 else
           "Bán ròng — áp lực lên thanh khoản" if pct_ngoai and pct_ngoai < 10 else
           "Giao dịch thăm dò — chưa rõ xu hướng")
        + "\n\n"
        f"\U0001f9e9 **MA TRẬN RỦI RO — {ma_upper}**\n"
        "| Loại rủi ro | Mức độ | Tác động | Giảm thiểu |\n"
        "|---|---|---|---|\n"
        + (f"| Rủi ro thị trường | {'Cao' if th and ('bán' in th.lower() or 'xấu' in th.lower()) else 'Trung bình' if th and ('mua' in th.lower() or 'tích' in th.lower()) else 'TB'} | {'Giảm giá mạnh nếu VN-Index điều chỉnh' if th and ('bán' in th.lower() or 'xấu' in th.lower()) else 'Biến động trong biên độ hẹp'} | Đa dạng hóa danh mục |\n")
        + (f"| Rủi ro ngành ({nganh}) | {'Cao' if de_ratio and de_ratio > 2 else 'Trung bình' if de_ratio and de_ratio > 1 else 'Thấp'} | {'Biến động giá đầu vào/đầu ra' if de_ratio and de_ratio > 2 else 'Cạnh tranh trong ngành'} | Theo dõi chỉ số ngành |\n")
        + (f"| Rủi ro tài chính (D/E) | {'Cao' if de_ratio and de_ratio > 2 else 'TB' if de_ratio and de_ratio > 1 else 'Thấp'} | {'Áp lực trả nợ, chi phí lãi vay cao' if de_ratio and de_ratio > 2 else 'Quản trị vốn hợp lý'} | Giám sát dòng tiền |\n")
        + "| Rủi ro thanh khoản | TB | Khó thoát khi thị trường xấu | Đặt lệnh giới hạn |\n\n"
        "\U0001f50d **NHẬN ĐỊNH CHUYÊN GIA — 80 NĂM KINH NGHIỆM**\n"
        f"\"Sau 80 năm trên thị trường tài chính, tôi đã học được rằng: "
        f"{ten} là một {'cổ phiếu VUA — thuộc về những người có tầm nhìn dài hạn' if roe and roe > 18 else 'cổ phiếu TĂNG TRƯỞNG — phù hợp với NĐT chấp nhận rủi ro' if roe and roe > 12 else 'khoản đầu tư PHÒNG THỦ — bảo toàn vốn là ưu tiên'}.\"\n\n"
        f"Vùng giá hiện tại {gia:,} VND với PE {pe}x là "
        + ("**CƠ HỘI MUA** hiếm có. Tôi khuyên bạn nên mua dần trong vùng hỗ trợ." if pe and pe < 10 else
           "**HỢP LÝ** để tích lũy cho dài hạn." if pe and pe < 18 else
           "**CAO** — cần kiên nhẫn chờ đợi mức giá tốt hơn.")
        + "\n\n"
        "\U0001f4a0 **LỜI KHUYÊN CUỐI CÙNG**\n"
        "\"Biết mười thứ mà chỉ làm một thứ tốt, hơn biết một thứ mà làm mười thứ dở.\" "
        "Hãy tập trung vào những doanh nghiệp tốt nhất. Không cần phải giao dịch mỗi ngày. "
        "Mua tốt, ngồi yên, và để thời gian làm việc cho bạn.\n\n"
        f"\u2795 **KHUYẾN NGHỊ:** {ma_upper} phù hợp với NĐT "
        + ("**TĂNG TRƯỞNG** — mua tại vùng hỗ trợ" if pe and pe < 12 else
           "**GIÁ TRỊ** — nắm giữ dài hạn" if pe and pe < 18 else
           "**THẬN TRỌNG** — chờ mức giá tốt hơn")
        + " | **Mức độ rủi ro:** "
        + ("**THẤP** — phù hợp mọi danh mục" if de_ratio and de_ratio < 1 and roe and roe > 15 else
           "**TRUNG BÌNH** — chiếm 10-15% danh mục" if de_ratio and de_ratio < 2 else
           "**CAO** — chiếm <5% danh mục")
        + "\n\n\u2696\ufe0f **HỘI ĐỒNG CHUYÊN GIA KGU ROBO-ADVISOR — KẾT LUẬN**\n\n"
        "\U0001f535 **Chuyên gia vĩ mô (40 năm):** "
        + (f"\"{ma_upper} hoạt động trong bối cảnh VN-Index {'tăng trưởng tích cực' if th and ('mua' in th.lower() or 'tích' in th.lower()) else 'điều chỉnh'}. "
           "Lãi suất duy trì thấp hỗ trợ định giá.\""
           if th else "")
        + "\n"
        "\U0001f7e2 **Chuyên gia kỹ thuật (30 năm):** "
        + (f"\"RSI {'trên 70 - quá mua, thận trọng' if th and 'mua' in th.lower() else 'dưới 30 - quá bán, cơ hội mua' if th and 'bán' in th.lower() else 'trung tính - chờ breakout'}. "
           f"Xu hướng dài hạn vẫn {'tích cực' if th and ('mua' in th.lower() or 'tích' in th.lower()) else 'cần xác nhận'}.\"")
        + "\n"
        "\U0001f534 **Chuyên gia cơ bản (25 năm):** "
        + f"\"PE {pe}x, ROE {roe}%, D/E {de_ratio}x — {'cơ bản rất tốt, xứng đáng trong danh mục dài hạn' if roe and roe > 15 and de_ratio and de_ratio < 1.5 else 'cơ bản ổn, cần theo dõi thêm các quý tới' if roe and roe > 10 else 'cơ bản yếu, cần thận trọng'}.\""
        + "\n"
        "\u26a1 **Chuyên gia rủi ro (20 năm):** "
        + (f"\"Rủi ro chính là {'đòn bẩy cao' if de_ratio and de_ratio > 2 else 'biến động ngành' if de_ratio and de_ratio > 1 else 'rủi ro thị trường chung'}. "
           f"Khuyến nghị {'phân bổ <5% danh mục' if de_ratio and de_ratio > 2 else 'phân bổ 10-15% danh mục'}.\"")
        + "\n\n"
        "\U0001f451 **KẾT LUẬN CUỐI CÙNG CỦA HỘI ĐỒNG:**\n"
        + (f"\"{ma_upper} là {'CƠ HỘI MUA TỐT' if pe and pe < 12 and roe and roe > 18 else 'KHOẢN ĐẦU TƯ HỢP LÝ' if pe and pe < 16 and roe and roe > 14 else 'KHOẢN ĐẦU TƯ CẦN THẬN TRỌNG'}. "
           "Hội đồng chuyên gia KGU đã phân tích và đi đến thống nhất: "
           + ("MUA tại vùng giá hiện tại. Đây là cơ hội hiếm có. "
              if pe and pe < 10 and roe and roe > 18 else
              "TÍCH LŨY dần trong 3-6 tháng. Không nên mua một lần. "
              if pe and pe < 14 else
              "CHỜ ĐỢI mức giá tốt hơn. Kiên nhẫn là chìa khóa.") +
           "\"\n\n"
           "— KGU Robo-Advisor, Đại học Kiên Giang, 2026"
        )
    )

def xu_ly_bo_dau(text):
    char_map = {
        'à':'a','á':'a','ả':'a','ã':'a','ạ':'a','ă':'a','ắ':'a','ằ':'a','ẳ':'a','ẵ':'a','ặ':'a',
        'â':'a','ấ':'a','ầ':'a','ẩ':'a','ẫ':'a','ậ':'a',
        'è':'e','é':'e','ẻ':'e','ẽ':'e','ẹ':'e','ê':'e','ế':'e','ề':'e','ể':'e','ễ':'e','ệ':'e',
        'ì':'i','í':'i','ỉ':'i','ĩ':'i','ị':'i',
        'ò':'o','ó':'o','ỏ':'o','õ':'o','ọ':'o','ô':'o','ố':'o','ồ':'o','ổ':'o','ỗ':'o','ộ':'o',
        'ơ':'o','ớ':'o','ờ':'o','ở':'o','ỡ':'o','ợ':'o',
        'ù':'u','ú':'u','ủ':'u','ũ':'u','ụ':'u','ư':'u','ứ':'u','ừ':'u','ử':'u','ữ':'u','ự':'u',
        'ỳ':'y','ý':'y','ỷ':'y','ỹ':'y','ỵ':'y',
        'đ':'d','Đ':'d',
        'À':'a','Á':'a','Ả':'a','Ã':'a','Ạ':'a','Ằ':'a','Ắ':'a',
        'Â':'a','Ấ':'a','Ầ':'a','Ẩ':'a','Ẫ':'a','Ậ':'a',
        'È':'e','É':'e','Ẻ':'e','Ẽ':'e','Ẹ':'e','Ê':'e','Ế':'e','Ề':'e','Ể':'e','Ễ':'e','Ệ':'e',
        'Ì':'i','Í':'i','Ỉ':'i','Ĩ':'i','Ị':'i',
        'Ò':'o','Ó':'o','Ỏ':'o','Õ':'o','Ọ':'o','Ô':'o','Ố':'o','Ồ':'o','Ổ':'o','Ỗ':'o','Ộ':'o',
        'Ơ':'o','Ớ':'o','Ờ':'o','Ở':'o','Ỡ':'o','Ợ':'o',
        'Ù':'u','Ú':'u','Ủ':'u','Ũ':'u','Ụ':'u','Ư':'u','Ứ':'u','Ừ':'u','Ử':'u','Ữ':'u','Ự':'u',
        'Ỳ':'y','Ý':'y','Ỷ':'y','Ỹ':'y','Ỵ':'y',
    }
    return ''.join(char_map.get(c, c) for c in text)

def tim_thong_tin_co_phieu(cau_thuong, cau_khong_dau):
    for ma in sorted(STOCK_INFO.keys(), key=len, reverse=True):
        if ma in cau_thuong or ma in cau_khong_dau:
            info = STOCK_INFO[ma]
            if any(kw in cau_thuong or kw in cau_khong_dau for kw in
                   ["phân tích", "phan tich", "giá", "gia", "mua", "bán", "ban",
                    "khuyến nghị", "khuyen nghi", "định giá", "dinh gia",
                    "phân tích kỹ thuật", "chỉ báo", "chi bao"]):
                return _tao_phan_tich_sieu_sau(ma, info)
            ten = info.get("ten", ma.upper())
            return (
                f"\U0001f4ca **{ten} (ma: {ma.upper()})**\n\n"
                f"• Gia hien tai: **{info['gia']:,} VND**\n"
                + (f"• Nganh: **{info['nganh']}**\n" if info.get('nganh') else "")
                + (f"• PE: **{info['pe']}**" if info.get('pe') else "")
                + (f" | PB: **{info['pb']}**" if info.get('pb') else "")
                + (f" | EPS: **{info['eps']:,} VND**\n" if info.get('eps') else "\n")
                + (f"• ROE: **{info['roe']}%**" if info.get('roe') else "")
                + (f" | ROIC: **{info['roic']}%**" if info.get('roic') else "")
                + (f" | Vốn hóa: **{info['von_hoa']:,.0f} tỷ**\n" if info.get('von_hoa') else "\n")
                + (f"• Tín hiệu: **{info['tin_hieu']}**\n" if info.get('tin_hieu') else "")
                + (f"• Chủ tịch: **{info['chu_tich']}**\n" if info.get('chu_tich') else "")
                + (f"• Nợ vay: **{info['no_vay']:,.0f} tỷ**" if info.get('no_vay') else "")
                + (f" | D/E: **{info['de_ratio']}x**" if info.get('de_ratio') else "")
                + (f" | Vốn CSH: **{info['von_csh']:,.0f} tỷ**\n" if info.get('von_csh') else "\n")
                + (f"• Sở hữu nội bộ: **{info['insider_pct']}%**" if info.get('insider_pct') else "")
                + (f" | Sở hữu ngoại: **{info['pct_ngoai']}%**\n" if info.get('pct_ngoai') else "\n")
                + (f"• Ho tro: **{info['gia_thap']:,} VND** | Khang cuc: **{info['gia_cao']:,} VND**\n" if info.get('gia_thap') else "")
                + (f"• KL TB: **{info['khoi_luong_tb']}**\n" if info.get('khoi_luong_tb') else "")
                + (f"• Sàn: **{info['san']}** | CP lưu hành: **{info['cp_luu_hanh']:,}**\n" if info.get('cp_luu_hanh') else "")
                + "\n\U0001f4ac Ban co muon phan tich CHI TIET ve **{ten}** khong?\n".format(ten=ten)
                + f"Go: \"phan tich {ma}\" de xem phan tich chuyen sau!"
            )
    return None

def tim_so_sanh(cau_thuong, cau_khong_dau):
    matched_stocks = []
    for ma in STOCK_INFO:
        if ma in cau_thuong or ma in cau_khong_dau:
            if len(matched_stocks) < 7:
                matched_stocks.append(ma)
    if len(matched_stocks) < 2:
        return None

    so_luong = len(matched_stocks)
    ten_cot = " | ".join(
        f"**{STOCK_INFO[m].get('ten', m.upper()).split('(')[0].strip()}**"
        for m in matched_stocks
    )
    header = f"| Chi tieu | {ten_cot} |"
    separator = "|" + "---|" * (so_luong + 1)

    def hang(label, key, fmt="{:,}", dieu_kien=None):
        values = []
        for m in matched_stocks:
            val = STOCK_INFO[m].get(key, 0)
            if dieu_kien and not dieu_kien(val):
                values.append("N/A")
            else:
                try:
                    values.append(fmt.format(val))
                except:
                    values.append(str(val))
        return f"| {label} | " + " | ".join(values) + " |"

    bang = header + "\n" + separator + "\n"
    bang += hang("Nganh", "nganh", "{}", lambda v: v) + "\n"
    bang += hang("Gia", "gia", "{:,}", lambda v: v) + "\n"
    bang += hang("PE", "pe", "{}x", lambda v: v) + "\n"
    bang += hang("PB", "pb", "{}x", lambda v: v) + "\n"
    bang += hang("EPS", "eps", "{:,}", lambda v: v) + "\n"
    bang += hang("ROE", "roe", "{}%", lambda v: v) + "\n"
    bang += hang("ROIC", "roic", "{}%", lambda v: v) + "\n"
    bang += hang("D/E", "de_ratio", "{}x", lambda v: v) + "\n"
    bang += hang("No vay", "no_vay", "{:,.0f}t", lambda v: v) + "\n"
    bang += hang("Von hoa", "von_hoa", "{:,.0f}t", lambda v: v) + "\n"
    bang += hang("NN nuoc ngoai", "pct_ngoai", "{}%", lambda v: v) + "\n"
    bang += hang("Co tuc", "co_tuc_pct", "{}%", lambda v: v) + "\n"

    pe_values = [(STOCK_INFO[m].get("pe", 0), m) for m in matched_stocks]
    pe_values = [(p, m) for p, m in pe_values if p]
    re_nhat = pe_values[0][1] if pe_values else matched_stocks[0]

    return (
        f"{MO_DAU}"
        f"\U0001f9d1\u200d\U0001f4bc **SO SANH {so_luong} CO PHIEU**\n\n"
        + bang
        + f"\n\U0001f50d **NHAN DINH:**\n"
        + f"{STOCK_INFO[re_nhat].get('ten', re_nhat.upper())} co PE re nhat ({STOCK_INFO[re_nhat].get('pe', 0)}x) trong nhom.\n"
        + "\"Da dang hoa la bua trua mien phi duy nhat trong tai chinh. "
        + "Khong bo tat ca trung vao mot ro.\"\n\n"
        + "\U0001f4a1 **GOI Y:** Ban co muon phan tich CHI TIET tung ma khong?\n"
        + "Hay go: \"phan tich " + ", phan tich ".join(m.upper() for m in matched_stocks[:3]) + "\""
    )

def tim_thong_tin_thi_truong(cau_thuong):
    for key, content in THI_TRUONG_ANALYSIS.items():
        if key in cau_thuong:
            return content
    return None

THI_TRUONG_TU_KHOA = {}
for key in THI_TRUONG_ANALYSIS:
    no_dau = xu_ly_bo_dau(key)
    THI_TRUONG_TU_KHOA[key] = key
    if no_dau != key:
        THI_TRUONG_TU_KHOA[no_dau] = key

QUY_THE_GIOI = {
    "berkshire hathaway": {
        "ten": "Berkshire Hathaway (BRK.B)",
        "chu_tich": "Warren Buffett (94 tuổi) — \"Nhà hiền triết Omaha\"",
        "nam_thanh_lap": 1965,
        "von_hoa": "$950 tỷ",
        "co_phieu_dau_nganh": "AAPL (40% danh mục), BAC, AXP, KO, OXY",
        "trieu_ly": "\"Định giá doanh nghiệp, không dự đoán thị trường\"",
        "phong_cach": "Đầu tư giá trị — mua doanh nghiệp tốt với giá hợp lý",
        "hieu_suat": "Lợi nhuận kép 19.8%/năm trong 58 năm — gấp 4.800 lần S&P 500",
        "bai_hoc": "\"Chỉ số quan trọng nhất là chỉ số thông minh. Không phải IQ của bạn, mà là khả năng kiểm soát cảm xúc\"",
    },
    "blackrock": {
        "ten": "BlackRock Inc. (BLK)",
        "chu_tich": "Larry Fink",
        "nam_thanh_lap": 1988,
        "von_hoa": "$10.500 tỷ (AUM — tài sản quản lý)",
        "co_phieu_dau_nganh": "Apple, Microsoft, Nvidia, Amazon, Meta — nắm 5-8% mỗi công ty S&P 500",
        "trieu_ly": "\"Tái cấu trúc tài chính toàn cầu\" thông qua ETF (iShares)",
        "phong_cach": "Quản lý thụ động — ETF và quỹ chỉ số là cốt lõi",
        "hieu_suat": "Largest asset manager thế giới — quản lý $10.5 nghìn tỷ",
        "bai_hoc": "Đa dạng hóa qua ETF là cách đầu tư thông minh cho NĐT cá nhân",
    },
    "vanguard": {
        "ten": "Vanguard Group",
        "chu_tich": "John Bogle (sáng lập, đã mất), Tim Buckley (CEO)",
        "nam_thanh_lap": 1975,
        "von_hoa": "$8.000 tỷ (AUM)",
        "co_phieu_dau_nganh": "S&P 500 (VOO), Total Market (VTI), Total Bond (BND)",
        "trieu_ly": "\"Đầu tư chỉ số là cách tốt nhất cho đa số nhà đầu tư\"",
        "phong_cach": "Đầu tư chỉ số chi phí thấp — phí quản lý 0.03-0.10%",
        "hieu_suat": "Phí thấp nhất ngành — tiết kiệm $100K+ phí trong 30 năm so với quỹ chủ động",
        "bai_hoc": "Chi phí là yếu tố quyết định. Phí 1% mỗi năm = mất 30% lợi nhuận trong 30 năm",
    },
    "fidelity": {
        "ten": "Fidelity Investments",
        "chu_tich": "Abigail Johnson",
        "nam_thanh_lap": 1946,
        "von_hoa": "$4.500 tỷ (AUM)",
        "co_phieu_dau_nganh": "Quỹ Magellan, Contrafund, Blue Chip Growth",
        "trieu_ly": "\"Nhà đầu tư huyền thoại\" Peter Lynch — \"Mua những gì bạn biết\"",
        "phong_cach": "Chủ động + thụ động — quỹ chủ động nổi tiếng",
        "hieu_suat": "Peter Lynch đạt 29.2%/năm trong 13 năm quản lý Magellan (1977-1990)",
        "bai_hoc": "\"Mua cổ phiếu của công ty mà bạn hiểu rõ\" — đầu tư vào kiến thức của mình",
    },
    "bridgewater": {
        "ten": "Bridgewater Associates",
        "chu_tich": "Ray Dalio",
        "nam_thanh_lap": 1975,
        "von_hoa": "$150 tỷ (AUM)",
        "co_phieu_dau_nganh": "All Weather Portfolio — vĩ mô toàn cầu",
        "trieu_ly": "\"Máy kinh tế\" — hiểu chu kỳ nợ ngắn hạn và dài hạn",
        "phong_cach": "Đầu tư vĩ mô — phòng hộ rủi ro, đa dạng hóa tối đa",
        "hieu_suat": "All Weather: 8-10%/năm với rủi ro rất thấp trong 30 năm",
        "bai_hoc": "\"Nguyên tắc\" (Principles) — xây dựng hệ thống quyết định dựa trên dữ liệu",
    },
    "templeton": {
        "ten": "Franklin Templeton Investments",
        "chu_tich": "Sir John Templeton (sáng lập)",
        "nam_thanh_lap": 1947,
        "von_hoa": "$1.400 tỷ (AUM)",
        "co_phieu_dau_nganh": "Đầu tư giá trị toàn cầu — thị trường mới nổi",
        "trieu_ly": "\"Mua khi người khác sợ hãi nhất, bán khi người khác tham lam nhất\"",
        "phong_cach": "Đầu tư giá trị ngược chiều (contrarian value)",
        "hieu_suat": "Mua cổ phiếu Nhật sau Thế chiến 2 — lợi nhuận 100 lần",
        "bai_hoc": "Cơ hội lớn nhất đến khi bi quan tột cùng",
    },
}

QUY_KW = {
    "berkshire": "berkshire hathaway", "buffett": "berkshire hathaway", "warren": "berkshire hathaway",
    "blackrock": "blackrock", "larry fink": "blackrock", "fink": "blackrock",
    "vanguard": "vanguard", "bogle": "vanguard", "jack bogle": "vanguard",
    "fidelity": "fidelity", "peter lynch": "fidelity", "lynch": "fidelity", "magellan": "fidelity",
    "bridgewater": "bridgewater", "ray dalio": "bridgewater", "dalio": "bridgewater", "all weather": "bridgewater",
    "templeton": "templeton", "john templeton": "templeton", "sir john": "templeton",
    "quỹ đầu tư": "general", "quy dau tu": "general", "quỹ lớn": "general", "quy lon": "general",
    "fund": "general", "quỹ tương hỗ": "general", "quy tuong ho": "general", "mutual fund": "general",
    "quỹ chỉ số": "vanguard", "quy chi so": "vanguard", "index fund": "vanguard",
    "etf": "vanguard", "quỹ etf": "vanguard",
}

def phan_tich_quy_lon(query_key, thong_tin):
    ten = thong_tin["ten"]
    return (
        f"{MO_DAU}"
        f"\U0001f3e6 **PHÂN TÍCH QUỸ ĐẦU TƯ LỚN: {ten}**\n\n"
        f"\U0001f4cc **THÔNG TIN CƠ BẢN**\n"
        f"• Tên quỹ: **{ten}**\n"
        f"• Lãnh đạo: **{thong_tin['chu_tich']}**\n"
        f"• Năm thành lập: **{thong_tin['nam_thanh_lap']}**\n"
        f"• Tài sản quản lý (AUM): **{thong_tin['von_hoa']}**\n\n"
        f"\U0001f4c8 **DANH MỤC ĐẦU TƯ CHÍNH**\n"
        f"• {thong_tin['co_phieu_dau_nganh']}\n\n"
        f"\U0001f50e **TRIẾT LÝ & PHONG CÁCH**\n"
        f"• **Triết lý:** {thong_tin['trieu_ly']}\n"
        f"• **Phong cách:** {thong_tin['phong_cach']}\n"
        f"• **Hiệu suất:** {thong_tin['hieu_suat']}\n\n"
        f"\U0001f4a1 **BÀI HỌC CHO NHÀ ĐẦU TƯ VIỆT NAM**\n"
        f"{thong_tin['bai_hoc']}\n\n"
        "\U0001f451 **HỘI ĐỒNG CHUYÊN GIA KGU — KẾT LUẬN**\n"
        f"\"Học từ các quỹ lớn nhất thế giới: {ten} dạy chúng ta rằng "
        f"{'đầu tư giá trị dài hạn' if query_key == 'berkshire hathaway' else 'đa dạng hóa qua ETF' if query_key == 'blackrock' else 'chi phí thấp là chìa khóa' if query_key == 'vanguard' else 'mua những gì bạn biết' if query_key == 'fidelity' else 'hiểu chu kỳ vĩ mô' if query_key == 'bridgewater' else 'mua khi người khác sợ hãi' if query_key == 'templeton' else 'kỷ luật đầu tư'} "
        f"là chìa khóa thành công. Áp dụng nguyên tắc này vào thị trường Việt Nam: "
        f"mua HPG, VCB, FPT, VNM và nắm giữ dài hạn.\"\n\n"
        f"— KGU Robo-Advisor, Đại học Kiên Giang, 2026"
    )

def phan_tich_tat_ca_quy():
    noi_dung = f"{MO_DAU}"
    noi_dung += "\U0001f3e6 **TẤT CẢ QUỸ ĐẦU TƯ LỚN TRÊN THẾ GIỚI**\n\n"
    noi_dung += "Đây là 6 quỹ đầu tư vĩ đại nhất lịch sử mà tôi theo dõi suốt 80 năm:\n\n"
    for key, q in QUY_THE_GIOI.items():
        noi_dung += (
            f"\U0001f539 **{q['ten']}** (AUM: {q['von_hoa']})\n"
            f"   • Lãnh đạo: {q['chu_tich']}\n"
            f"   • Triết lý: {q['trieu_ly']}\n"
            f"   • Bài học: {q['bai_hoc']}\n\n"
        )
    noi_dung += "\U0001f447 Hãy hỏi chi tiết về từng quỹ: \"phân tích Berkshire\", \"phân tích BlackRock\"..."
    return noi_dung

def tim_quy(cau_thuong, cau_khong_dau):
    for kw, key in QUY_KW.items():
        if kw in cau_thuong or kw in cau_khong_dau:
            if key == "general":
                return phan_tich_tat_ca_quy()
            if key in QUY_THE_GIOI:
                return phan_tich_quy_lon(key, QUY_THE_GIOI[key])
    return None

def tim_cau_tra_loi(cau_hoi, lich_su=None):
    cau_thuong = cau_hoi.lower().strip()
    cau_khong_dau = xu_ly_bo_dau(cau_thuong)

    for tu_khoa in ["tạm biệt", "cảm ơn", "hello", "xin chào"]:
        if tu_khoa in cau_thuong or xu_ly_bo_dau(tu_khoa) in cau_khong_dau:
            return HOI_DAP.get(tu_khoa, random.choice(CAU_TRA_LOI_MAC_DINH))

    try:
        from .ai_advisors import hoi_dong_ai_tu_van
        tra_loi = hoi_dong_ai_tu_van(cau_hoi)
        if tra_loi and len(tra_loi) > 50:
            return tra_loi
    except Exception:
        pass

    try:
        from .ai_advisor import tra_loi_ai
        if lich_su is None:
            lich_su = []
        tra_loi = tra_loi_ai(cau_hoi, lich_su)
        if tra_loi and "[" not in tra_loi[:5]:
            return tra_loi
    except:
        pass

    if "so sanh" in cau_thuong or "so sánh" in cau_thuong:
        kq = tim_so_sanh(cau_thuong, cau_khong_dau)
        if kq:
            return kq

    ma_count = sum(1 for ma in STOCK_INFO if ma in cau_thuong or ma in cau_khong_dau)
    if ma_count >= 2:
        kq = tim_so_sanh(cau_thuong, cau_khong_dau)
        if kq:
            return kq

    if any(kw in cau_thuong for kw in ["cổ phiếu thế giới", "co phieu the gioi", "cổ phiếu quốc tế", "co phieu quoc te", "chứng khoán thế giới", "chung khoan the gioi", "thị trường thế giới", "thi truong the gioi"]):
        return (
            f"{MO_DAU}"
            "\U0001f30d **CỔ PHIẾU THẾ GIỚI — DANH MỤC THEO DÕI**\n\n"
            f"Tôi đang theo dõi **{len(WORLD_STOCK_INFO)} cổ phiếu quốc tế** từ Mỹ, châu Âu, châu Á.\n\n"
            "\U0001f1fa\U0001f1f8 **MỸ:** AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, JPM, V, ...\n"
            "\U0001f1ea\U0001f1f8 **CHÂU ÂU:** SAP, Siemens, Nestlé, LVMH, Airbus, ...\n"
            "\U0001f1ef\U0001f1f5 **NHẬT:** Toyota, Sony, SoftBank, Nintendo, ...\n"
            "\U0001f1e8\U0001f1f3 **TRUNG QUỐC:** Tencent, Alibaba, Meituan, Xiaomi, ...\n"
            "\U0001f1f0\U0001f1f7 **HÀN QUỐC:** Samsung, SK Hynix, NAVER, ...\n\n"
            f"\U0001f447 **Thử hỏi tôi:** \"phân tích AAPL\", \"giá MSFT\", \"cổ phiếu công nghệ Mỹ\""
        )

    kw_crypto = ["bitcoin", "btc", "crypto", "tiền điện tử", "tien dien tu", "điện tử", "ethereum", "eth", "đồng coin", "coin"]
    if any(kw in cau_thuong or kw in cau_khong_dau for kw in kw_crypto):
        if "ethereum" in cau_thuong or "eth" in cau_thuong or "ether" in cau_thuong:
            return phan_tich_crypto("ethereum")
        if any(kw in cau_thuong for kw in ["crypto tổng", "tiền điện tử tổng", "tổng quan crypto", "thi trường crypto"]):
            return (
                f"{MO_DAU}"
                "\U0001f4ca **TỔNG QUAN THỊ TRƯỜNG CRYPTO**\n\n"
                "Thị trường tiền điện tử đang vận động theo chu kỳ 4 năm (halving). "
                "Tổng vốn hóa thị trường: **~$2,400 tỷ**.\n\n"
                "\U0001f539 **Top 10 (chiếm 85% thị phần):**\n"
                "1. **BTC** — $67K (~55% thị phần) — \"vàng kỹ thuật số\"\n"
                "2. **ETH** — $3.5K (~17%) — hợp đồng thông minh\n"
                "3. **USDT** — $1.0 — stablecoin lớn nhất\n"
                "4. **BNB** — $580 — hệ sinh thái Binance\n"
                "5. **SOL** — $145 — Layer-1 tốc độ cao\n"
                "6. **XRP** — $0.62 — thanh toán xuyên biên giới\n"
                "7. **USDC** — $1.0 — stablecoin\n"
                "8. **ADA** — $0.48 — smart contract\n"
                "9. **AVAX** — $35 — subnet\n"
                "10. **DOGE** — $0.15 — meme coin\n\n"
                "\U0001f50d **CHIẾN LƯỢC:** Chỉ nắm BTC + ETH. "
                "Altcoin và meme coin là đánh bạc. "
                "\"Mua BTC và ETH, quên mật khẩu, sống cuộc đời hạnh phúc.\""
            )
        return phan_tich_crypto("bitcoin")

    kw_vang = ["giá vàng", "vang", "vàng", "gold", "xau", "sjc", "vàng sjc", "vàng thế giới", "kim loại quý", "gold price", "xauusd"]
    if any(kw in cau_thuong or kw in cau_khong_dau for kw in kw_vang):
        if "phân tích" in cau_thuong or "phan tich" in cau_khong_dau or "giá" in cau_thuong or "gia" in cau_khong_dau:
            return phan_tich_vang()
        return (
            f"{MO_DAU}"
            "\U0001f947 **VÀNG HÔM NAY**\n\n"
            "• Vàng SJC: ~78-80 triệu VNĐ/lượng\n"
            "• Vàng thế giới: ~$2,350-2,400/oz\n"
            "• Chênh lệch: 5-7 triệu — do độc quyền SJC\n"
            "• Vàng nhẫn 24K: ~74-77 triệu/lượng\n\n"
            "Hãy hỏi: \"Phân tích vàng\" để xem phân tích CHUYÊN SÂU!"
        )

    kq_quy = tim_quy(cau_thuong, cau_khong_dau)
    if kq_quy:
        return kq_quy

    for ma in sorted(STOCK_INFO.keys(), key=len, reverse=True):
        if ma in cau_thuong or ma in cau_khong_dau:
            if len(ma) < 3 and ma != cau_thuong and ma != cau_khong_dau:
                continue
            info = STOCK_INFO[ma]
            return _tao_phan_tich_sieu_sau(ma, info)

    for ma_world in sorted(WORLD_STOCK_INFO.keys(), key=len, reverse=True):
        if ma_world in cau_thuong or ma_world in cau_khong_dau:
            if len(ma_world) < 3 and ma_world != cau_thuong and ma_world != cau_khong_dau:
                continue
            info = WORLD_STOCK_INFO[ma_world]
            return _tao_phan_tich_co_phieu_tg(ma_world, info)

    for ten_cong_ty, ma_world in sorted(COMMON_NAMES_MAP.items(), key=lambda x: -len(x[0])):
        if ten_cong_ty in cau_thuong or ten_cong_ty in cau_khong_dau:
            if ma_world in WORLD_STOCK_INFO:
                info = WORLD_STOCK_INFO[ma_world]
                return _tao_phan_tich_co_phieu_tg(ma_world, info)

    for keyword, original_key in THI_TRUONG_TU_KHOA.items():
        if keyword in cau_khong_dau:
            return THI_TRUONG_ANALYSIS[original_key]

    for tu_khoa, tra_loi in HOI_DAP.items():
        if tu_khoa in cau_thuong or xu_ly_bo_dau(tu_khoa) in cau_khong_dau:
            return tra_loi

    return random.choice(CAU_TRA_LOI_MAC_DINH)
