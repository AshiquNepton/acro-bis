param(
    [string]$SourceDir = "D:\PROJECTS\VsCode Project\ACRO-BIS",
    [string]$BackupBaseDir = "E:\ACRO_DEV_BACKUP",
    [int]$RetentionDays = 14
)

$ErrorActionPreference = "Stop"

# Generate Date String (YYYY-MM-DD)
$DateStr = Get-Date -Format "yyyy-MM-dd"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$TargetDir = Join-Path -Path $BackupBaseDir -ChildPath $DateStr
$LogFile = Join-Path -Path $SourceDir -ChildPath "logs\backup.log"

# Ensure directories exist
if (-not (Test-Path -Path $BackupBaseDir)) {
    New-Item -ItemType Directory -Path $BackupBaseDir -Force | Out-Null
}
if (-not (Test-Path -Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}
$LogsDir = Join-Path -Path $SourceDir -ChildPath "logs"
if (-not (Test-Path -Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}

function Write-BackupLog {
    param([string]$Message)
    $Entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $Entry
    Add-Content -Path $LogFile -Value $Entry
}

Write-BackupLog "=================================================="
Write-BackupLog "Starting Daily Project Backup"
Write-BackupLog "Source: $SourceDir"
Write-BackupLog "Destination: $TargetDir"

# Exclude unnecessary heavy directories/files
$ExcludeDirs = @("venv", "__pycache__", ".git", "backups", "staticfiles")
$ExcludeExtensions = @("*.pyc", "*.pyo", "*.log", "*.tmp")

try {
    $TotalFilesCopied = 0
    
    # Copy files while mirroring directory structure
    Get-ChildItem -Path $SourceDir -Recurse | ForEach-Object {
        $Item = $_
        
        # Check if item resides inside excluded directories
        $RelativePath = $Item.FullName.Substring($SourceDir.Length).TrimStart("\")
        $PathParts = $RelativePath.Split("\")
        
        $IsExcluded = $false
        foreach ($ExDir in $ExcludeDirs) {
            if ($PathParts -contains $ExDir) {
                $IsExcluded = $true
                break
            }
        }
        
        if (-not $IsExcluded) {
            $DestPath = Join-Path -Path $TargetDir -ChildPath $RelativePath
            
            if ($Item.PSIsContainer) {
                if (-not (Test-Path -Path $DestPath)) {
                    New-Item -ItemType Directory -Path $DestPath -Force | Out-Null
                }
            } else {
                # Check extension exclusion
                $ExtMatch = $false
                foreach ($Ext in $ExcludeExtensions) {
                    if ($Item.Name -like $Ext) {
                        $ExtMatch = $true
                        break
                    }
                }
                
                if (-not $ExtMatch) {
                    # Only copy if file doesn't exist or was modified
                    $ShouldCopy = $true
                    if (Test-Path -Path $DestPath) {
                        $DestItem = Get-Item -Path $DestPath
                        if ($Item.LastWriteTime -le $DestItem.LastWriteTime) {
                            $ShouldCopy = $false
                        }
                    }
                    
                    if ($ShouldCopy) {
                        Copy-Item -Path $Item.FullName -Destination $DestPath -Force
                        $TotalFilesCopied++
                    }
                }
            }
        }
    }
    
    # Save a git diff summary if git is available
    try {
        $GitDiff = git -C $SourceDir diff --stat 2>$null
        if ($GitDiff) {
            $DiffFile = Join-Path -Path $TargetDir -ChildPath "git_changes_summary.txt"
            Set-Content -Path $DiffFile -Value $GitDiff
            Write-BackupLog "Recorded Git diff changes summary to git_changes_summary.txt"
        }
    } catch {
        # Non-fatal if git is not in PATH
    }
    
    Write-BackupLog "Daily backup completed successfully. Total updated/copied files: $TotalFilesCopied"

    # Retention cleanup (keep backups for specified retention days)
    Get-ChildItem -Path $BackupBaseDir -Directory | ForEach-Object {
        if ($_.Name -match '^\d{4}-\d{2}-\d{2}$') {
            $DirDate = [datetime]::ParseExact($_.Name, 'yyyy-MM-dd', $null)
            $Age = (Get-Date) - $DirDate
            if ($Age.Days -gt $RetentionDays) {
                Write-BackupLog "Purging old backup directory: $($_.FullName)"
                Remove-Item -Path $_.FullName -Recurse -Force
            }
        }
    }

} catch {
    Write-BackupLog "[ERROR] Backup failed with error: $_"
    exit 1
}

Write-BackupLog "Backup operation finished."
Write-BackupLog "=================================================="
