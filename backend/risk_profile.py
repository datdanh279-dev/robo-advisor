import numpy as np

LOAI_NHA_DAU_TU = {
    "Bảo thủ": {
        "score_range": (0, 36),
        "mieu_ta": "Ưu tiên an toàn vốn tuyệt đối, chấp nhận lợi nhuận thấp",
        "danh_muc": {
            "Tiền gửi/Ngân hàng": 0.50,
            "Trái phiếu chính phủ": 0.30,
            "Vàng": 0.10,
            "Cổ phiếu blue-chip": 0.10,
            "Bất động sản": 0.00,
            "Cổ phiếu tăng trưởng": 0.00,
            "Chứng chỉ quỹ/ETF": 0.00,
            "Tiền điện tử": 0.00,
        },
    },
    "Thận trọng": {
        "score_range": (37, 60),
        "mieu_ta": "Chấp nhận rủi ro thấp để có lợi suất cao hơn một chút",
        "danh_muc": {
            "Tiền gửi/Ngân hàng": 0.35,
            "Trái phiếu chính phủ": 0.20,
            "Vàng": 0.10,
            "Cổ phiếu blue-chip": 0.15,
            "Bất động sản": 0.05,
            "Cổ phiếu tăng trưởng": 0.00,
            "Chứng chỉ quỹ/ETF": 0.15,
            "Tiền điện tử": 0.00,
        },
    },
    "Trung dung": {
        "score_range": (61, 84),
        "mieu_ta": "Cân bằng giữa rủi ro và lợi nhuận",
        "danh_muc": {
            "Tiền gửi/Ngân hàng": 0.15,
            "Trái phiếu chính phủ": 0.15,
            "Vàng": 0.10,
            "Cổ phiếu blue-chip": 0.20,
            "Bất động sản": 0.10,
            "Cổ phiếu tăng trưởng": 0.08,
            "Chứng chỉ quỹ/ETF": 0.20,
            "Tiền điện tử": 0.02,
        },
    },
    "Tăng trưởng": {
        "score_range": (85, 104),
        "mieu_ta": "Tập trung vào tăng trưởng dài hạn, chấp nhận biến động",
        "danh_muc": {
            "Tiền gửi/Ngân hàng": 0.05,
            "Trái phiếu chính phủ": 0.08,
            "Vàng": 0.10,
            "Cổ phiếu blue-chip": 0.20,
            "Bất động sản": 0.15,
            "Cổ phiếu tăng trưởng": 0.20,
            "Chứng chỉ quỹ/ETF": 0.10,
            "Tiền điện tử": 0.12,
        },
    },
    "Táo bạo": {
        "score_range": (105, 120),
        "mieu_ta": "Chấp nhận rủi ro cao để tối đa hóa lợi nhuận",
        "danh_muc": {
            "Tiền gửi/Ngân hàng": 0.05,
            "Trái phiếu chính phủ": 0.05,
            "Vàng": 0.10,
            "Cổ phiếu blue-chip": 0.15,
            "Bất động sản": 0.10,
            "Cổ phiếu tăng trưởng": 0.25,
            "Chứng chỉ quỹ/ETF": 0.05,
            "Tiền điện tử": 0.25,
        },
    },
}

CAU_HOI_KHAO_SAT = [
    {
        "cau_hoi": "Bạn bao nhiêu tuổi?",
        "y": "tuoi",
        "lua_chon": [
            {"nhan": "Dưới 25 tuổi", "diem": 5},
            {"nhan": "25 - 35 tuổi", "diem": 4},
            {"nhan": "36 - 50 tuổi", "diem": 3},
            {"nhan": "51 - 60 tuổi", "diem": 2},
            {"nhan": "Trên 60 tuổi", "diem": 1},
        ],
    },
    {
        "cau_hoi": "Thu nhập hàng tháng của bạn là bao nhiêu?",
        "y": "thu_nhap",
        "lua_chon": [
            {"nhan": "Dưới 5 triệu VND", "diem": 1},
            {"nhan": "5 - 15 triệu VND", "diem": 2},
            {"nhan": "15 - 30 triệu VND", "diem": 3},
            {"nhan": "30 - 50 triệu VND", "diem": 4},
            {"nhan": "Trên 50 triệu VND", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Bạn có quỹ dự phòng khẩn cấp (đủ chi tiêu 6 tháng) không?",
        "y": "quy_du_phong",
        "lua_chon": [
            {"nhan": "Có, đầy đủ", "diem": 5},
            {"nhan": "Có, nhưng chưa đủ", "diem": 3},
            {"nhan": "Không có", "diem": 1},
        ],
    },
    {
        "cau_hoi": "Mục tiêu đầu tư chính của bạn là gì?",
        "y": "muc_tieu",
        "lua_chon": [
            {"nhan": "Bảo toàn vốn", "diem": 1},
            {"nhan": "Thu nhập thụ động ổn định", "diem": 2},
            {"nhan": "Cân bằng tăng trưởng và thu nhập", "diem": 3},
            {"nhan": "Tăng trưởng dài hạn", "diem": 4},
            {"nhan": "Tối đa hóa lợi nhuận", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Bạn sẽ phản ứng thế nào nếu danh mục đầu tư giảm 20% trong 1 tháng?",
        "y": "phan_ung_rui_ro",
        "lua_chon": [
            {"nhan": "Bán hết ngay lập tức", "diem": 1},
            {"nhan": "Bán một phần", "diem": 2},
            {"nhan": "Giữ nguyên và theo dõi", "diem": 3},
            {"nhan": "Mua thêm vì giá rẻ", "diem": 4},
            {"nhan": "Vay thêm để mua", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Kinh nghiệm đầu tư của bạn như thế nào?",
        "y": "kinh_nghiem",
        "lua_chon": [
            {"nhan": "Chưa từng đầu tư", "diem": 1},
            {"nhan": "Dưới 1 năm", "diem": 2},
            {"nhan": "1 - 3 năm", "diem": 3},
            {"nhan": "3 - 7 năm", "diem": 4},
            {"nhan": "Trên 7 năm", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Bạn dự định đầu tư trong bao lâu?",
        "y": "thoi_gian",
        "lua_chon": [
            {"nhan": "Dưới 1 năm", "diem": 1},
            {"nhan": "1 - 3 năm", "diem": 2},
            {"nhan": "3 - 5 năm", "diem": 3},
            {"nhan": "5 - 10 năm", "diem": 4},
            {"nhan": "Trên 10 năm", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Tỷ lệ thu nhập bạn sẵn sàng đầu tư hàng tháng?",
        "y": "ty_le_dau_tu",
        "lua_chon": [
            {"nhan": "Dưới 5%", "diem": 1},
            {"nhan": "5 - 10%", "diem": 2},
            {"nhan": "10 - 20%", "diem": 3},
            {"nhan": "20 - 30%", "diem": 4},
            {"nhan": "Trên 30%", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Bạn có kiến thức về các kênh đầu tư nào?",
        "y": "kien_thuc",
        "lua_chon": [
            {"nhan": "Chỉ biết gửi tiết kiệm", "diem": 1},
            {"nhan": "Tiết kiệm, vàng", "diem": 2},
            {"nhan": "Tiết kiệm, vàng, cổ phiếu", "diem": 3},
            {"nhan": "Cổ phiếu, trái phiếu, chứng chỉ quỹ", "diem": 4},
            {"nhan": "Tất cả kênh (kể cả crypto, forex)", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Nếu đầu tư thua lỗ, bạn có sẵn sàng chờ đợi để hồi phục không?",
        "y": "kha_nang_cho",
        "lua_chon": [
            {"nhan": "Không, tôi cần tiền ngay", "diem": 1},
            {"nhan": "Có thể chờ 6 tháng", "diem": 2},
            {"nhan": "Có thể chờ 1-2 năm", "diem": 3},
            {"nhan": "Có thể chờ 3-5 năm", "diem": 4},
            {"nhan": "Có thể chờ trên 5 năm", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Mục tiêu tài chính cụ thể của bạn trong 5 năm tới là gì?",
        "y": "muc_tieu_cu_the",
        "lua_chon": [
            {"nhan": "Mua nhà/trả góp", "diem": 2},
            {"nhan": "Học hành cho con cái", "diem": 2},
            {"nhan": "Nghỉ hưu sớm/tự do tài chính", "diem": 5},
            {"nhan": "Du lịch/mua sắm lớn", "diem": 3},
            {"nhan": "Xây dựng quỹ dự phòng dài hạn", "diem": 3},
        ],
    },
    {
        "cau_hoi": "Bạn muốn nhận báo cáo đầu tư với tần suất thế nào?",
        "y": "tan_suat_bao_cao",
        "lua_chon": [
            {"nhan": "Hàng tuần", "diem": 5},
            {"nhan": "Hàng tháng", "diem": 4},
            {"nhan": "Hàng quý", "diem": 3},
            {"nhan": "Hàng năm", "diem": 2},
            {"nhan": "Chỉ khi có biến động lớn", "diem": 1},
        ],
    },
    {
        "cau_hoi": "Tổng tài sản ròng (tiền + vàng + bất động sản + chứng khoán) của bạn ước tính bao nhiêu?",
        "y": "tai_san_ron_g",
        "lua_chon": [
            {"nhan": "Dưới 500 triệu VND", "diem": 1},
            {"nhan": "500 triệu - 2 tỷ VND", "diem": 2},
            {"nhan": "2 tỷ - 5 tỷ VND", "diem": 3},
            {"nhan": "5 tỷ - 20 tỷ VND", "diem": 4},
            {"nhan": "Trên 20 tỷ VND", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Tỷ lệ nợ vay (thẻ tín dụng, vay tiêu dùng, vay mua nhà) trên thu nhập hàng năm của bạn?",
        "y": "ty_le_no",
        "lua_chon": [
            {"nhan": "Trên 50% (rất cao)", "diem": 1},
            {"nhan": "30% - 50%", "diem": 2},
            {"nhan": "10% - 30%", "diem": 3},
            {"nhan": "Dưới 10%", "diem": 4},
            {"nhan": "Không có nợ", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Bạn dự định bỏ vào đầu tư số tiền ban đầu là bao nhiêu?",
        "y": "von_ban_dau",
        "lua_chon": [
            {"nhan": "Dưới 10 triệu VND", "diem": 1},
            {"nhan": "10 - 50 triệu VND", "diem": 2},
            {"nhan": "50 - 200 triệu VND", "diem": 3},
            {"nhan": "200 triệu - 1 tỷ VND", "diem": 4},
            {"nhan": "Trên 1 tỷ VND", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Nếu danh mục giảm 40% trong 1 tháng (kịch bản khủng hoảng), bạn sẽ làm gì?",
        "y": "phan_ung_40_phantram",
        "lua_chon": [
            {"nhan": "Bán hết, không thể chịu nổi", "diem": 1},
            {"nhan": "Bán phần lớn để cắt lỗ", "diem": 2},
            {"nhan": "Giữ nguyên, không làm gì", "diem": 3},
            {"nhan": "Mua thêm một phần vì giá hời", "diem": 4},
            {"nhan": "Dồn tiền mua thêm tối đa có thể", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Mức lỗ tối đa bạn chấp nhận được cho toàn bộ danh mục?",
        "y": "lo_toi_da_chap_nhan",
        "lua_chon": [
            {"nhan": "Dưới 5%", "diem": 1},
            {"nhan": "5% - 15%", "diem": 2},
            {"nhan": "15% - 30%", "diem": 3},
            {"nhan": "30% - 50%", "diem": 4},
            {"nhan": "Trên 50% (sẵn sàng mất hết)", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Bạn hiểu P/E (giá/lợi nhuận) và P/B (giá/giá trị sổ sách) ở mức nào?",
        "y": "hieu_bi_pe_pb",
        "lua_chon": [
            {"nhan": "Chưa từng nghe", "diem": 1},
            {"nhan": "Nghe nhưng không hiểu", "diem": 2},
            {"nhan": "Hiểu cơ bản", "diem": 3},
            {"nhan": "Hiểu và đã dùng để chọn cổ phiếu", "diem": 4},
            {"nhan": "Thành thạo, kết hợp nhiều chỉ số nâng cao", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Tình trạng gia đình hiện tại của bạn?",
        "y": "tinh_trang_gia_dinh",
        "lua_chon": [
            {"nhan": "Độc thân, không phụ thuộc", "diem": 5},
            {"nhan": "Độc thân, đang nuôi con nhỏ", "diem": 3},
            {"nhan": "Kết hôn, hai vợ chồng cùng thu nhập", "diem": 4},
            {"nhan": "Kết hôn, một người thu nhập chính", "diem": 2},
            {"nhan": "Đã nghỉ hưu", "diem": 1},
        ],
    },
    {
        "cau_hoi": "Bạn có bao nhiêu người phụ thuộc tài chính (con cái, bố mẹ già, người thân)?",
        "y": "so_nguoi_phu_thuoc",
        "lua_chon": [
            {"nhan": "Không có", "diem": 5},
            {"nhan": "1 người", "diem": 4},
            {"nhan": "2 người", "diem": 3},
            {"nhan": "3 - 4 người", "diem": 2},
            {"nhan": "5 người trở lên", "diem": 1},
        ],
    },
    {
        "cau_hoi": "Bạn dự kiến tần suất giao dịch mua/bán cổ phiếu?",
        "y": "tan_suat_giao_dich",
        "lua_chon": [
            {"nhan": "Mua giữ, gần như không bán", "diem": 5},
            {"nhan": "1 - 3 lần/năm (cân bằng lại DM)", "diem": 4},
            {"nhan": "1 - 2 lần/tháng", "diem": 3},
            {"nhan": "1 - 2 lần/tuần (lướt sóng)", "diem": 2},
            {"nhan": "Hàng ngày (day trading)", "diem": 1},
        ],
    },
    {
        "cau_hoi": "Bạn đã từng sử dụng margin (vay ký quỹ) để mua cổ phiếu chưa?",
        "y": "kinh_nghiem_margin",
        "lua_chon": [
            {"nhan": "Chưa, không biết margin là gì", "diem": 1},
            {"nhan": "Chưa, nhưng biết là có rủi ro cao", "diem": 2},
            {"nhan": "Có, dùng rất ít (< 20% tỷ lệ)", "diem": 4},
            {"nhan": "Có, dùng thường xuyên (20 - 50%)", "diem": 5},
            {"nhan": "Có, dùng margin tối đa (>50%) và đã cháy TK", "diem": 1},
        ],
    },
    {
        "cau_hoi": "Bạn đã từng lỗ hơn 30% giá trị tài khoản trong quá khứ?",
        "y": "lo_30_truoc_day",
        "lua_chon": [
            {"nhan": "Chưa từng đầu tư", "diem": 3},
            {"nhan": "Có, và đã rút lui khỏi TTCK", "diem": 1},
            {"nhan": "Có, nhưng đã hồi phục và tiếp tục", "diem": 4},
            {"nhan": "Chưa từng lỗ quá 30%", "diem": 3},
            {"nhan": "Lỗ hơn 30% nhiều lần, coi đó là bài học", "diem": 5},
        ],
    },
    {
        "cau_hoi": "Mức độ bạn tin tưởng vào thị trường chứng khoán Việt Nam 5 năm tới?",
        "y": "tin_tuong_thi_truong",
        "lua_chon": [
            {"nhan": "Rất thấp, sẽ rút tiền ra", "diem": 1},
            {"nhan": "Thấp, chỉ giữ tiền gửi", "diem": 2},
            {"nhan": "Trung lập, thị trường VN khó đoán", "diem": 3},
            {"nhan": "Tin tưởng, sẽ tiếp tục đầu tư", "diem": 4},
            {"nhan": "Rất tin tưởng, sẽ tăng tỷ trọng cổ phiếu", "diem": 5},
        ],
    },
]


def danh_gia_rui_ro(cau_tra_loi):
    tong_diem = sum(cau_tra_loi.values())
    for loai, thong_tin in LOAI_NHA_DAU_TU.items():
        low, high = thong_tin["score_range"]
        if low <= tong_diem <= high:
            return loai, tong_diem, thong_tin["mieu_ta"], thong_tin["danh_muc"]
    return "Trung dung", tong_diem, "Cân bằng", LOAI_NHA_DAU_TU["Trung dung"]["danh_muc"]


def phan_bo_danh_muc(loai_nha_dau_tu, tong_so_tien):
    danh_muc = LOAI_NHA_DAU_TU[loai_nha_dau_tu]["danh_muc"]
    phan_bo = {}
    for kenh, ty_trong in danh_muc.items():
        phan_bo[kenh] = {
            "ty_trong": ty_trong,
            "so_tien": round(tong_so_tien * ty_trong, -3),
        }
    return phan_bo
