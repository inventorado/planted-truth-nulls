# prereg_amend_3 battery (after the amendment is frozen): gate-critical runs first. Run from the programme root:
#   powershell -NoProfile -File arcs\audit\src\run_a3_battery.ps1
# Re-running skips finished outputs (paths built in invariant culture; sk-SK would write 0.5 as "0,5").
$py = "env\venv\Scripts\python.exe"
$inv = [cultureinfo]::InvariantCulture
if (-not (Test-Path "artifacts\plants\a3species_dk_C-gene_m25_a0.9.csv.gz")) {
    & $py -X utf8 arcs\audit\src\e3_species_replay.py all 2>&1 | Select-String -NotMatch "Warning|warn"
}
$runs = @()  # F-align / F-align-pc: one run writes both paired w files (.5 and .9)
foreach ($c in "aal", "dk", "cc200") { foreach ($t in "wmod", "grad", "mod", "brain") { $runs += ,@($c, "F-align", $t, "both", 1000) } }
foreach ($t in "mod", "grad", "brain") { $runs += ,@("dk-ctx", "F-align", $t, "both", 1000) }
foreach ($c in "aal", "dk") { foreach ($a in 0.3, 0.5, 0.7) { $runs += ,@($c, "C-align", "wmod", $a, 500) } }
foreach ($c in "aal", "dk", "cc200") { foreach ($t in "pc1", "pc2") { $runs += ,@($c, "F-align-pc", $t, "both", 200) } }
foreach ($r in $runs) {
    $was = if ($r[3] -eq "both") { @(0.5, 0.9) } else { @($r[3]) }
    $outs = $was | ForEach-Object { [string]::Format($inv, "artifacts\plants_a3\{0}_{1}_{2}_{3}.csv.gz", $r[0], $r[1], $r[2], $_) }
    if (($outs | Where-Object { -not (Test-Path $_) }).Count -eq 0) { "skip $($outs -join ', ')"; continue }
    & $py -X utf8 arcs\audit\src\e3_align_plants.py $r[0] $r[1] $r[2] ([string]::Format($inv, "{0}", $r[3])) $r[4] 2>&1 | Select-String -NotMatch "Warning|warn"
}
"A3 BATTERY DONE $(Get-Date -Format s)"
