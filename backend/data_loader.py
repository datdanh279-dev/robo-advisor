import pandas as pd
import numpy as np
import os
import re
import unicodedata
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _bo_dau(s: str) -> str:
    """Bỏ dấu tiếng Việt + chuyển lowercase + gộp khoảng trắng để map key ổn định."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


_NGANH_TV = {
    "cong nghe": "Công nghệ",
    "cong nghe thong tin": "Công nghệ thông tin",
    "ngan hang": "Ngân hàng",
    "ha tang so": "Hạ tầng số",
    "ban le": "Bán lẻ",
    "thep": "Thép",
    "thep & cong nghiep": "Thép & Công nghiệp",
    "thep va cong nghiep": "Thép & Công nghiệp",
    "tieu dung": "Tiêu dùng thiết yếu",
    "tieu dung thiet yeu": "Tiêu dùng thiết yếu",
    "hang tieu dung": "Hàng tiêu dùng",
    "chung khoan": "Chứng khoán",
    "bat dong san": "Bất động sản",
    "dau khi": "Dầu khí",
    "dien": "Điện",
    "vien thong": "Viễn thông",
    "y te": "Y tế",
    "du lich": "Du lịch",
    "giao duc": "Giáo dục",
    "xay dung": "Xây dựng",
    "van tai": "Vận tải",
    "logistics": "Logistics",
    "bao hiem": "Bảo hiểm",
    "thep & cong nghiep": "Thép & Công nghiệp",
    "nong nghiep": "Nông nghiệp",
    "thuy san": "Thủy sản",
    "thuc pham": "Thực phẩm",
    "sua & thuc pham": "Sữa & Thực phẩm",
    "sua": "Sữa & Thực phẩm",
    "ban le cong nghe": "Bán lẻ công nghệ",
    "cong nghe fpt": "Công nghệ",
    "ha tang": "Hạ tầng",
    "khoang san": "Khoáng sản",
    "hoa chat": "Hóa chất",
    "phân bón": "Phân bón",
    "det may": "Dệt may",
    "giay": "Giày",
    "go": "Gỗ",
    "nhua": "Nhựa",
    "bao bi": "Bao bì",
    "in an": "In ấn",
    "truyen thong": "Truyền thông",
    "quang cao": "Quảng cáo",
    "the thao": "Thể thao",
    "giai tri": "Giải trí",
    "game": "Game",
    "crypto": "Crypto",
    "vang": "Vàng",
    "ngoai te": "Ngoại tệ",
    "ty gia": "Tỷ giá",
    "lai suat": "Lãi suất",
    "trai phieu": "Trái phiếu",
    "quy": "Quỹ",
    "etf": "ETF",
    "phai sinh": "Phái sinh",
    "hang khong": "Hàng không",
    "duong sat": "Đường sắt",
    "duong bien": "Đường biển",
    "cang": "Cảng",
    "kho bai": "Kho bãi",
    "bat dong san kcn": "Bất động sản KCN",
    "khu cong nghiep": "Khu công nghiệp",
    "kcn": "Khu công nghiệp",
    "kdc": "Khu đô thị",
    "khu do thi": "Khu đô thị",
    "dich vu": "Dịch vụ",
    "tu van": "Tư vấn",
    "kiem toan": "Kiểm toán",
    "luat": "Luật",
    "nhan su": "Nhân sự",
    "cong nghe tai chinh": "Công nghệ tài chính",
    "fintech": "Công nghệ tài chính",
    "thuong mai dien tu": "Thương mại điện tử",
    "ecommerce": "Thương mại điện tử",
    "logistics & van tai": "Logistics & Vận tải",
    "vận tải & logistics": "Logistics & Vận tải",
    "spa": "Spa",
    "my pham": "Mỹ phẩm",
    "thoi trang": "Thời trang",
    "trang suc": "Trang sức",
    "vang bac": "Vàng bạc",
    "kim loai": "Kim loại",
    "phi kim": "Phi kim",
    "nap dien": "Nạp điện",
    "xe dien": "Xe điện",
    "oto": "Ô tô",
    "xe may": "Xe máy",
    "phu tung": "Phụ tùng",
    "nang luong": "Năng lượng",
    "nang luong tai tao": "Năng lượng tái tạo",
    "dien mat troi": "Điện mặt trời",
    "dien gio": "Điện gió",
    "nha hang": "Nhà hàng",
    "khach san": "Khách sạn",
    "du lich & khach san": "Du lịch & Khách sạn",
    "du lich & le hoi": "Du lịch & Lễ hội",
    "cong nghe & so": "Công nghệ & Số",
    "cong nghe thong tin & vien thong": "Công nghệ thông tin & Viễn thông",
    "ngan hang & tai chinh": "Ngân hàng & Tài chính",
    "chung khoan & dau tu": "Chứng khoán & Đầu tư",
    "thep & vlxd": "Thép & VLXD",
    "vlxd": "VLXD",
    "bat dong san & xay dung": "Bất động sản & Xây dựng",
    "vien thong & cong nghe": "Viễn thông & Công nghệ",
    "dau khi & nang luong": "Dầu khí & Năng lượng",
    "thuc pham & do uong": "Thực phẩm & Đồ uống",
    "do uong": "Đồ uống",
    "bia": "Bia",
    "ruou": "Rượu",
    "bia ruou": "Bia & Rượu",
    "bia & ruou": "Bia & Rượu",
    "duong": "Đường",
    "sua & sua chua": "Sữa & Sữa chua",
    "sua & thuc pham dinh duong": "Sữa & Thực phẩm dinh dưỡng",
    "thuc pham dong hop": "Thực phẩm đóng hộp",
    "thuc pham & thuc pham chuc nang": "Thực phẩm & Thực phẩm chức năng",
    "thuc pham chuc nang": "Thực phẩm chức năng",
    "y te & duoc pham": "Y tế & Dược phẩm",
    "duoc pham": "Dược phẩm",
    "thiet bi y te": "Thiết bị y tế",
    "giao duc & dao tao": "Giáo dục & Đào tạo",
    "dao tao": "Đào tạo",
    "trung tam ngoai ngu": "Trung tâm ngoại ngữ",
    "van hoa": "Văn hóa",
    "the thao & giai tri": "Thể thao & Giải trí",
    "truyen hinh": "Truyền hình",
    "sach": "Sách",
    "xuat ban": "Xuất bản",
    "bao": "Báo",
    "bao chi": "Báo chí",
    "truyen thong & quang cao": "Truyền thông & Quảng cáo",
    "agency": "Quảng cáo",
    "phim": "Phim",
    "am nhac": "Âm nhạc",
    "nghe thuat": "Nghệ thuật",
    "game & esports": "Game & Esports",
    "esports": "Esports",
    "crypto & blockchain": "Crypto & Blockchain",
    "blockchain": "Blockchain",
    "nft": "NFT",
    "metaverse": "Metaverse",
    "ai & robot": "AI & Robot",
    "ai": "AI",
    "robot": "Robot",
    "iot": "IoT",
    "big data": "Big Data",
    "cloud": "Cloud",
    "cybersecurity": "Cybersecurity",
    "an ninh mang": "An ninh mạng",
    "an ninh": "An ninh",
    "quan su": "Quân sự",
    "quoc phong": "Quốc phòng",
    "vũ khí": "Vũ khí",
    "hang khong vu tru": "Hàng không vũ trụ",
    "vu tru": "Vũ trụ",
    "ten lua": "Tên lửa",
    "hat nhan": "Hạt nhân",
    "nang luong hat nhan": "Năng lượng hạt nhân",
    "dien hat nhan": "Điện hạt nhân",
    "mo": "Mỏ",
    "vang bac da quy": "Vàng bạc đá quý",
    "da quy": "Đá quý",
    "trang suc & da quy": "Trang sức & Đá quý",
    "co khi": "Cơ khí",
    "che tao": "Chế tạo",
    "tu dong hoa": "Tự động hóa",
    "ban dan": "Bán dẫn",
    "chip": "Chip",
    "vi mach": "Vi mạch",
    "linh kien dien tu": "Linh kiện điện tử",
    "thiet bi dien tu": "Thiết bị điện tử",
    "do gia dung": "Đồ gia dụng",
    "noi that": "Nội thất",
    "ngoai that": "Ngoại thất",
    "vat lieu xay dung": "Vật liệu xây dựng",
    "kinh": "Kính",
    "men": "Men",
    "gach": "Gạch",
    "ximang": "Xi măng",
    "thep": "Thép",
    "nhom": "Nhôm",
    "dong": "Đồng",
    "kem": "Kẽm",
    "chi": "Chì",
    "thiec": "Thiếc",
    "niken": "Niken",
    "sat": "Sắt",
    "thep khong gi": "Thép không gỉ",
    "inox": "Inox",
    "gang": "Gang",
    "pallet": "Pallet",
    "thung carton": "Thùng carton",
    "mang boc thuc pham": "Màng bọc thực phẩm",
    "tui nylon": "Túi nylon",
    "nhựa đường": "Nhựa đường",
    "bê tông": "Bê tông",
    "cot thep": "Cốt thép",
    "xep day": "Xếp dỡ",
    "boc xep": "Bốc xếp",
    "giao nhan": "Giao nhận",
    "chuyen phat": "Chuyển phát",
    "buu chinh": "Bưu chính",
    "buu pham": "Bưu phẩm",
    "thuong mai": "Thương mại",
    "xuat nhap khau": "Xuất nhập khẩu",
    "sieu thi": "Siêu thị",
    "cua hang tien loi": "Cửa hàng tiện lợi",
    "mini mart": "Cửa hàng tiện lợi",
    "trung tam thuong mai": "Trung tâm thương mại",
    "tttm": "Trung tâm thương mại",
    "cho": "Chợ",
    "cho dau moi": "Chợ đầu mối",
    "dau gia": "Đấu giá",
    "shopee": "Thương mại điện tử",
    "lazada": "Thương mại điện tử",
    "tiki": "Thương mại điện tử",
    "sendo": "Thương mại điện tử",
    "tiktok shop": "Thương mại điện tử",
    "livestream": "Thương mại điện tử",
    "affiliate": "Thương mại điện tử",
    "dropship": "Thương mại điện tử",
    "amazon": "Thương mại điện tử",
    "ebay": "Thương mại điện tử",
    "alibaba": "Thương mại điện tử",
    "taobao": "Thương mại điện tử",
    "1688": "Thương mại điện tử",
    "global sources": "Thương mại điện tử",
    "made-in-china": "Thương mại điện tử",
    "yiwu": "Thương mại điện tử",
    "canton fair": "Thương mại điện tử",
    "huawei": "Công nghệ",
    "apple": "Công nghệ",
    "samsung": "Công nghệ",
    "xiaomi": "Công nghệ",
    "oppo": "Công nghệ",
    "vivo": "Công nghệ",
    "realme": "Công nghệ",
    "tecno": "Công nghệ",
    "infinix": "Công nghệ",
    "itel": "Công nghệ",
    "nokia": "Công nghệ",
    "sony": "Công nghệ",
    "panasonic": "Công nghệ",
    "lg": "Công nghệ",
    "toshiba": "Công nghệ",
    "sharp": "Công nghệ",
    "philips": "Công nghệ",
    "dyson": "Công nghệ",
    "bose": "Công nghệ",
    "jbl": "Công nghệ",
    "logitech": "Công nghệ",
    "razer": "Công nghệ",
    "corsair": "Công nghệ",
    "msi": "Công nghệ",
    "asus": "Công nghệ",
    "acer": "Công nghệ",
    "dell": "Công nghệ",
    "hp": "Công nghệ",
    "lenovo": "Công nghệ",
    "ibm": "Công nghệ",
    "oracle": "Công nghệ",
    "sap": "Công nghệ",
    "salesforce": "Công nghệ",
    "adobe": "Công nghệ",
    "autodesk": "Công nghệ",
    "vmware": "Công nghệ",
    "cisco": "Công nghệ",
    "juniper": "Công nghệ",
    "fortinet": "Công nghệ",
    "palo alto": "Công nghệ",
    "crowdstrike": "Công nghệ",
    "zscaler": "Công nghệ",
    "okta": "Công nghệ",
    "servicenow": "Công nghệ",
    "snowflake": "Công nghệ",
    "datadog": "Công nghệ",
    "splunk": "Công nghệ",
    "elastic": "Công nghệ",
    "mongodb": "Công nghệ",
    "confluent": "Công nghệ",
    "hashicorp": "Công nghệ",
    "gitlab": "Công nghệ",
    "github": "Công nghệ",
    "atlassian": "Công nghệ",
    "jetbrains": "Công nghệ",
    "nvidia": "Công nghệ",
    "amd": "Công nghệ",
    "intel": "Công nghệ",
    "tsmc": "Công nghệ",
    "samsung electronics": "Công nghệ",
    "sk hynix": "Công nghệ",
    "micron": "Công nghệ",
    "western digital": "Công nghệ",
    "seagate": "Công nghệ",
    "sandisk": "Công nghệ",
    "applied materials": "Công nghệ",
    "lam research": "Công nghệ",
    "kla": "Công nghệ",
    "asml": "Công nghệ",
    "tokyo electron": "Công nghệ",
    "disco": "Công nghệ",
    "screen holdings": "Công nghệ",
    "advantest": "Công nghệ",
    "lasertec": "Công nghệ",
    "naver": "Công nghệ",
    "kakao": "Công nghệ",
    "coupang": "Công nghệ",
    "baemin": "Công nghệ",
    "yogiyo": "Công nghệ",
    "baedal minjok": "Công nghệ",
    "woowahan": "Công nghệ",
    "toss": "Công nghệ tài chính",
    "kakao pay": "Công nghệ tài chính",
    "kakao bank": "Ngân hàng",
    "kakao entertainment": "Giải trí",
    "sm entertainment": "Giải trí",
    "jyp entertainment": "Giải trí",
    "yg entertainment": "Giải trí",
    "hybe": "Giải trí",
    "hyundai": "Ô tô",
    "kia": "Ô tô",
    "genesis": "Ô tô",
    "kgm": "Ô tô",
    "ssangyong": "Ô tô",
    "chevrolet": "Ô tô",
    "ford": "Ô tô",
    "toyota": "Ô tô",
    "honda": "Ô tô",
    "mazda": "Ô tô",
    "subaru": "Ô tô",
    "nissan": "Ô tô",
    "mitsubishi": "Ô tô",
    "isuzu": "Ô tô",
    "suzuki": "Ô tô",
    "daihatsu": "Ô tô",
    "lexus": "Ô tô",
    "infiniti": "Ô tô",
    "acura": "Ô tô",
    "cadillac": "Ô tô",
    "buick": "Ô tô",
    "gmc": "Ô tô",
    "chrysler": "Ô tô",
    "dodge": "Ô tô",
    "ram": "Ô tô",
    "jeep": "Ô tô",
    "tesla": "Ô tô",
    "rivian": "Ô tô",
    "lucid": "Ô tô",
    "nio": "Ô tô",
    "xpeng": "Ô tô",
    "li auto": "Ô tô",
    "byd": "Ô tô",
    "vinfast": "Ô tô",
    "togg": "Ô tô",
    "sono": "Ô tô",
    "fisker": "Ô tô",
    "canoo": "Ô tô",
    "lordstown": "Ô tô",
    "nikola": "Ô tô",
    "hyzon": "Ô tô",
    "plug power": "Năng lượng",
    "ballard": "Năng lượng",
    "fuelcell": "Năng lượng",
    "bloom energy": "Năng lượng",
    "nuvve": "Năng lượng",
    "chargepoint": "Năng lượng",
    "evgo": "Năng lượng",
    "blink charging": "Năng lượng",
    "wallbox": "Năng lượng",
    "albemarle": "Khoáng sản",
    "livent": "Khoáng sản",
    "lithium americas": "Khoáng sản",
    "lithium argentina": "Khoáng sản",
    "sigma lithium": "Khoáng sản",
    "pilbara minerals": "Khoáng sản",
    "igo": "Khoáng sản",
    "allkem": "Khoáng sản",
    "ganfeng": "Khoáng sản",
    "tianqi": "Khoáng sản",
    "smm": "Khoáng sản",
    "cnmn": "Khoáng sản",
    "catl": "Phụ tùng",
    "byd electronic": "Phụ tùng",
    "eve energy": "Phụ tùng",
    "gotion": "Phụ tùng",
    "calb": "Phụ tùng",
    "svolt": "Phụ tùng",
    "envision": "Năng lượng",
    "sungrow": "Năng lượng",
    "goodwe": "Năng lượng",
    "growatt": "Năng lượng",
    "solis": "Năng lượng",
    "fronius": "Năng lượng",
    "smainverters": "Năng lượng",
    "kostal": "Năng lượng",
    "kaco": "Năng lượng",
    "delta": "Năng lượng",
    "honeywell": "Năng lượng",
    "schneider": "Năng lượng",
    "abb": "Năng lượng",
    "siemens": "Năng lượng",
    "ge": "Năng lượng",
    "vestas": "Năng lượng",
    "siemens gamesa": "Năng lượng",
    "mhi vestas": "Năng lượng",
    "goldwind": "Năng lượng",
    "mingyang": "Năng lượng",
    "sany": "Năng lượng",
    "xgma": "Năng lượng",
    "zoomlion": "Năng lượng",
    "xcmg": "Năng lượng",
    "lonking": "Năng lượng",
    "liugong": "Năng lượng",
    "sdg": "Năng lượng",
    "shantui": "Năng lượng",
    "caterpillar": "Năng lượng",
    "komatsu": "Năng lượng",
    "hitachi": "Năng lượng",
    "kobelco": "Năng lượng",
    "sumitomo": "Năng lượng",
    "volvo ce": "Năng lượng",
    "jcb": "Năng lượng",
    "manitou": "Năng lượng",
    "haulotte": "Năng lượng",
    "tadano": "Năng lượng",
    "liebherr": "Năng lượng",
    "terex": "Năng lượng",
    "genie": "Năng lượng",
    "jlg": "Năng lượng",
    "skyjack": "Năng lượng",
    "snorkel": "Năng lượng",
    "niftylift": "Năng lượng",
    "platform basket": "Năng lượng",
    "altec": "Năng lượng",
    "versalift": "Năng lượng",
    "time": "Năng lượng",
    "elliott": "Năng lượng",
    "texoma": "Năng lượng",
    "versalift east": "Năng lượng",
    "utility bodies": "Năng lượng",
    "reading": "Năng lượng",
    "ime": "Năng lượng",
    "effer": "Năng lượng",
    "hiab": "Năng lượng",
    "loglift": "Năng lượng",
    "jonsered": "Năng lượng",
    "palfinger": "Năng lượng",
    "fassi": "Năng lượng",
    "cormach": "Năng lượng",
    "heila": "Năng lượng",
    "amco veba": "Năng lượng",
    "copma": "Năng lượng",
    "columbus": "Năng lượng",
    "autogru": "Năng lượng",
    "pm": "Năng lượng",
    "gru cometto": "Năng lượng",
    "tadano demag": "Năng lượng",
    "grove": "Năng lượng",
    "manitowoc": "Năng lượng",
    "potain": "Năng lượng",
    "bkt": "Năng lượng",
    "yongmao": "Năng lượng",
    "saez": "Năng lượng",
    "terex cct": "Năng lượng",
    "cargotec": "Năng lượng",
    "konecranes": "Năng lượng",
    "mantsinen": "Năng lượng",
    "cargotec siwert": "Năng lượng",
    "macgregor": "Năng lượng",
    "hatlapa": "Năng lượng",
    "porsgrunn": "Năng lượng",
    "rapak": "Năng lượng",
    "cargotec kalmar": "Năng lượng",
    "kalmar": "Năng lượng",
    "bromma": "Năng lượng",
    "sisu": "Năng lượng",
    "polaris": "Năng lượng",
    "bogballe": "Năng lượng",
    "bdl": "Năng lượng",
    "champion": "Năng lượng",
    "perard": "Năng lượng",
    "strohm": "Năng lượng",
    "cynkomet": "Năng lượng",
    "metaltech": "Năng lượng",
    "krampe": "Năng lượng",
    "wielton": "Năng lượng",
    "cargotec silvey": "Năng lượng",
    "silvey": "Năng lượng",
    "evergem": "Năng lượng",
    "zwaans": "Năng lượng",
    "ravas": "Năng lượng",
    "grammer": "Năng lượng",
    "istra": "Năng lượng",
    "beak": "Năng lượng",
    "kmc": "Năng lượng",
    "maus": "Năng lượng",
    "baldan": "Năng lượng",
    "tatu": "Năng lượng",
    "baldan & tatu": "Năng lượng",
    "semeato": "Năng lượng",
    "jan": "Năng lượng",
    "tornado": "Năng lượng",
    "fankhauser": "Năng lượng",
    "bm": "Năng lượng",
    "bremer": "Năng lượng",
    "bs": "Năng lượng",
    "bt": "Năng lượng",
    "cat": "Năng lượng",
    "cifa": "Năng lượng",
    "dieci": "Năng lượng",
    "eurocomach": "Năng lượng",
    "faresin": "Năng lượng",
    "fiorigroup": "Năng lượng",
    "genie industries": "Năng lượng",
    "haulotte group": "Năng lượng",
    "jcb agri": "Năng lượng",
    "jcb compact": "Năng lượng",
    "jcb ground": "Năng lượng",
    "jcb heavy": "Năng lượng",
    "jcb industrial": "Năng lượng",
    "jcb landfill": "Năng lượng",
    "jcb military": "Năng lượng",
    "jcb power": "Năng lượng",
    "jcb rail": "Năng lượng",
    "jcb rough": "Năng lượng",
    "jcb scrap": "Năng lượng",
    "jcb teletruk": "Năng lượng",
    "jcb tracked": "Năng lượng",
    "jcb wheeled": "Năng lượng",
    "kleemann": "Năng lượng",
    "kleemann reiner": "Năng lượng",
    "kobelco construction": "Năng lượng",
    "komatsu utility": "Năng lượng",
    "komtrax": "Năng lượng",
    "kpi-jci": "Năng lượng",
    "krupp": "Năng lượng",
    "kubota": "Năng lượng",
    "kverneland": "Năng lượng",
    "lammert": "Năng lượng",
    "liebherr concrete": "Năng lượng",
    "liebherr cranes": "Năng lượng",
    "liebherr domestic": "Năng lượng",
    "liebherr earthmoving": "Năng lượng",
    "liebherr maritime": "Năng lượng",
    "liebherr mining": "Năng lượng",
    "liebherr mobile": "Năng lượng",
    "liebherr tower": "Năng lượng",
    "liebherr trucks": "Năng lượng",
    "linde": "Năng lượng",
    "linde material": "Năng lượng",
    "linde heavy": "Năng lượng",
    "linde light": "Năng lượng",
    "linde special": "Năng lượng",
    "man": "Năng lượng",
    "man diesel": "Năng lượng",
    "man engines": "Năng lượng",
    "man trucks": "Năng lượng",
    "mantella": "Năng lượng",
    "marini": "Năng lượng",
    "marini fayat": "Năng lượng",
    "marini-mefintel": "Năng lượng",
    "mecalac": "Năng lượng",
    "mecalac asm": "Năng lượng",
    "mecalac axel": "Năng lượng",
    "mecalac tvsd": "Năng lượng",
    "mecbo": "Năng lượng",
    "merlo": "Năng lượng",
    "merlo cingo": "Năng lượng",
    "merlo compact": "Năng lượng",
    "merlo electric": "Năng lượng",
    "merlo heavy": "Năng lượng",
    "merlo panoro": "Năng lượng",
    "merlo roto": "Năng lượng",
    "merlo telehandlers": "Năng lượng",
    "merlo turbofarmer": "Năng lượng",
    "merlo turbosprayer": "Năng lượng",
    "merlo turbosup": "Năng lượng",
    "merlo utility": "Năng lượng",
    "messer": "Năng lượng",
    "messer cutmaster": "Năng lượng",
    "messer mgt": "Năng lượng",
    "messer mgts": "Năng lượng",
    "metso": "Năng lượng",
    "metso flow": "Năng lượng",
    "metso lokotrack": "Năng lượng",
    "metso nordberg": "Năng lượng",
    "metso outotec": "Năng lượng",
    "metso plants": "Năng lượng",
    "metso screens": "Năng lượng",
    "mewa": "Năng lượng",
    "mfl": "Năng lượng",
    "mh": "Năng lượng",
    "mh+swac": "Năng lượng",
    "mhwirth": "Năng lượng",
    "mh-b": "Năng lượng",
    "mh-c": "Năng lượng",
    "mh-d": "Năng lượng",
    "mh-e": "Năng lượng",
    "mh-f": "Năng lượng",
    "mh-g": "Năng lượng",
    "mh-h": "Năng lượng",
    "mh-i": "Năng lượng",
    "mh-j": "Năng lượng",
    "mh-k": "Năng lượng",
    "mh-l": "Năng lượng",
    "mh-m": "Năng lượng",
    "mh-n": "Năng lượng",
    "mh-o": "Năng lượng",
    "mh-p": "Năng lượng",
    "mh-q": "Năng lượng",
    "mh-r": "Năng lượng",
    "mh-s": "Năng lượng",
    "mh-t": "Năng lượng",
    "mh-u": "Năng lượng",
    "mh-v": "Năng lượng",
    "mh-w": "Năng lượng",
    "mh-x": "Năng lượng",
    "mh-y": "Năng lượng",
    "mh-z": "Năng lượng",
    "mikasa": "Năng lượng",
    "mitsubishi heavy": "Năng lượng",
    "mitsubishi logisnext": "Năng lượng",
    "mitsubishi motors": "Ô tô",
    "moog": "Năng lượng",
    "morooka": "Năng lượng",
    "mourik": "Năng lượng",
    "movax": "Năng lượng",
    "moxy": "Năng lượng",
    "moxhe": "Năng lượng",
    "mp": "Năng lượng",
    "mq": "Năng lượng",
    "mr": "Năng lượng",
    "ms": "Năng lượng",
    "mt": "Năng lượng",
    "mu": "Năng lượng",
    "mv": "Năng lượng",
    "mw": "Năng lượng",
    "mx": "Năng lượng",
    "my": "Năng lượng",
    "mz": "Năng lượng",
    "na": "Năng lượng",
    "nb": "Năng lượng",
    "nc": "Năng lượng",
    "nd": "Năng lượng",
    "ne": "Năng lượng",
    "nf": "Năng lượng",
    "ng": "Năng lượng",
    "nh": "Năng lượng",
    "ni": "Năng lượng",
    "nj": "Năng lượng",
    "nk": "Năng lượng",
    "nl": "Năng lượng",
    "nm": "Năng lượng",
    "nn": "Năng lượng",
    "no": "Năng lượng",
    "np": "Năng lượng",
    "nq": "Năng lượng",
    "nr": "Năng lượng",
    "ns": "Năng lượng",
    "nt": "Năng lượng",
    "nu": "Năng lượng",
    "nv": "Năng lượng",
    "nw": "Năng lượng",
    "nx": "Năng lượng",
    "ny": "Năng lượng",
    "nz": "Năng lượng",
}

_KET_LUAN_TV = {
    "MUA": "MUA MẠNH",
    "MUA MANH": "MUA MẠNH",
    "GIU": "GIỮ",
    "GIU LAI": "GIỮ LẠI",
    "BAN 1 PHAN": "BÁN 1 PHẦN",
    "BAN 1 PHAN NHE": "BÁN 1 PHẦN NHẸ",
    "MUA THEM": "MUA THÊM",
    "CAN NHAC": "CÂN NHẮC",
    "TRÁNH": "TRÁNH",
    "TRA": "TRÁNH",
    "GIAM": "GIẢM",
    "TANG": "TĂNG",
    "BAN": "BÁN",
    "BAN MANH": "BÁN MẠNH",
    "GIU LAI XEM XET": "GIỮ LẠI XEM XÉT",
    "MUA DÀI HẠN": "MUA DÀI HẠN",
    "MUA NGAN HAN": "MUA NGẮN HẠN",
    "CHO GIA TOT HON": "CHỜ GIÁ TỐT HƠN",
    "CHO THEM": "CHỜ THÊM",
    "CHOT LOI": "CHỐT LỜI",
    "CAT LO": "CẮT LỖ",
    "PHAN PHAT": "PHÂN PHÁT",
    "THOAT RA": "THOÁT RA",
    "THOAT": "THOÁT",
    "MUA MOT PHAN": "MUA MỘT PHẦN",
    "BAN MOT PHAN": "BÁN MỘT PHẦN",
    "GIU HAT": "GIỮ HẠT",
    "BAN HET": "BÁN HẾT",
    "MUA HET": "MUA HẾT",
    "QUAN SAT": "QUAN SÁT",
    "CAN NHAC BAN": "CÂN NHẮC BÁN",
    "CAN NHAC MUA": "CÂN NHẮC MUA",
    "TRUNG LAP": "TRUNG LẬP",
    "TRUNG TINH": "TRUNG TÍNH",
    "QUA MUA": "QUÁ MUA",
    "QUA BAN": "QUÁ BÁN",
    "HO TRO": "HỖ TRỢ",
    "KHANG CỰ": "KHÁNG CỰ",
    "XU HUONG TANG": "XU HƯỚNG TĂNG",
    "XU HUONG GIAM": "XU HƯỚNG GIẢM",
    "XU HUONG DI NGANG": "XU HƯỚNG ĐI NGANG",
    "BUNG NO": "BUNG NỔ",
    "DOT BIEN": "ĐỘT BIẾN",
    "ON DINH": "ỔN ĐỊNH",
    "BAT ON": "BẤT ỔN",
    "TIEM NANG": "TIỀM NĂNG",
    "RUÏ RO CAO": "RỦI RO CAO",
    "RUÏ RO THAP": "RỦI RO THẤP",
    "RUÏ RO TRUNG BINH": "RỦI RO TRUNG BÌNH",
    "MUA DIEN RONG": "MUA DIỄN RỘNG",
    "MUA TAP TRUNG": "MUA TẬP TRUNG",
    "MUA GIAI DOAN": "MUA GIAI ĐOẠN",
    "MUA CHIEU KHUYET": "MUA CHIẾU KHuyết",
    "MUA GIA RE": "MUA GIÁ RẺ",
    "MUA KHOE": "MUA KHỎE",
    "MUA BEN VUNG": "MUA BỀN VỮNG",
    "MUA DAU CO": "MUA ĐẦU CƠ",
    "MUA AN TOAN": "MUA AN TOÀN",
    "MUA RUI RO": "MUA RỦI RO",
    "MUA TY TRONG LON": "MUA TỶ TRỌNG LỚN",
    "MUA TY TRONG NHO": "MUA TỶ TRỌNG NHỎ",
    "MUA PHONG THU": "MUA PHÒNG THỦ",
    "MUA TAN CONG": "MUA TẤN CÔNG",
    "MUA CAN BANG": "MUA CÂN BẰNG",
    "MUA SONG HANH": "MUA SONG HÀNH",
    "MUA DOI UNG": "MUA ĐỐI ỨNG",
    "MUA BO SUNG": "MUA BỔ SUNG",
    "MUA GIA TĂNG": "MUA GIA TĂNG",
    "MUA DÀI HAN": "MUA DÀI HẠN",
    "MUA NGAN HAN": "MUA NGẮN HẠN",
    "MUA TRUNG HAN": "MUA TRUNG HẠN",
    "BAN DAI HAN": "BÁN DÀI HẠN",
    "BAN NGAN HAN": "BÁN NGẮN HẠN",
    "BAN TRUNG HAN": "BÁN TRUNG HẠN",
    "GIU DAI HAN": "GIỮ DÀI HẠN",
    "GIU NGAN HAN": "GIỮ NGẮN HẠN",
    "GIU TRUNG HAN": "GIỮ TRUNG HẠN",
}


def _chuong_hoa_tv_nganh(nganh: str) -> str:
    if not nganh:
        return nganh
    key = _bo_dau(nganh)
    return _NGANH_TV.get(key, nganh.strip())


def _chuong_hoa_tv_ket_luan(ket_luan: str) -> str:
    if not ket_luan:
        return ket_luan
    key = _bo_dau(ket_luan).upper()
    return _KET_LUAN_TV.get(key, ket_luan.strip())


def _dong_bo_performance_tu_danh_muc():
    dm = DOCS.get("danh_muc") or {}
    if not dm:
        return
    try:
        from backend.danh_muc_metrics import tinh_return_danh_muc
        _, _, _, return_pct = tinh_return_danh_muc(dm)
        perf = DOCS.setdefault("performance", {})
        perf["Rp"] = round(return_pct / 100, 4)
    except Exception as e:
        logger.warning("Sync Rp from danh_muc failed: %s", e)


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)

# Ultimate fallback: embedded data from Excel snapshot
try:
    from backend.data_snapshot import get_snapshot as _get_snapshot
except Exception:
    try:
        from data_snapshot import get_snapshot as _get_snapshot
    except Exception:
        def _get_snapshot(key): return None

_EXCEL_CANDIDATES = [
    os.environ.get("EXCEL_PATH"),
    os.path.join(_PROJECT_DIR, "data", "TONG_HOP_v44_SOI_HOP_NHAT.xlsx"),
    os.path.join(_PROJECT_DIR, "TONG_HOP_v44_SOI_HOP_NHAT.xlsx"),
]

EXCEL_PATH = None
for _p in _EXCEL_CANDIDATES:
    if _p and os.path.exists(_p):
        EXCEL_PATH = _p
        break

_NGAY_FILE = "29/05/2026"
_WB = None

def _get_wb():
    global _WB
    if _WB is None and EXCEL_PATH and os.path.exists(EXCEL_PATH):
        _WB = pd.ExcelFile(EXCEL_PATH)
        _mtime = os.path.getmtime(EXCEL_PATH)
        global _NGAY_FILE
        _NGAY_FILE = datetime.fromtimestamp(_mtime).strftime("%d/%m/%Y")
    return _WB

def _read_sheet(sheet_name, header=None):
    wb = _get_wb()
    if wb is None or sheet_name not in wb.sheet_names:
        return pd.DataFrame()
    return pd.read_excel(wb, sheet_name=sheet_name, header=header)

def doc_live_price():
    df = _read_sheet("📡 LIVE PRICE FEED")
    if df.empty: return {}
    data = {}
    for i in range(2, len(df)):
        r = df.iloc[i]
        ma = str(r.iloc[0]).strip().upper()
        if not ma or ma == "NAN" or len(ma) > 6:
            continue
        try:
            gia = float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0
            thay_doi_pct = float(r.iloc[5]) if pd.notna(r.iloc[5]) else 0
            pe = float(r.iloc[6]) if pd.notna(r.iloc[6]) else 0
            pb = float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0
            kl = float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0
        except:
            continue
        data[ma] = {
            "ten": str(r.iloc[1]).strip()[:50] if pd.notna(r.iloc[1]) else "",
                "nganh": str(r.iloc[2]).strip()[:30] if pd.notna(r.iloc[2]) else "",
            "gia": gia, "thay_doi_pct": thay_doi_pct,
            "pe": pe, "pb": pb, "khoi_luong": kl,
        }
    return data

def doc_co_phieu_vn():
    df = _read_sheet("📈 Cổ Phiếu VN 🔍")
    if df.empty: return {}
    data = {}
    for i in range(3, len(df)):
        r = df.iloc[i]
        ma = str(r.iloc[0]).strip().upper()
        if not ma or ma == "NAN" or len(ma) > 6:
            continue
        try:
            data[ma] = {
                "ten": str(r.iloc[1]).strip()[:50] if pd.notna(r.iloc[1]) else "",
                "nganh": str(r.iloc[2]).strip()[:30] if pd.notna(r.iloc[2]) else "",
                "gia": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                "pe": float(r.iloc[4]) if pd.notna(r.iloc[4]) else 0,
                "pb": float(r.iloc[5]) if pd.notna(r.iloc[5]) else 0,
                "roe": float(r.iloc[6]) if pd.notna(r.iloc[6]) else 0,
                "von_hoa": float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0,
                "eps": float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0,
                "ytd": float(r.iloc[9]) if pd.notna(r.iloc[9]) else 0,
                "tin_hieu": str(r.iloc[10]).strip()[:20] if pd.notna(r.iloc[10]) else "",
                "ghi_chu": str(r.iloc[11]).strip()[:100] if pd.notna(r.iloc[11]) else "",
                "von_csh": float(r.iloc[12]) if pd.notna(r.iloc[12]) else 0,
                "no_vay": float(r.iloc[13]) if pd.notna(r.iloc[13]) else 0,
                "ebitda": float(r.iloc[14]) if pd.notna(r.iloc[14]) else 0,
                "dt_2025": float(r.iloc[15]) if pd.notna(r.iloc[15]) else 0,
                "lnst_2025": float(r.iloc[16]) if pd.notna(r.iloc[16]) else 0,
                "bien_ln": float(r.iloc[17]) if pd.notna(r.iloc[17]) else 0,
                "roic": float(r.iloc[18]) if pd.notna(r.iloc[18]) else 0,
                "de_ratio": float(r.iloc[19]) if pd.notna(r.iloc[19]) else 0,
                "co_tuc_pct": float(r.iloc[20]) if pd.notna(r.iloc[20]) else 0,
                "co_tuc_d": float(r.iloc[21]) if pd.notna(r.iloc[21]) else 0,
                "pct_ngoai": float(r.iloc[22]) if pd.notna(r.iloc[22]) else 0,
                "insider_pct": float(r.iloc[23]) if pd.notna(r.iloc[23]) else 0,
                "chu_tich": str(r.iloc[24]).strip()[:50] if pd.notna(r.iloc[24]) else "",
                "esg_score": str(r.iloc[25]).strip()[:20] if pd.notna(r.iloc[25]) else "",
                "dao_duc": str(r.iloc[26]).strip()[:20] if pd.notna(r.iloc[26]) else "",
                "canh_bao": str(r.iloc[27]).strip()[:50] if pd.notna(r.iloc[27]) else "",
                "san": str(r.iloc[28]).strip()[:10] if pd.notna(r.iloc[28]) else "",
            }
        except:
            continue
    return data

def doc_co_phieu_tg():
    df = _read_sheet("🌐 Cổ Phiếu TG 🔍")
    if df.empty: return {}
    data = {}
    for i in range(3, len(df)):
        r = df.iloc[i]
        ma = str(r.iloc[0]).strip().upper()
        if not ma or ma == "NAN" or len(ma) > 10:
            continue
        try:
            data[ma] = {
                "ten": str(r.iloc[1]).strip()[:50] if pd.notna(r.iloc[1]) else "",
                "san": str(r.iloc[2]).strip()[:10] if pd.notna(r.iloc[2]) else "",
                "tin_hieu": str(r.iloc[9]).strip()[:20] if pd.notna(r.iloc[9]) else "",
                "nganh": str(r.iloc[10]).strip()[:30] if pd.notna(r.iloc[10]) else "",
            }
        except:
            continue
    return data

def doc_danh_muc():
    df = _read_sheet("HỆ THỐNG QUẢN LÝ ")
    if df.empty: return {}
    data = {}
    for i in range(4, len(df)):
        r = df.iloc[i]
        ma = str(r.iloc[0]).strip().upper()
        if not ma or ma == "NAN" or len(ma) > 6:
            continue
        try:
            data[ma] = {
                "nganh": str(r.iloc[1]).strip()[:30] if pd.notna(r.iloc[1]) else "",
                "cong_ty": str(r.iloc[2]).strip()[:20] if pd.notna(r.iloc[2]) else "",
                "ty_trong_muc_tieu": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                "so_luong": float(r.iloc[4]) if pd.notna(r.iloc[4]) else 0,
                "gia_von": float(r.iloc[5]) if pd.notna(r.iloc[5]) else 0,
                "gia_thi_truong": float(r.iloc[6]) if pd.notna(r.iloc[6]) else 0,
                "von_hoa": float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0,
                "no_ky_quy": float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0,
            }
        except:
            continue
    return data

def doc_kpi():
    df = _read_sheet("📈 Dashboard KPI")
    if df.empty: return {}
    portfolio = {}
    kpi_header = None
    for i in range(len(df)):
        if str(df.iloc[i].tolist()[0]).strip() == "Mã CP":
            kpi_header = i
            break
    if kpi_header is not None:
        for i in range(kpi_header + 1, len(df)):
            r = df.iloc[i]
            ma = str(r.iloc[0]).strip().upper()
            if not ma or ma == "NAN" or len(ma) > 6:
                continue
            try:
                portfolio[ma] = {
                        "nganh": _chuong_hoa_tv_nganh(str(r.iloc[1]).strip()[:30] if pd.notna(r.iloc[1]) else ""),
                    "gia": float(r.iloc[2]) if pd.notna(r.iloc[2]) else 0,
                    "lai_lo_pct": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                    "roe": float(r.iloc[4]) if pd.notna(r.iloc[4]) else 0,
                    "pe": float(r.iloc[5]) if pd.notna(r.iloc[5]) else 0,
                    "upside": float(r.iloc[6]) if pd.notna(r.iloc[6]) else 0,
                    "diem_mua": float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0,
                    "diem_ban": float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0,
                    "ket_luan": _chuong_hoa_tv_ket_luan(str(r.iloc[9]).strip()[:30] if pd.notna(r.iloc[9]) else ""),
                    "hanh_dong": str(r.iloc[10]).strip()[:30] if pd.notna(r.iloc[10]) else "",
                    "ty_trong_ht": float(r.iloc[11]) if pd.notna(r.iloc[11]) else 0,
                    "ty_trong_mt": float(r.iloc[12]) if pd.notna(r.iloc[12]) else 0,
                    "chenh_lech": float(r.iloc[13]) if pd.notna(r.iloc[13]) else 0,
                    "beta": float(r.iloc[14]) if pd.notna(r.iloc[14]) else 0,
                    "var_1": float(r.iloc[15]) if pd.notna(r.iloc[15]) else 0,
                    "co_tuc": float(r.iloc[16]) if pd.notna(r.iloc[16]) else 0,
                    "trang_thai": str(r.iloc[17]).strip()[:20] if pd.notna(r.iloc[17]) else "",
                }
            except:
                continue
    return portfolio

def doc_liquid():
    df = _read_sheet("💧 Thanh Khoản ADTV")
    if df.empty: return {}
    data = {}
    for i in range(len(df)):
        if str(df.iloc[i].tolist()[0]).strip() == "Mã CP":
            for j in range(i + 1, len(df)):
                r = df.iloc[j]
                ma = str(r.iloc[0]).strip().upper()
                if not ma or ma == "NAN" or len(ma) > 6:
                    continue
                try:
                    data[ma] = {
                        "adtv": float(r.iloc[1]) if pd.notna(r.iloc[1]) else 0,
                        "gia": float(r.iloc[2]) if pd.notna(r.iloc[2]) else 0,
                        "gtgd_ngay": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                    }
                except:
                    continue
            break
    return data

def doc_esg():
    df = _read_sheet("🌱 ESG Scoring")
    if df.empty: return {}
    data = {}
    for i in range(len(df)):
        if str(df.iloc[i].tolist()[0]).strip() == "Ngành":
            for j in range(i + 1, len(df)):
                r = df.iloc[j]
                ten = str(r.iloc[0]).strip() if pd.notna(r.iloc[0]) else ""
                if not ten or ten == "nan":
                    continue
                try:
                    data[ten] = {
                        "e": str(r.iloc[1]) if pd.notna(r.iloc[1]) else "0%",
                        "s": str(r.iloc[2]) if pd.notna(r.iloc[2]) else "0%",
                        "g": str(r.iloc[3]) if pd.notna(r.iloc[3]) else "0%",
                        "mo_ta": str(r.iloc[5]).strip()[:100] if pd.notna(r.iloc[5]) else "",
                    }
                except:
                    continue
            break
    return data

def doc_stress():
    df = _read_sheet("🌪️ Macro Stress")
    if df.empty: return {}, {}
    variables = {}
    impact = {}
    for i in range(len(df)):
        r = df.iloc[i]
        v0 = str(r.iloc[0]).strip() if pd.notna(r.iloc[0]) else ""
        if "Lãi suất điều hành" in v0:
            variables["lai_suat"] = str(r.iloc[1]) if pd.notna(r.iloc[1]) else ""
        elif "Tỷ giá" in v0:
            variables["ty_gia"] = str(r.iloc[1]) if pd.notna(r.iloc[1]) else ""
        elif "Lạm phát" in v0:
            variables["lam_phat"] = str(r.iloc[1]) if pd.notna(r.iloc[1]) else ""
        elif "Giá thép" in v0:
            variables["gia_thep"] = str(r.iloc[1]) if pd.notna(r.iloc[1]) else ""
        elif "GDP" in v0:
            variables["gdp"] = str(r.iloc[1]) if pd.notna(r.iloc[1]) else ""
    for i in range(len(df)):
        if str(df.iloc[i].tolist()[0]).strip() == "Mã CP":
            for j in range(i + 1, len(df)):
                r = df.iloc[j]
                ma = str(r.iloc[0]).strip().upper()
                if not ma or ma == "NAN" or len(ma) > 6:
                    continue
                try:
                    impact[ma] = {
                    "nganh": str(r.iloc[1]).strip()[:30] if pd.notna(r.iloc[1]) else "",
                        "gia_ht": float(r.iloc[2]) if pd.notna(r.iloc[2]) else 0,
                        "pe_ht": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                        "tac_dong_ls": str(r.iloc[4]).strip()[:20] if pd.notna(r.iloc[4]) else "",
                        "tac_dong_tg": str(r.iloc[5]).strip()[:20] if pd.notna(r.iloc[5]) else "",
                        "tac_dong_lp": str(r.iloc[6]).strip()[:20] if pd.notna(r.iloc[6]) else "",
                        "pe_stress": float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0,
                        "gia_hop_ly_base": float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0,
                        "gia_hop_ly_stress": float(r.iloc[9]) if pd.notna(r.iloc[9]) else 0,
                        "chenh_lech": str(r.iloc[10]).strip()[:20] if pd.notna(r.iloc[10]) else "",
                        "downside": str(r.iloc[11]).strip()[:20] if pd.notna(r.iloc[11]) else "",
                        "hanh_dong": str(r.iloc[12]).strip()[:50] if pd.notna(r.iloc[12]) else "",
                    }
                except:
                    continue
            break
    return variables, impact

def doc_performance():
    df = _read_sheet("📊 Performance")
    if df.empty: return {}
    params = {}
    for i in range(len(df)):
        r = df.iloc[i]
        v0 = str(r.iloc[0]).strip() if pd.notna(r.iloc[0]) else ""
        v1 = r.iloc[1] if pd.notna(r.iloc[1]) else None
        if "Lãi suất phi rủi ro" in v0:
            params["Rf"] = float(v1) if v1 else 0.045
        elif "Lợi nhuận VN-Index" in v0:
            params["Rm"] = float(v1) if v1 else 0.082
        elif "Beta danh mục" in v0:
            params["Beta"] = float(v1) if v1 else 1.0
        elif "% Return" in v0:
            params["Rp"] = float(v1) if v1 else 0.168
        elif "Phí giao dịch" in v0:
            params["phi_gd"] = float(v1) if v1 else 0.0015
        elif "Thuế" in v0:
            params["thue"] = float(v1) if v1 else 0.001
    return params

_JSON_DIR = os.path.join(_PROJECT_DIR, "data")

_JSON_FALLBACK = {
    "live": "live.json",
    "co_phieu_vn": "co_phieu_vn.json",
    "co_phieu_tg": "co_phieu_tg.json",
    "danh_muc": "danh_muc.json",
    "kpi": "kpi.json",
    "liquid": "liquid.json",
    "esg": "esg.json",
    "performance": "performance.json",
    "stress_vars": "stress_vars.json",
    "stress": "stress.json",
}

def _load_json_fallback(key: str):
    fname = _JSON_FALLBACK.get(key)
    if not fname:
        return None
    fpath = os.path.join(_JSON_DIR, fname)
    if not os.path.exists(fpath):
        return None
    try:
        import json
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("JSON fallback '%s' failed: %s", fname, e)
        return None

def _safe_load(sheet_name: str, loader, key: str = "", default=None):
    try:
        data = loader()
        if data:
            return data
    except Exception as e:
        logger.warning("Sheet '%s' failed to load: %s", sheet_name, e)
    if key:
        fb = _load_json_fallback(key)
        if fb is not None:
            logger.info("Using JSON fallback for '%s'", key)
            return fb
    if key:
        snap = _get_snapshot(key)
        if snap is not None:
            logger.info("Using snapshot for '%s'", key)
            return snap
    return default if default is not None else {}

_LOADED = False

def load_all():
    global DOCS, _LOADED
    if _LOADED:
        return
    DOCS["live"] = _safe_load("live", doc_live_price, key="live")
    DOCS["co_phieu_vn"] = _safe_load("co_phieu_vn", doc_co_phieu_vn, key="co_phieu_vn")
    DOCS["co_phieu_tg"] = _safe_load("co_phieu_tg", doc_co_phieu_tg, key="co_phieu_tg")
    DOCS["danh_muc"] = _safe_load("danh_muc", doc_danh_muc, key="danh_muc")
    DOCS["kpi"] = _safe_load("kpi", doc_kpi, key="kpi", default={})
    DOCS["liquid"] = _safe_load("liquid", doc_liquid, key="liquid")
    DOCS["esg"] = _safe_load("esg", doc_esg, key="esg")
    DOCS["performance"] = _safe_load("performance", doc_performance, key="performance")
    sv, s = _safe_load("stress", lambda: doc_stress(), default=({}, {}))
    if not sv and not s:
        sv = _load_json_fallback("stress_vars") or {}
        s = _load_json_fallback("stress") or {}
        if not sv and not s:
            sv = _get_snapshot("stress_vars") or {}
            s = _get_snapshot("stress") or {}
    DOCS["stress_vars"], DOCS["stress"] = sv, s
    DOCS["ngay_cap_nhat"] = _NGAY_FILE
    kpi = DOCS.get("kpi", {})
    for _ma, _info in DOCS.get("kpi", {}).items():
        if _info.get("nganh"):
            _info["nganh"] = _chuong_hoa_tv_nganh(_info["nganh"])
        if _info.get("ket_luan"):
            _info["ket_luan"] = _chuong_hoa_tv_ket_luan(_info["ket_luan"])
    for _ma, _info in DOCS.get("co_phieu_vn", {}).items():
        if _info.get("nganh"):
            _info["nganh"] = _chuong_hoa_tv_nganh(_info["nganh"])
        if _info.get("tin_hieu"):
            _info["tin_hieu"] = _chuong_hoa_tv_ket_luan(_info["tin_hieu"])
    for _ma, _info in DOCS.get("co_phieu_tg", {}).items():
        if _info.get("nganh"):
            _info["nganh"] = _chuong_hoa_tv_nganh(_info["nganh"])
        if _info.get("tin_hieu"):
            _info["tin_hieu"] = _chuong_hoa_tv_ket_luan(_info["tin_hieu"])
    for _ma, _info in DOCS.get("danh_muc", {}).items():
        if _info.get("nganh"):
            _info["nganh"] = _chuong_hoa_tv_nganh(_info["nganh"])
    _fallback_portfolio = ["FPT", "MBB", "VCB", "CTR", "MWG", "HPG", "VNM", "VIX"]
    DOCS["danh_sach_portfolio"] = sorted(
        [k for k in kpi.keys() if k != "NAN"],
        key=lambda x: kpi[x].get("ty_trong_ht", 0) if x in kpi else 0,
        reverse=True,
    ) or _fallback_portfolio
    _dong_bo_performance_tu_danh_muc()
    _LOADED = True

DOCS = {
    "live": {}, "co_phieu_vn": {}, "co_phieu_tg": {}, "danh_muc": {},
    "kpi": {}, "liquid": {}, "esg": {}, "performance": {},
    "stress_vars": {}, "stress": {}, "ngay_cap_nhat": _NGAY_FILE,
    "danh_sach_portfolio": ["FPT", "MBB", "VCB", "CTR", "MWG", "HPG", "VNM", "VIX"],
}

import threading
_DOCS_LOCK = threading.Lock()
def tu_dong_cap_nhat():
    def _reload():
        try:
            with _DOCS_LOCK:
                DOCS["live"] = doc_live_price()
                DOCS["co_phieu_vn"] = doc_co_phieu_vn()
                DOCS["co_phieu_tg"] = doc_co_phieu_tg()
                DOCS["kpi"] = doc_kpi()
                DOCS["liquid"] = doc_liquid()
                DOCS["stress_vars"], DOCS["stress"] = doc_stress()
        except Exception as e:
            logger.warning("Auto-reload failed: %s", e)
    t = threading.Thread(target=_reload, daemon=True)
    t.start()
