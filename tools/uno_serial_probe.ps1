param(
    [string]$Port = "COM14",
    [int]$Baud = 115200,
    [string]$Command = "W,80,80,80,80",
    [double]$SendRateHz = 20.0,
    [double]$DurationSec = 3.0,
    [double]$ReadyWaitSec = 2.0,
    [double]$TailReadSec = 0.6,
    [switch]$NoSend
)

Add-Type -AssemblyName System

function Write-StampedLine {
    param(
        [string]$Direction,
        [string]$Text
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return
    }

    $stamp = [DateTime]::Now.ToString("HH:mm:ss.fff")
    Write-Output ("[{0}] {1} {2}" -f $stamp, $Direction, $Text.Trim())
}

function Flush-SerialLines {
    param(
        [System.IO.Ports.SerialPort]$SerialPort,
        [ref]$Buffer
    )

    while ($SerialPort.BytesToRead -gt 0) {
        $Buffer.Value += $SerialPort.ReadExisting()
    }

    while ($true) {
        $newlineIndex = $Buffer.Value.IndexOf("`n")
        if ($newlineIndex -lt 0) {
            break
        }

        $line = $Buffer.Value.Substring(0, $newlineIndex).Trim("`r")
        $Buffer.Value = $Buffer.Value.Substring($newlineIndex + 1)
        Write-StampedLine "RX" $line
    }
}

$serial = New-Object System.IO.Ports.SerialPort $Port, $Baud, ([System.IO.Ports.Parity]::None), 8, ([System.IO.Ports.StopBits]::One)
$serial.ReadTimeout = 50
$serial.WriteTimeout = 500
$serial.NewLine = "`n"

$buffer = ""

try {
    $serial.Open()
    Start-Sleep -Milliseconds 150

    $readyDeadline = [DateTime]::Now.AddSeconds($ReadyWaitSec)
    while ([DateTime]::Now -lt $readyDeadline) {
        Flush-SerialLines -SerialPort $serial -Buffer ([ref]$buffer)
        Start-Sleep -Milliseconds 20
    }

    if (-not $NoSend) {
        $intervalMs = [Math]::Max(1, [int][Math]::Round(1000.0 / $SendRateHz))
        $durationMs = [int][Math]::Round($DurationSec * 1000.0)
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $nextSendMs = 0

        while ($stopwatch.ElapsedMilliseconds -lt $durationMs) {
            if ($stopwatch.ElapsedMilliseconds -ge $nextSendMs) {
                $serial.Write($Command + "`n")
                Write-StampedLine "TX" $Command
                $nextSendMs += $intervalMs
            }

            Flush-SerialLines -SerialPort $serial -Buffer ([ref]$buffer)
            Start-Sleep -Milliseconds 5
        }

        $stopCommand = "W,0,0,0,0"
        $serial.Write($stopCommand + "`n")
        Write-StampedLine "TX" $stopCommand
    }

    $tailDeadline = [DateTime]::Now.AddSeconds($TailReadSec)
    while ([DateTime]::Now -lt $tailDeadline) {
        Flush-SerialLines -SerialPort $serial -Buffer ([ref]$buffer)
        Start-Sleep -Milliseconds 20
    }
}
finally {
    if ($serial.IsOpen) {
        $serial.Close()
    }
}
