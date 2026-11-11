# ASDG-AUD-E3-plants: the full synthetic battery of prereg §6.2-6.3, gate-critical cells first.
# Run from the programme root: powershell -File arcs\audit\src\run_e3_battery.ps1
$py = "env\venv\Scripts\python.exe"
$cells = @()
foreach ($atlas in "aal", "dk", "cc200") { foreach ($fam in "F-sp", "F-mod", "F-traj") { $cells += ,@($atlas, $fam, 25, 0, 1000) } }
foreach ($atlas in "aal", "dk") { foreach ($fam in "C-sp", "C-gene") { foreach ($a in 0.3, 0.6, 0.9) { $cells += ,@($atlas, $fam, 25, $a, 300) } } }
foreach ($m in 10, 100) { foreach ($fam in "F-sp", "F-mod", "F-traj") { $cells += ,@("aal", $fam, $m, 0, 300) } }
foreach ($c in $cells) {
    # invariant culture: under sk-SK, -f would write a = 0.3 as "0,3" and the skip test would never match
    $out = [string]::Format([cultureinfo]::InvariantCulture, "artifacts\plants\{0}_{1}_m{2}_a{3}.csv.gz", $c[0], $c[1], $c[2], $c[3])
    if ((Test-Path $out) -and ((Get-Date) - (Get-Item $out).LastWriteTime).TotalHours -lt 24) {
        $n = (& $py -c "import pandas as pd;print(len(pd.read_csv(r'$out')))")
        if ([int]$n -eq $c[4]) { "skip $out (n=$n)"; continue }
    }
    & $py -X utf8 arcs\audit\src\e3_plants.py $c[0] $c[1] $c[2] $c[3] $c[4] 22 2>&1 | Select-String -NotMatch "Warning|warn"
}
"BATTERY DONE $(Get-Date -Format s)"
