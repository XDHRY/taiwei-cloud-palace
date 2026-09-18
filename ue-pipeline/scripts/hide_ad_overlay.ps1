param([long]$Hwnd = 4522168)
$sig = @"
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool ShowWindowAsync(System.IntPtr h, int n);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr h, int n);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool IsWindowVisible(System.IntPtr h);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool SetWindowPos(System.IntPtr h, System.IntPtr after, int x, int y, int cx, int cy, uint flags);
"@
Add-Type -MemberDefinition $sig -Name U32Win -Namespace WinUtil
$h = [System.IntPtr]::new($Hwnd)
# SW_HIDE = 0
[WinUtil.U32Win]::ShowWindow($h, 0) | Out-Null
Start-Sleep -Milliseconds 400
$vis = [WinUtil.U32Win]::IsWindowVisible($h)
Write-Output "visible_after_hide=$vis"
if ($vis) {
  # fallback: move off-screen (SWP_NOSIZE=0x1 SWP_NOZORDER=0x4)
  [WinUtil.U32Win]::SetWindowPos($h, [System.IntPtr]::Zero, -4000, -4000, 0, 0, 0x1 -bor 0x4) | Out-Null
  Write-Output "moved_offscreen"
}
