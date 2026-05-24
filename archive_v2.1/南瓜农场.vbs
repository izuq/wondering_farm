Set fso = CreateObject("Scripting.FileSystemObject")
curDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set ws = CreateObject("Wscript.Shell")
ws.CurrentDirectory = curDir

' 修复快捷方式路径，确保项目迁移后依然可用
lnkPath = curDir & "\南瓜农场.lnk"
If fso.FileExists(lnkPath) Then
    Set sc = ws.CreateShortcut(lnkPath)
    sc.TargetPath = curDir & "\南瓜农场.vbs"
    sc.WorkingDirectory = curDir
    sc.IconLocation = curDir & "\南瓜农场.ico, 0"
    sc.Save()
End If

ws.Run "python farm_tkinter_v2.py", 0, False
