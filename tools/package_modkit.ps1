<#
.SYNOPSIS
    Assembles and zips the PropHunt Mod Kit that map creators download to build and
    publish custom Workshop maps.

.DESCRIPTION
    Produces a trimmed copy of the UE project containing everything a creator needs:
      - the project + source so the editor opens,
      - the base-game release version (Releases\<ver>\Win64) for DLC cooking,
      - the PropHuntModKit plugin (the in-editor Publish tool),
      - the publish script and creator guide.
    It excludes transient/dev folders, the throwaway test plugin, and (IMPORTANT) any
    paid/proprietary Content packs you are not licensed to redistribute.

.NOTES
    Re-run this whenever you ship a new Mod Kit. Bump -ReleaseVersion when the base game's
    cooked content changes (and regenerate the release version first - see -GenerateRelease).

.EXAMPLE
    pwsh -File tools\package_modkit.ps1
    pwsh -File tools\package_modkit.ps1 -ReleaseVersion 1.1 -GenerateRelease
#>
[CmdletBinding()]
param(
    [string]$ProjectDir     = "$PSScriptRoot\..\prophunt",
    [string]$OutDir         = "$PSScriptRoot\..\dist",
    [string]$EngineDir      = "F:\Unreal\UE_5.7",
    [string]$ReleaseVersion = "1.0",
    [string]$AppId          = "4133940",

    # Keep the prebuilt editor binaries so creators can open the project WITHOUT a C++
    # compiler. Set to $false for a smaller, source-only kit (creators must build).
    [bool]$IncludeEditorBinaries = $true,

    # Minimal/protected kit: exclude the game C++ Source, game Binaries, and game Content so
    # creators get a BARE project (template generator + publish plugin + release version) and
    # CANNOT see your Blueprints or source. The staged .uproject is made content-only so it
    # opens without the game module. Creators build maps with engine/free assets and cannot
    # run the game in-editor. REQUIRES a test pass - see the warning the script prints.
    [switch]$Minimal,

    # Run UAT to (re)generate the base-game release version before packaging.
    [switch]$GenerateRelease,

    # Stop with an error if the release version folder is missing (default). Pass
    # -AllowMissingRelease to package anyway (the kit will not be able to cook DLC).
    [switch]$AllowMissingRelease,

    [switch]$SkipZip
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

# !! REVIEW BEFORE SHARING !!
# Paid / proprietary Content packs to EXCLUDE from the creator kit. Redistributing
# Marketplace/Fab content to third parties usually violates its license. Verify EACH
# folder's license. Pre-filled with the packs that look paid; edit to match your licenses.
# (FREE_Interiors, FREE_Interiors_2, Furniture_Free look free - confirm and add here if not.)
$ExcludeContentDirs = @(
    'Fantastic_Dungeon_Pack',
    'Fantastic_Village_Pack',
    'IndustryPropsPack6',
    'LowPolyMarket',
    'Low_Poly_Sci-Fi_Corridor',
    'Realistic_Starter_VFX_Pack_Vol2',
    'RPGEffects',
    'sA_Megapack_v1',
    'Stylized_Egypt'
)

# Plugins to EXCLUDE from the kit. PropHuntModKit is intentionally KEPT (it is the Publish
# tool creators need). PipelineTest was a throwaway pipeline test.
$ExcludePlugins = @('PipelineTest')

# Folders excluded by name anywhere in the tree (transient/dev artifacts).
$ExcludeDirNames = @('Intermediate', 'Saved', 'DerivedDataCache', 'DDC', '.git', '.vs', '.idea')
if (-not $IncludeEditorBinaries) { $ExcludeDirNames += 'Binaries' }

# -Minimal mode only: Content subfolders to KEEP for creators to build with (e.g. free,
# redistributable building assets). EVERYTHING else under Content\ is excluded so your
# Blueprints/maps never ship. Leave empty for a bare kit (engine shapes only).
$MinimalKeepContentDirs = @()

# ---------------------------------------------------------------------------
# RESOLVE PATHS
# ---------------------------------------------------------------------------
$ProjectDir = (Resolve-Path $ProjectDir).Path
$UProject   = Join-Path $ProjectDir 'prophunt.uproject'
if (-not (Test-Path $UProject)) { throw "Cannot find prophunt.uproject under '$ProjectDir'." }

$KitName  = "PropHunt-ModKit-$ReleaseVersion"
$Staging  = Join-Path $OutDir $KitName
$ZipPath  = Join-Path $OutDir "$KitName.zip"
# UE 5 names the release-version platform folder "Windows"; older flows used "Win64".
$ReleaseRoot = Join-Path $ProjectDir "Releases\$ReleaseVersion"
$ReleaseDir  = @("$ReleaseRoot\Windows", "$ReleaseRoot\Win64") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $ReleaseDir) { $ReleaseDir = "$ReleaseRoot\Windows" }  # default for the not-found message

Write-Host "PropHunt Mod Kit packager" -ForegroundColor Cyan
Write-Host "  Project : $ProjectDir"
Write-Host "  Output  : $Staging"
Write-Host "  Release : $ReleaseVersion ($ReleaseDir)"
Write-Host ""

# ---------------------------------------------------------------------------
# 0. (Optional) generate the base-game release version
# ---------------------------------------------------------------------------
if ($GenerateRelease) {
    $RunUAT = Join-Path $EngineDir 'Engine\Build\BatchFiles\RunUAT.bat'
    if (-not (Test-Path $RunUAT)) { throw "RunUAT.bat not found at '$RunUAT' (check -EngineDir)." }
    Write-Host "Generating release version $ReleaseVersion (this cooks the base game; can take a while)..." -ForegroundColor Yellow
    & $RunUAT BuildCookRun -project="$UProject" -noP4 -platform=Win64 -clientconfig=Shipping `
        -cook -stage -pak "-createreleaseversion=$ReleaseVersion"
    if ($LASTEXITCODE -ne 0) { throw "RunUAT createreleaseversion failed (exit $LASTEXITCODE)." }
}

# ---------------------------------------------------------------------------
# 1. Validate the release version exists
# ---------------------------------------------------------------------------
if (-not (Test-Path $ReleaseDir)) {
    $msg = @"
Release version not found: $ReleaseDir
The Mod Kit cannot cook DLC maps without it. Generate it first:

  pwsh -File tools\package_modkit.ps1 -ReleaseVersion $ReleaseVersion -GenerateRelease

or run RunUAT BuildCookRun ... -createreleaseversion=$ReleaseVersion manually.
"@
    if ($AllowMissingRelease) { Write-Warning $msg } else { throw $msg }
}

# ---------------------------------------------------------------------------
# 2. Copy the project to staging, excluding transient/paid/test content
# ---------------------------------------------------------------------------
if (Test-Path $Staging) { Remove-Item $Staging -Recurse -Force }
New-Item -ItemType Directory -Path $Staging -Force | Out-Null

# Build robocopy /XD exclude list: names (any level) + absolute paths for specific dirs.
$xd = @()
$xd += $ExcludeDirNames
foreach ($c in $ExcludeContentDirs) { $xd += (Join-Path $ProjectDir "Content\$c") }
foreach ($p in $ExcludePlugins)     { $xd += (Join-Path $ProjectDir "Plugins\$p") }

# Minimal/protected kit: strip the game C++ Source, the game Binaries, and all game Content
# (except an optional keep-list). The PropHuntModKit plugin (publish tool) is kept whole.
if ($Minimal) {
    $keepLabel = if ($MinimalKeepContentDirs) { $MinimalKeepContentDirs -join ', ' } else { 'nothing - engine shapes only' }
    Write-Host "MINIMAL mode: excluding game Source, Binaries, and Content (keeping Content: $keepLabel)." -ForegroundColor Magenta
    $xd += (Join-Path $ProjectDir 'Source')
    $xd += (Join-Path $ProjectDir 'Binaries')
    $contentRoot = Join-Path $ProjectDir 'Content'
    if (Test-Path $contentRoot) {
        Get-ChildItem -Directory $contentRoot | ForEach-Object {
            if ($MinimalKeepContentDirs -notcontains $_.Name) { $xd += $_.FullName }
        }
    }
}

# Files excluded everywhere: VS solution + debug symbols (creators never need .pdb; the
# prebuilt .dll is what lets the plugin load without compiling).
$xf = @('*.sln', '*.pdb')
if ($Minimal) {
    # Ship only the release-version asset registry (Metadata\*.bin + AssetRegistry.bin), NOT
    # the multi-GB cooked base-game pak. DLC cooking reads the registry to know which assets
    # already live in the base game; it never reads the pak. Dropping it also means the kit
    # carries no cooked copy of your game content.
    $xf += @('*.pak', '*.ucas', '*.utoc')
}

# /MIR mirrors the tree; /XD excludes dirs; /XF excludes files; /NFL /NDL quiet file lists.
$roboArgs = @($ProjectDir, $Staging, '/MIR', '/R:1', '/W:1', '/NFL', '/NDL', '/NP')
$roboArgs += '/XF'
$roboArgs += $xf
$roboArgs += '/XD'
$roboArgs += $xd

Write-Host "Copying project (excluding transient, test, and paid content)..." -ForegroundColor Yellow
& robocopy @roboArgs | Out-Null
# robocopy exit codes < 8 are success (1=files copied, etc.)
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE." }

# ---------------------------------------------------------------------------
# 3. Fix up the staged .uproject (remove excluded plugins, ensure ModKit enabled)
# ---------------------------------------------------------------------------
$StagedUProject = Join-Path $Staging 'prophunt.uproject'
$proj = Get-Content $StagedUProject -Raw | ConvertFrom-Json
$proj.Plugins = @($proj.Plugins | Where-Object { $ExcludePlugins -notcontains $_.Name })
$modkit = $proj.Plugins | Where-Object { $_.Name -eq 'PropHuntModKit' }
if ($modkit) { $modkit.Enabled = $true } # creators need the publish tool

# Minimal mode: make the project content-only so it opens WITHOUT the game C++ module
# (whose Source we stripped). The PropHuntModKit plugin still provides the publish tool via
# its own (prebuilt) binaries.
if ($Minimal -and ($proj.PSObject.Properties.Name -contains 'Modules')) {
    $proj.PSObject.Properties.Remove('Modules')
    Write-Host "Minimal: removed game C++ Modules from staged .uproject (content-only)." -ForegroundColor Magenta
}
($proj | ConvertTo-Json -Depth 20) | Set-Content $StagedUProject -Encoding UTF8
Write-Host "Adjusted staged .uproject (removed: $($ExcludePlugins -join ', '); ModKit enabled)."

# ---------------------------------------------------------------------------
# 4. Drop in creator-facing helpers
# ---------------------------------------------------------------------------
# steam_appid.txt for convenience (note: it must sit next to the EDITOR exe to take effect).
Set-Content -Path (Join-Path $Staging 'steam_appid.txt') -Value $AppId -Encoding ascii

# Creator guide: prefer the maintained docs copy.
$guideSrc = Join-Path $ProjectDir '..\docs\workshop\README.md'
if (Test-Path $guideSrc) {
    Copy-Item $guideSrc (Join-Path $Staging 'CREATOR_GUIDE.md') -Force
}

# ---------------------------------------------------------------------------
# 5. Zip it
# ---------------------------------------------------------------------------
if (-not $SkipZip) {
    if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
    Write-Host "Compressing -> $ZipPath ..." -ForegroundColor Yellow
    Compress-Archive -Path (Join-Path $Staging '*') -DestinationPath $ZipPath -CompressionLevel Optimal
    $sizeMB = [Math]::Round((Get-Item $ZipPath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Mod Kit zip ready: $ZipPath ($sizeMB MB)" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Staging folder ready (zip skipped): $Staging" -ForegroundColor Green
}

Write-Host ""
Write-Host "REMINDER: verify the excluded paid-content list above before sharing the kit." -ForegroundColor Yellow
if ($Minimal) {
    Write-Host ""
    Write-Host "MINIMAL KIT - TEST BEFORE DISTRIBUTING:" -ForegroundColor Yellow
    Write-Host "  1. Open the staged project in a CLEAN UE $($EngineDir.Split('_')[-1]) install." -ForegroundColor Yellow
    Write-Host "     It must open without prompting to rebuild C++ (PropHuntModKit must load from" -ForegroundColor Yellow
    Write-Host "     its prebuilt binaries). If it prompts to rebuild, ship matching plugin binaries." -ForegroundColor Yellow
    Write-Host "  2. Run create_map_template.py, save a test level, then run publish_test_item.py." -ForegroundColor Yellow
    Write-Host "  3. Confirm the DLC cook succeeds against Releases\\$ReleaseVersion." -ForegroundColor Yellow
}
