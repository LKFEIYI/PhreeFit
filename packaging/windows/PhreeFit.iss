#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\\..\\dist\\windows\\PhreeFit"
#endif
#ifndef OutputDir
  #define OutputDir "..\\..\\dist\\windows"
#endif

[Setup]
AppId={{72D600A1-A831-45E7-B8E2-7E0DCA94286A}
AppName=PhreeFit
AppVersion={#MyAppVersion}
AppPublisher=PhreeFit
DefaultDirName={localappdata}\Programs\PhreeFit
DefaultGroupName=PhreeFit
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename=PhreeFit-{#MyAppVersion}-win-x64-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=PhreeFit
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\PhreeFit"; Filename: "{app}\PhreeFit.exe"
Name: "{autodesktop}\PhreeFit"; Filename: "{app}\PhreeFit.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PhreeFit.exe"; Description: "Launch PhreeFit"; Flags: nowait postinstall skipifsilent
