param(
    [string]$ProjectRoot,
    [string]$VenvName = "venv",
    [string]$RequirementsFile = "requirements.txt",
    [string]$ProjectName = "diario_viajes",
    [string]$AppName = "FlyNote",
    [string]$AdminUsername,
    [switch]$SkipUpdateCheck,
    [switch]$CreateAdmin,
    [switch]$SkipRunServer
)

$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -ErrorAction Stop

function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
}

function Ensure-LocalCodeSignature {
    $scriptPath = $PSCommandPath
    if (-not $scriptPath) {
        return
    }

    $certSubject = "CN=Local PowerShell Auto Script Signer"
    $cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert -ErrorAction SilentlyContinue |
        Where-Object { $_.Subject -eq $certSubject } |
        Select-Object -First 1

    if (-not $cert) {
        $cert = New-SelfSignedCertificate `
            -CertStoreLocation "Cert:\CurrentUser\My" `
            -Type CodeSigningCert `
            -Subject $certSubject `
            -FriendlyName "LocalPowerShellSigner" `
            -KeyUsage DigitalSignature `
            -KeySpec Signature
    }

    if ($cert) {
        try {
            Set-AuthenticodeSignature -FilePath $scriptPath -Certificate $cert -ErrorAction Stop
            Write-Host "Firma local aplicada a $scriptPath" -ForegroundColor Green
        } catch {
            Write-Warning "No se pudo firmar localmente el script: $($_.Exception.Message)"
        }
    }
}

function Ensure-Python {
    foreach ($candidate in @("py", "python")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $candidate
        }
    }

    Write-Host "Python no está instalado. Intentando instalarlo con winget..." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Python.Python.3 -e --source winget
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo instalar Python."
        }
        return "py"
    }

    throw "No se encontró Python ni winget para instalarlo."
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $candidateRoots = @(
        $PSScriptRoot,
        (Get-Location).Path,
        (Split-Path -Parent $PSScriptRoot)
    )

    foreach ($candidate in $candidateRoots) {
        if ($candidate -and (Test-Path $candidate)) {
            $candidateProject = Join-Path $candidate "diario_viajes"
            $candidateProjectAlt = Join-Path $candidate "diario_viaje"
            $candidateVenv = Join-Path $candidate "venv"
            $candidateManagePy = Join-Path $candidateProject "manage.py"
            $candidateManagePyAlt = Join-Path $candidateProjectAlt "manage.py"
            if ((Test-Path $candidateManagePy) -or (Test-Path $candidateManagePyAlt) -or (Test-Path $candidateVenv)) {
                $ProjectRoot = $candidate
                break
            }
        }
    }

    if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
        $ProjectRoot = $PSScriptRoot
    }
}

$resolvedRoot = (Resolve-Path $ProjectRoot).Path
$venvPath = Join-Path $resolvedRoot $VenvName
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
$pythonCommand = Ensure-Python

Write-Section "Verificando entorno virtual"
if (-not (Test-Path $venvPath)) {
    Write-Host "No existe el entorno '$VenvName'. Creándolo..." -ForegroundColor Yellow
    & $pythonCommand -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo crear el entorno virtual."
    }
} else {
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    $venvWorks = $false
    if (Test-Path $venvPython) {
        try {
            & $venvPython -c "import sys; print(sys.executable)" 2>$null
            $venvWorks = ($LASTEXITCODE -eq 0)
        } catch {
            $venvWorks = $false
        }
    }

    if (-not $venvWorks) {
        Write-Host "El entorno virtual no es válido o apunta a una ruta antigua. Recreándolo..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvPath
        & $pythonCommand -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo recrear el entorno virtual."
        }
    } else {
        Write-Host "El entorno virtual ya existe y funciona correctamente. Se omite la creación." -ForegroundColor Green
    }
}

if (-not (Test-Path $activateScript)) {
    throw "No se encontró el script de activación: $activateScript"
}

Write-Host "Activando el entorno virtual..."
. $activateScript

$pythonExe = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "No se encontró Python dentro del entorno: $pythonExe"
}

Write-Section "Instalando y actualizando dependencias"
& $pythonExe -m pip install --upgrade pip setuptools wheel
$pipExitCode = $LASTEXITCODE
if ($pipExitCode -ne 0) {
    throw "No se pudo actualizar pip (código de salida $pipExitCode). Ejecuta '$pythonExe -m pip install --upgrade pip setuptools wheel' para ver el error completo."
}

& $pythonExe -m pip install --upgrade "django>=4.2,<5.0"
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo instalar o actualizar Django 4.2 compatible con MariaDB 10.4."
}

$projectPath = $null
foreach ($candidate in @("diario_viajes", "diario_viaje")) {
    $candidatePath = Join-Path $resolvedRoot $candidate
    if (Test-Path $candidatePath) {
        $projectPath = $candidatePath
        $ProjectName = $candidate
        break
    }
}

if (-not $projectPath) {
    Write-Section "Creando proyecto Django"
    Set-Location $resolvedRoot
    & $pythonExe -m django startproject $ProjectName
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo crear el proyecto Django."
    }
    $projectPath = Join-Path $resolvedRoot $ProjectName
}

Set-Location $projectPath
Write-Host "Directorio de trabajo: $projectPath" 

$managePy = Join-Path $projectPath "manage.py"
if (-not (Test-Path $managePy)) {
    throw "No se encontró manage.py en $projectPath."
}

$appPath = Join-Path $projectPath $AppName
if (-not (Test-Path $appPath)) {
    Write-Section "Creando aplicación $AppName"
    & $pythonExe $managePy startapp $AppName
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo crear la app $AppName."
    }
} else {
    Write-Host "La aplicación '$AppName' ya existe. Se omite la creación." -ForegroundColor Green
}

Write-Section "Comprobando dependencias"
$requirementsPath = Join-Path $resolvedRoot $RequirementsFile
if (Test-Path $requirementsPath) {
    Write-Host "Se encontró $RequirementsFile. Instalando dependencias..."
    & $pythonExe -m pip install -r $requirementsPath
    if ($LASTEXITCODE -ne 0) {
        throw "La instalación de dependencias falló."
    }
} else {
    Write-Host "No existe $RequirementsFile en $resolvedRoot. Se omite la instalación desde archivo." -ForegroundColor DarkYellow
}

if (-not $SkipUpdateCheck) {
    Write-Section "Verificando actualizaciones disponibles"
    & $pythonExe -m pip list --outdated --format=columns
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "La comprobación de actualizaciones terminó con código $LASTEXITCODE."
    }
} else {
    Write-Host "Se omitió la comprobación de actualizaciones por parámetro." 
}

Write-Section "Generando migraciones"
& $pythonExe $managePy makemigrations
if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron generar las migraciones."
}

Write-Section "Aplicando migraciones"
& $pythonExe $managePy migrate
if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron aplicar las migraciones."
}

if ($CreateAdmin) {
    Write-Section "Configurando administrador"
    if ([string]::IsNullOrWhiteSpace($AdminUsername)) {
        $AdminUsername = Read-Host "Nombre de usuario del administrador"
    }
    if ([string]::IsNullOrWhiteSpace($AdminUsername)) {
        throw "El nombre de usuario del administrador no puede estar vacío."
    }
    $env:FLYNOTE_ADMIN_USERNAME = $AdminUsername
    try {
        $adminExists = (& $pythonExe $managePy shell -c "import os; from django.contrib.auth import get_user_model; print(get_user_model().objects.filter(username=os.environ['FLYNOTE_ADMIN_USERNAME']).exists())").Trim()
        if ($adminExists -eq "False") {
            Write-Host "No existe '$AdminUsername'. Se abrirá el asistente para crear el superusuario."
            & $pythonExe $managePy createsuperuser --username $AdminUsername
            if ($LASTEXITCODE -ne 0) {
                throw "No se pudo crear el superusuario '$AdminUsername'."
            }
        }

        & $pythonExe $managePy shell -c "import os; from django.contrib.auth import get_user_model; user=get_user_model().objects.get(username=os.environ['FLYNOTE_ADMIN_USERNAME']); user.is_staff=True; user.is_superuser=True; user.save(update_fields=['is_staff', 'is_superuser'])"
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudieron activar los permisos de administrador para '$AdminUsername'."
        }
        Write-Host "'$AdminUsername' tiene permisos de administrador." -ForegroundColor Green
    } finally {
        Remove-Item Env:FLYNOTE_ADMIN_USERNAME -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "Se omitió la configuración del administrador. Usa -CreateAdmin para habilitarla."
}

if (-not $SkipRunServer) {
    Write-Section "Iniciando Django"
    Write-Host "Ejecutando: python manage.py runserver"
    & $pythonExe $managePy runserver
} else {
    Write-Host "Se omitió la ejecución de runserver por parámetro."
}

Ensure-LocalCodeSignature

Write-Host ""
Write-Host "Entorno virtual activo y proyecto listo." -ForegroundColor Green
Write-Host "Ruta del entorno: $venvPath" 
Write-Host "Ruta del proyecto: $projectPath" 

# SIG # Begin signature block
# SIG # End signature block
