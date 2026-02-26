#define AppName "PyStart"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppPublisher "PyStart"
#define AppURL "https://github.com/PyStart"
#define AppExeName "PyStart.exe"

#ifndef OutputFileName
  #define OutputFileName "PyStart-win7-Setup"
#endif

[Setup]
AppId={{A7B9C1D2-E3F4-4567-8901-23456789ABCD}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename={#OutputFileName}
; 使用相对于 ISS 文件的路径
SetupIconFile=..\assets\installer.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[Files]
; 源路径全部改为相对于 packaging 目录的相对路径
Source: "..\dist\app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\src\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\PyStart.bmp"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{autoprograms}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"
