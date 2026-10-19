"""Builds the .vsix package. Install with: code --install-extension speak-language-<version>.vsix --force"""
import json, zipfile
version = json.load(open('package.json'))['version']
import glob
files = ['package.json', 'extension.js', 'language-configuration.json', 'README.md', 'src/speak.py', 'src/speak_debug.py', 'src/debug_adapter.py',
         'syntaxes/speak.tmLanguage.json', 'snippets/speak.json', 'icons/speak.png', 'icons/speak-file.svg', 'LIBRARIES.md']
files += sorted(glob.glob('src/speak_libraries/*.py'))
manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id="speak-language" Version="{version}" Publisher="local"/>
    <DisplayName>Speak</DisplayName>
    <Description xml:space="preserve">A readable pseudocode language that runs on Python.</Description>
    <Categories>Programming Languages</Categories>
  </Metadata>
  <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>
  <Dependencies/>
  <Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets>
</PackageManifest>'''
types = '''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/Content-Types">
  <Default Extension=".json" ContentType="application/json"/>
  <Default Extension=".js" ContentType="application/javascript"/>
  <Default Extension=".py" ContentType="text/plain"/>
  <Default Extension=".md" ContentType="text/markdown"/>
  <Default Extension=".png" ContentType="image/png"/>
  <Default Extension=".svg" ContentType="image/svg+xml"/>
  <Default Extension=".vsixmanifest" ContentType="text/xml"/>
</Types>'''
name = f'speak-language-{version}.vsix'
with zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', types)
    z.writestr('extension.vsixmanifest', manifest)
    for f in files:
        z.write(f, 'extension/' + f)
print('built', name)
