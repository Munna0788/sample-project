Set WshShell = CreateObject("WScript.Shell")
strPath = WshShell.CurrentDirectory
WshShell.Run chr(34) & "C:\Users\VICTUS\.gemini\antigravity\scratch\sample-project\start_spotlight.bat" & Chr(34), 0
Set WshShell = Nothing
