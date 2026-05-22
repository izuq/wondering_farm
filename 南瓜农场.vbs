Set fso = CreateObject("Scripting.FileSystemObject")
curDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set ws = CreateObject("Wscript.Shell")
ws.CurrentDirectory = curDir

' 更新快捷方式图标路径，确保移动到其他目录后图标依然有效
lnkPath = curDir & "\南瓜农场.lnk"
icoPath = curDir & "\南瓜农场.ico"
If fso.FileExists(lnkPath) And fso.FileExists(icoPath) Then
    Set sc = ws.CreateShortcut(lnkPath)
    sc.IconLocation = icoPath & ", 0"
    sc.Save()
End If

ws.Run "python farm_tkinter_v2.py", 0, False
