# TestPilot 一键启动脚本（Windows PowerShell）
# 1) 启动 Mock 被测系统  2) 启动 Streamlit 平台
$root = $PSScriptRoot

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; python mock_server/app.py"
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; streamlit run app.py"
Write-Host "Mock 服务: http://127.0.0.1:9999  |  平台: http://localhost:8501"
