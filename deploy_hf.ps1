# ============================================================
# Hướng dẫn deploy lên Hugging Face Spaces (miễn phí)
# Không bị fair-use limit như Streamlit Cloud
# ============================================================
#
# Cách 1: Deploy tự động (cần token)
#   1. Vào https://huggingface.co/settings/tokens → New token
#   2. Copy token, chạy:
#      $env:HF_TOKEN="hf_..." ; .\deploy_hf.ps1
#
# Cách 2: Deploy thủ công qua web (dễ hơn)
#   1. Vào https://huggingface.co/new-space
#   2. Tên: robo-advisor
#   3. SDK: chọn Streamlit
#   4. Space hardware: Free
#   5. Connect GitHub repo: datdanh279-dev/robo-advisor
#   6. Create Space → auto deploy sau 2-3 phút
#   7. URL: https://{username}-robo-advisor.hf.space

$HF_TOKEN = $env:HF_TOKEN
if (-not $HF_TOKEN) {
    Write-Host "Chưa có HF_TOKEN. Set bằng: `$env:HF_TOKEN=""hf_...""" -ForegroundColor Yellow
    Write-Host "Hoặc deploy thủ công qua web (xem hướng dẫn trên)." -ForegroundColor Yellow
    exit 0
}

# Cấu hình
$SPACE_NAME = "robo-advisor"
$USERNAME = "soi-co-doc"

Write-Host "Đang tạo Space: $USERNAME/$SPACE_NAME ..." -ForegroundColor Green

# Tạo Space config
@"
sdk: streamlit
sdk_version: "1.58.0"
app_file: app.py
"@ | Out-File -FilePath "C:\Users\ACER\robo-advisor\.space.yaml" -Encoding utf8

Write-Host "✅ File .space.yaml đã tạo." -ForegroundColor Green
Write-Host ""
Write-Host "Sau khi deploy, app sẽ ở: https://$USERNAME-$SPACE_NAME.hf.space" -ForegroundColor Cyan
Write-Host "Deploy bằng cách push code lên GitHub → HF tự sync." -ForegroundColor Cyan
