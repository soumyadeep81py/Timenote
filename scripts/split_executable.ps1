# PowerShell script to split large executable for GitHub upload
# Splits Timenote.exe into chunks smaller than 25MB

param(
    [string]$InputFile = "dist\Timenote.exe",
    [string]$OutputDir = "dist\split",
    [int]$ChunkSize = 20MB  # 20MB chunks to stay well under GitHub's 25MB limit
)

Write-Host "Splitting Timenote executable for GitHub..." -ForegroundColor Green

# Check if input file exists
if (-not (Test-Path $InputFile)) {
    Write-Error "Input file '$InputFile' not found!"
    Write-Host "Please build the executable first using: scripts\build_exe.bat" -ForegroundColor Yellow
    exit 1
}

# Get file info
$fileInfo = Get-Item $InputFile
$fileSize = $fileInfo.Length
$fileName = $fileInfo.BaseName
$fileExt = $fileInfo.Extension

Write-Host "File: $($fileInfo.Name)"
Write-Host "Size: $([math]::Round($fileSize/1MB, 2)) MB"

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Created directory: $OutputDir"
}

# Calculate number of chunks needed
$chunksNeeded = [math]::Ceiling($fileSize / $ChunkSize)
Write-Host "Will create $chunksNeeded chunks of max $([math]::Round($ChunkSize/1MB, 0))MB each"

# Read the file and split it
$buffer = New-Object byte[] $ChunkSize
$inputStream = [System.IO.File]::OpenRead($InputFile)

try {
    for ($i = 0; $i -lt $chunksNeeded; $i++) {
        $chunkNumber = $i + 1
        $outputFileName = "$OutputDir\${fileName}.part$($chunkNumber.ToString('000'))"
        
        $bytesRead = $inputStream.Read($buffer, 0, $ChunkSize)
        
        if ($bytesRead -gt 0) {
            $outputStream = [System.IO.File]::Create($outputFileName)
            $outputStream.Write($buffer, 0, $bytesRead)
            $outputStream.Close()
            
            $chunkSize = [math]::Round($bytesRead/1MB, 2)
            Write-Host "Created: $(Split-Path $outputFileName -Leaf) ($chunkSize MB)"
        }
    }
} finally {
    $inputStream.Close()
}

Write-Host "`nSplit complete!" -ForegroundColor Green
Write-Host "Upload all .part files to GitHub, then use the reconstruction script." -ForegroundColor Yellow

# Create reconstruction script
$reconstructScript = @"
@echo off
echo Reconstructing Timenote.exe from parts...

if not exist "Timenote.part001" (
    echo Error: Part files not found!
    echo Please ensure all .part files are in the current directory.
    pause
    exit /b 1
)

copy /b Timenote.part* Timenote.exe
if %errorlevel% equ 0 (
    echo Success! Timenote.exe reconstructed.
    echo You can now run Timenote.exe
) else (
    echo Error occurred during reconstruction.
)
pause
"@

$reconstructScript | Out-File -FilePath "$OutputDir\reconstruct.bat" -Encoding ascii
Write-Host "Created reconstruction script: $OutputDir\reconstruct.bat" -ForegroundColor Cyan

# Create README for the split files
$splitReadme = @"
# Timenote Executable - Split Archive

This directory contains the Timenote executable split into parts due to GitHub's 25MB file size limit.

## Files
"@

Get-ChildItem "$OutputDir\*.part*" | ForEach-Object {
    $size = [math]::Round($_.Length/1MB, 2)
    $splitReadme += "`n- $($_.Name) ($size MB)"
}

$splitReadme += @"

## Reconstruction Instructions

### Windows:
1. Download all .part files to the same directory
2. Run the included `reconstruct.bat` script
3. The original `Timenote.exe` will be created

### Manual (Command Line):
``````cmd
copy /b Timenote.part* Timenote.exe
``````

### PowerShell:
``````powershell
Get-Content Timenote.part* -Raw -Encoding Byte | Set-Content Timenote.exe -Encoding Byte
``````

## Verification
After reconstruction:
- File size should be approximately 35MB
- You should be able to run Timenote.exe normally

## Alternative
Instead of using split files, consider downloading from GitHub Releases where the full executable is available without splitting.
"@

$splitReadme | Out-File -FilePath "$OutputDir\README.md" -Encoding utf8
Write-Host "Created: $OutputDir\README.md" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Magenta
Write-Host "1. Add the split files to git: git add $OutputDir" -ForegroundColor White
Write-Host "2. Commit and push to GitHub" -ForegroundColor White
Write-Host "3. Users can download and reconstruct using the provided script" -ForegroundColor White