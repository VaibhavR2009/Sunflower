$Url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
$OutFile = Join-Path $PSScriptRoot "face_landmarker.task"

Write-Host "Downloading MediaPipe Face Landmarker model..."
curl.exe -L $Url -o $OutFile

if (Test-Path $OutFile) {
    $size = (Get-Item $OutFile).Length
    if ($size -gt 1000000) {
        Write-Host "Model downloaded successfully: $OutFile ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "The model file looks too small. Check the download." -ForegroundColor Yellow
    }
} else {
    Write-Host "Download failed." -ForegroundColor Red
}
