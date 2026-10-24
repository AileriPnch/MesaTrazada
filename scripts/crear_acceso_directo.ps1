# Crea (o reemplaza) en el escritorio un acceso directo que abre la app sin consola,
# con el ícono propio y el AppUserModelID de la app (agrupa bien en la barra de tareas).
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File scripts\crear_acceso_directo.ps1
param(
    # Carpeta donde crear el acceso directo. Por defecto, el Escritorio real del usuario.
    [string]$Destino = [Environment]::GetFolderPath('Desktop')
)
$ErrorActionPreference = 'Stop'

# Debe coincidir con APP_USER_MODEL_ID en src/app/windows_integration.py
$appUserModelId = 'JScandizzo.MesaTrazada'

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonw = Join-Path $projectRoot '.venv\Scripts\pythonw.exe'
$mainPy = Join-Path $projectRoot 'main.py'
$icon = Join-Path $projectRoot 'assets\app_icon_blender.ico'

foreach ($required in @($pythonw, $mainPy, $icon)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "No se encontró: $required"
    }
}

# GetFolderPath resuelve la ubicación real del Escritorio, aunque esté redirigido a la nube.
if (-not $Destino -or -not (Test-Path -LiteralPath $Destino)) {
    throw "No existe la carpeta de destino: $Destino"
}
$shortcutPath = Join-Path $Destino 'Mesa Trazada.lnk'
$legacyPath = Join-Path $Destino 'Ajedrez y Solitario.lnk'  # el acceso directo con el nombre anterior
if (Test-Path -LiteralPath $legacyPath) {
    Remove-Item -LiteralPath $legacyPath -Force
    Write-Host "Acceso directo con el nombre anterior eliminado."
}
if (Test-Path -LiteralPath $shortcutPath) {
    Remove-Item -LiteralPath $shortcutPath -Force
    Write-Host "Acceso directo anterior eliminado."
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = '"' + $mainPy + '"'
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = 'Mesa Trazada: ajedrez contra Stockfish y Solitario Klondike'
$shortcut.IconLocation = "$icon,0"
$shortcut.Save()

# WScript.Shell no expone System.AppUserModel.ID: se graba vía IPropertyStore.
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class ShortcutAppId {
    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    struct PropertyKey { public Guid FormatId; public uint PropertyId; }

    [StructLayout(LayoutKind.Explicit)]
    struct PropVariant {
        [FieldOffset(0)] public ushort VarType;
        [FieldOffset(8)] public IntPtr Pointer;
        [FieldOffset(16)] public IntPtr Padding;
    }

    [ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IPropertyStore {
        [PreserveSig] int GetCount(out uint count);
        [PreserveSig] int GetAt(uint index, out PropertyKey key);
        [PreserveSig] int GetValue(ref PropertyKey key, out PropVariant value);
        [PreserveSig] int SetValue(ref PropertyKey key, ref PropVariant value);
        [PreserveSig] int Commit();
    }

    [ComImport, Guid("0000010b-0000-0000-C000-000000000046"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IPersistFile {
        void GetClassID(out Guid classId);
        [PreserveSig] int IsDirty();
        void Load([MarshalAs(UnmanagedType.LPWStr)] string fileName, uint mode);
        void Save([MarshalAs(UnmanagedType.LPWStr)] string fileName, [MarshalAs(UnmanagedType.Bool)] bool remember);
        void SaveCompleted([MarshalAs(UnmanagedType.LPWStr)] string fileName);
        void GetCurFile([MarshalAs(UnmanagedType.LPWStr)] out string fileName);
    }

    [ComImport, Guid("00021401-0000-0000-C000-000000000046")]
    class ShellLink { }

    [DllImport("ole32.dll")]
    static extern int PropVariantClear(ref PropVariant value);

    const ushort VT_LPWSTR = 31;
    const uint STGM_READWRITE = 2;

    static PropertyKey AppIdKey() {
        PropertyKey key;
        key.FormatId = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3");
        key.PropertyId = 5;
        return key;
    }

    public static void Set(string path, string appId) {
        object link = new ShellLink();
        try {
            ((IPersistFile)link).Load(path, STGM_READWRITE);
            IPropertyStore store = (IPropertyStore)link;
            PropertyKey key = AppIdKey();
            PropVariant value = new PropVariant();
            value.VarType = VT_LPWSTR;
            value.Pointer = Marshal.StringToCoTaskMemUni(appId);
            try {
                Marshal.ThrowExceptionForHR(store.SetValue(ref key, ref value));
                Marshal.ThrowExceptionForHR(store.Commit());
            } finally {
                Marshal.FreeCoTaskMem(value.Pointer);
            }
            ((IPersistFile)link).Save(path, true);
        } finally {
            Marshal.ReleaseComObject(link);
        }
    }

    public static string Get(string path) {
        object link = new ShellLink();
        try {
            ((IPersistFile)link).Load(path, 0);
            PropertyKey key = AppIdKey();
            PropVariant value;
            Marshal.ThrowExceptionForHR(((IPropertyStore)link).GetValue(ref key, out value));
            string result = value.VarType == VT_LPWSTR ? Marshal.PtrToStringUni(value.Pointer) : null;
            PropVariantClear(ref value);
            return result;
        } finally {
            Marshal.ReleaseComObject(link);
        }
    }
}
'@
[ShortcutAppId]::Set($shortcutPath, $appUserModelId)
$grabado = [ShortcutAppId]::Get($shortcutPath)
if ($grabado -ne $appUserModelId) {
    throw "No se pudo grabar el AppUserModelID en el acceso directo (leído: '$grabado')."
}

Write-Host "Acceso directo creado: $shortcutPath"
Write-Host "  Destino:        $pythonw `"$mainPy`""
Write-Host "  Directorio:     $projectRoot"
Write-Host "  Ícono:          $icon"
Write-Host "  AppUserModelID: $grabado"
