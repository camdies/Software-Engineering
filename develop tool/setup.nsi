; ================================================================
; EduMgmt-Setup.nsi -- University Course Management System Setup
; ================================================================
; Build: makensis.exe setup.nsi
; Requires: dist-bundle\ folder prepared by build_installer.bat
; ================================================================

!include "MUI2.nsh"
!include "LogicLib.nsh"

; --- Installer metadata ---
Name "EduMgmt System v3.0"
OutFile "EduMgmt-Setup-3.0.0.exe"
Unicode True
InstallDir "$LOCALAPPDATA\EduMgmt"
InstallDirRegKey HKLM "Software\EduMgmt" "InstallDir"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

VIProductVersion "3.0.0.0"
VIAddVersionKey "ProductName"     "EduMgmt System"
VIAddVersionKey "ProductVersion"  "3.0.0"
VIAddVersionKey "FileVersion"     "3.0.0.0"
VIAddVersionKey "FileDescription" "University Course Management System Setup"
VIAddVersionKey "CompanyName"     "SCNU Software Engineering"
VIAddVersionKey "LegalCopyright"  "AGPL-3.0"

; --- MUI Pages ---
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\win.bmp"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\run.bat"
!define MUI_FINISHPAGE_RUN_TEXT "Launch EduMgmt System"
!define MUI_FINISHPAGE_LINK "Create desktop shortcut"
!define MUI_FINISHPAGE_LINK_LOCATION "$INSTDIR"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Add Desktop Shortcut"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION CreateDesktopShortcut

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"

; --- Components ---
InstType "Full (recommended)"
InstType "Compact"

Var VC_NEEDED

Section "-vcDetect"
    SetRegView 64
    ReadRegDword $R0 HKLM "SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" "Installed"
    ${If} $R0 == 1
        StrCpy $VC_NEEDED "0"
    ${Else}
        StrCpy $VC_NEEDED "1"
    ${EndIf}
    SetRegView lastused
SectionEnd

SectionGroup "!Core Components"
    Section "Flask Backend" SecBackend
        SectionIn 1 2
        SetOutPath "$INSTDIR"
        DetailPrint "Installing backend..."
        SetOutPath "$INSTDIR\backend"
        File /r /x "__pycache__" /x "*.pyc" /x "config.ini" /x ".env" "backend\*.*"
        SetOutPath "$INSTDIR\backend\config"
        ${If} ${FileExists} "$INSTDIR\backend\config\config.ini"
        ${Else}
            File "backend\config\config.ini.example"
            Rename "$INSTDIR\backend\config\config.ini.example" "$INSTDIR\backend\config\config.ini"
        ${EndIf}
        SetOutPath "$INSTDIR"
        File "run.py"
        File "start_mysql.py"
        DetailPrint "Backend installed"
    SectionEnd
    Section "Vue Frontend" SecFrontend
        SectionIn 1 2
        SetOutPath "$INSTDIR"
        DetailPrint "Installing frontend..."
        SetOutPath "$INSTDIR\frontend\dist"
        File /r "frontend\dist\*.*"
        DetailPrint "Frontend installed"
    SectionEnd
    Section "MySQL Portable" SecMySQL
        SectionIn 1 2
        SetOutPath "$INSTDIR"
        DetailPrint "Installing MySQL Portable..."
        SetOutPath "$INSTDIR\mysql-portable"
        File /r /x "data" /x "*.auto" "mysql-portable\*.*"
        DetailPrint "MySQL Portable installed (data dir created on first launch)"
    SectionEnd
    Section "Startup Scripts" SecScripts
        SectionIn 1 2
        SetOutPath "$INSTDIR"
        DetailPrint "Installing scripts..."
        File "dist-bundle\run.bat"
        File "dist-bundle\stop.bat"
        DetailPrint "Scripts installed"
    SectionEnd
SectionGroupEnd

SectionGroup "!Runtime"
    Section "Embedded Python 3.11" SecPython
        SectionIn 1
        SetOutPath "$INSTDIR"
        DetailPrint "Installing embedded Python..."
        SetOutPath "$INSTDIR\python-embed"
        File /r "dist-bundle\python-embed\*.*"
        DetailPrint "Embedded Python installed"
    SectionEnd
    Section "VC++ Redist" SecVC
        SectionIn 1 2
        ${If} $VC_NEEDED == "1"
            DetailPrint "Installing VC++ Redist..."
            File "dist-bundle\vc_redist.x64.exe"
            ExecWait '"$INSTDIR\vc_redist.x64.exe" /install /quiet /norestart' $R1
            Delete "$INSTDIR\vc_redist.x64.exe"
            ${If} $R1 == 0
                DetailPrint "VC++ Redist installed"
            ${Else}
                DetailPrint "WARNING: VC++ Redist install failed (exit $R1)"
                DetailPrint "mysqld.exe may not start. Install manually from:"
                DetailPrint "https://aka.ms/vs/17/release/vc_redist.x64.exe"
            ${EndIf}
        ${EndIf}
    SectionEnd
SectionGroupEnd

Section "Desktop Shortcut" SecShortcut
    SectionIn 1 2
    SetOutPath "$INSTDIR"
    DetailPrint "Creating shortcuts..."
    CreateShortCut "$DESKTOP\EduMgmt.lnk" "$INSTDIR\run.bat" "" "$SYSDIR\shell32.dll" 25 "" "" "Launch EduMgmt System"
    CreateDirectory "$SMPROGRAMS\EduMgmt"
    CreateShortCut "$SMPROGRAMS\EduMgmt\Start EduMgmt.lnk" "$INSTDIR\run.bat"
    CreateShortCut "$SMPROGRAMS\EduMgmt\Stop All Services.lnk" "$INSTDIR\stop.bat"
    CreateShortCut "$SMPROGRAMS\EduMgmt\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    DetailPrint "Shortcuts created"
SectionEnd

Section "-post"
    SetOutPath "$INSTDIR"
    WriteRegStr HKLM "Software\EduMgmt" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\EduMgmt" "Version" "3.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EduMgmt" \
        "DisplayName" "EduMgmt System v3.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EduMgmt" \
        "DisplayVersion" "3.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EduMgmt" \
        "Publisher" "SCNU Software Engineering"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EduMgmt" \
        "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EduMgmt" \
        "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EduMgmt" \
        "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EduMgmt" \
        "EstimatedSize" 120000
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; --- Uninstall ---
Section "Uninstall"
    DetailPrint "Stopping services..."
    nsExec::ExecToLog 'taskkill /FI "WINDOWTITLE eq EduMgmt MySQL" /F 2>nul'
    nsExec::ExecToLog 'taskkill /FI "WINDOWTITLE eq EduMgmt Flask" /F 2>nul'
    Sleep 2000

    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Keep MySQL database data (mysql-portable\data\)?$\n$\nChoose YES to keep data, NO to delete everything." \
        IDYES keep IDNO clean

    clean:
        RMDir /r "$INSTDIR\python-embed"
        RMDir /r "$INSTDIR\backend"
        RMDir /r "$INSTDIR\frontend"
        RMDir /r "$INSTDIR\mysql-portable"
        Delete "$INSTDIR\run.bat"
        Delete "$INSTDIR\stop.bat"
        Delete "$INSTDIR\run.py"
        Delete "$INSTDIR\uninstall.exe"
        RMDir "$INSTDIR"
        Goto done

    keep:
        RMDir /r "$INSTDIR\python-embed"
        RMDir /r "$INSTDIR\backend"
        RMDir /r "$INSTDIR\frontend"
        RMDir /r "$INSTDIR\mysql-portable\bin"
        RMDir /r "$INSTDIR\mysql-portable\lib"
        Delete "$INSTDIR\mysql-portable\my.ini"
        Delete "$INSTDIR\mysql-portable\my.ini.auto"
        Delete "$INSTDIR\run.bat"
        Delete "$INSTDIR\stop.bat"
        Delete "$INSTDIR\run.py"
        Delete "$INSTDIR\uninstall.exe"
        RMDir "$INSTDIR"

    done:
        Delete "$DESKTOP\EduMgmt.lnk"
        RMDir /r "$SMPROGRAMS\EduMgmt"
        DeleteRegKey HKLM "Software\EduMgmt"
        DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EduMgmt"
        DetailPrint "Uninstall complete"
SectionEnd

Function CreateDesktopShortcut
    CreateShortCut "$DESKTOP\EduMgmt.lnk" "$INSTDIR\run.bat" "" "$SYSDIR\shell32.dll" 25 "" "" "Launch EduMgmt System"
FunctionEnd

Function .onInit
    ; Only check for actual service windows, not the installer itself
    nsExec::ExecToStack 'tasklist /FI "WINDOWTITLE eq EduMgmt MySQL" /FO CSV /NH 2>nul'
    Pop $R0
    ${If} $R0 != 0
        StrCpy $R0 "1"  ; tasklist returns 1 when no match found, which is fine
    ${Else}
        StrLen $R1 $R0
        ${If} $R1 > 5
            MessageBox MB_ICONSTOP|MB_OK \
                "EduMgmt is already running. Please close all EduMgmt windows (MySQL/Flask) before installing."
            Abort
        ${EndIf}
    ${EndIf}
    nsExec::ExecToStack 'tasklist /FI "WINDOWTITLE eq EduMgmt Flask" /FO CSV /NH 2>nul'
    Pop $R0
    ${If} $R0 != 0
        StrCpy $R0 "1"
    ${Else}
        StrLen $R1 $R0
        ${If} $R1 > 5
            MessageBox MB_ICONSTOP|MB_OK \
                "EduMgmt is already running. Please close all EduMgmt windows (MySQL/Flask) before installing."
            Abort
        ${EndIf}
    ${EndIf}
    UserInfo::GetAccountType
    Pop $R0
    ${If} $R0 != "Admin"
        MessageBox MB_ICONSTOP|MB_OK \
            "Administrator privileges required. Right-click the installer and Run as Administrator."
        Abort
    ${EndIf}
FunctionEnd
