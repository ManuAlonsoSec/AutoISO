[Setup]
AppName=ISO Autoupdater
AppVersion=1.0.0
AppPublisher=ManuAlonsoSec
DefaultDirName={autopf}\ISOAutoupdater
DefaultGroupName=ISO Autoupdater
OutputDir=..\output
OutputBaseFilename=ISOAutoupdater-1.0.0-windows-setup
SetupIconFile=..\..\iso-autoupdater\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "..\..\iso-autoupdater\dist\ISOAutoupdater.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ISO Autoupdater"; Filename: "{app}\ISOAutoupdater.exe"
Name: "{autodesktop}\ISO Autoupdater"; Filename: "{app}\ISOAutoupdater.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\ISOAutoupdater.exe"; Description: "Launch ISO Autoupdater"; Flags: nowait postinstall skipifsilent
