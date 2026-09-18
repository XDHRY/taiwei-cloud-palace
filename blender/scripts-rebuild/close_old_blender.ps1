$procs = Get-Process blender -ErrorAction SilentlyContinue
if (-not $procs) { Write-Output 'NO_BLENDER'; exit 0 }
foreach ($p in $procs) {
    Write-Output "Closing PID $($p.Id)..."
    $null = $p.CloseMainWindow()
}
Start-Sleep -Seconds 3
$procs = Get-Process blender -ErrorAction SilentlyContinue
if ($procs) {
    foreach ($p in $procs) {
        Write-Output "Stopping PID $($p.Id)..."
        Stop-Process -Id $p.Id -Force
    }
}
Write-Output 'ALL_CLOSED'
