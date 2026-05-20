param(
    [string]$Port = "COM14",
    [int]$Baud = 115200,
    [double]$WheelA = 0.05,
    [double]$WheelB = 0.05,
    [double]$WheelC = 0.05,
    [double]$WheelD = 0.05,
    [int]$SendHz = 20,
    [int]$SendMs = 2000,
    [int]$PassiveReadMs = 500,
    [int]$PostReadMs = 1000
)

function Read-SerialFor {
    param(
        [System.IO.Ports.SerialPort]$SerialPort,
        [int]$DurationMs
    )

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.ElapsedMilliseconds -lt $DurationMs) {
        try {
            $line = $SerialPort.ReadLine().Trim("`r", "`n")
            if ($line) {
                $timestamp = Get-Date -Format "HH:mm:ss.fff"
                Write-Host "[$timestamp] $line"
            }
        } catch [TimeoutException] {
        }
    }
}

$frame = ("W,{0:F3},{1:F3},{2:F3},{3:F3}" -f $WheelA, $WheelB, $WheelC, $WheelD)
$intervalMs = [Math]::Max([int](1000 / [Math]::Max($SendHz, 1)), 1)

$portObj = New-Object System.IO.Ports.SerialPort $Port, $Baud, 'None', 8, 'One'
$portObj.NewLine = "`n"
$portObj.ReadTimeout = 200
$portObj.WriteTimeout = 500
$portObj.DtrEnable = $false
$portObj.RtsEnable = $false

try {
    $portObj.Open()
    Start-Sleep -Milliseconds 200

    Write-Host "=== Passive read on $Port @ $Baud ==="
    Read-SerialFor -SerialPort $portObj -DurationMs $PassiveReadMs

    Write-Host "=== Active send: $frame ==="
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $nextSend = 0
    while ($sw.ElapsedMilliseconds -lt $SendMs) {
        if ($sw.ElapsedMilliseconds -ge $nextSend) {
            $timestamp = Get-Date -Format "HH:mm:ss.fff"
            Write-Host "[$timestamp] TX $frame"
            $portObj.Write("$frame`n")
            $nextSend += $intervalMs
        }

        try {
            $line = $portObj.ReadLine().Trim("`r", "`n")
            if ($line) {
                $timestamp = Get-Date -Format "HH:mm:ss.fff"
                Write-Host "[$timestamp] $line"
            }
        } catch [TimeoutException] {
        }
    }

    Write-Host "=== Post read ==="
    Read-SerialFor -SerialPort $portObj -DurationMs $PostReadMs
}
finally {
    if ($portObj.IsOpen) {
        $portObj.Close()
    }
}
