[Setup]
AppName=FusionFlows
AppVersion=3.9.1
WizardStyle=modern
DefaultDirName={localappdata}\Programs\FusionFlows
DefaultGroupName=FusionFlows
OutputBaseFilename=FusionFlows-Windows
SetupIconFile=fusionflows.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\FusionFlows.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "fusionflows.ini"; DestDir: "{app}"; Flags: ignoreversion
Source: "fusionflows.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "facefusion\flowframes_bin\*"; DestDir: "{app}\flowframes_bin"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\FusionFlows"; Filename: "{app}\FusionFlows.exe"; IconFilename: "{app}\fusionflows.ico"
Name: "{group}\{cm:UninstallProgram,FusionFlows}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\FusionFlows"; Filename: "{app}\FusionFlows.exe"; IconFilename: "{app}\fusionflows.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\FusionFlows.exe"; Description: "{cm:LaunchProgram,FusionFlows}"; Flags: nowait postinstall skipifsilent
