param(
    [string]$Port = "COM14",
    [int]$Baud = 115200,
    [string[]]$Commands = @(),
    [string]$CommandScript = "",
    [int]$PassiveReadMs = 300,
    [int]$ReadMs = 250,
    [int]$DelayMs = 50,
    [switch]$Interactive,
    [switch]$ResetAfterOpen,
    [string]$StlinkSn = "37FF71064E573436B1631543",
    [string]$ProgrammerCli = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ProgrammerCliPath {
    param(
        [string]$RequestedPath
    )

    if ($RequestedPath -and (Test-Path -LiteralPath $RequestedPath)) {
        return (Resolve-Path -LiteralPath $RequestedPath).Path
    }

    $candidates = @(
        "F:\CodeForge\STM32CubeIDE_2.1.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.400.202601091506\tools\bin\STM32_Programmer_CLI.exe",
        "F:\CodeForge\OpenMV IDE\share\qtcreator\stcubeprogrammer\windows\STM32_Programmer_CLI.exe",
        "C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

function Write-TimedLine {
    param(
        [string]$Prefix,
        [string]$Text
    )

    $timestamp = Get-Date -Format "HH:mm:ss.fff"
    Write-Host ("[{0}] {1}{2}" -f $timestamp, $Prefix, $Text)
}

function Read-SerialWindow {
    param(
        [System.IO.Ports.SerialPort]$SerialPort,
        [int]$DurationMs
    )

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.ElapsedMilliseconds -lt $DurationMs) {
        try {
            $line = $SerialPort.ReadLine().Trim("`r", "`n")
            if ($line.Length -gt 0) {
                Write-TimedLine "" $line
            }
        }
        catch [TimeoutException] {
        }
    }
}

function Invoke-StlinkReset {
    param(
        [string]$CliPath,
        [string]$SerialNumber
    )

    if (-not $CliPath) {
        throw "STM32_Programmer_CLI.exe not found."
    }

    Write-TimedLine "" ("ST-Link reset via {0}" -f $CliPath)
    & $CliPath -c "port=SWD" "freq=50" "sn=$SerialNumber" "mode=HotPlug" "-rst" | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "ST-Link reset failed with exit code $LASTEXITCODE."
    }
}

function Send-CsrCommand {
    param(
        [System.IO.Ports.SerialPort]$SerialPort,
        [string]$Command,
        [int]$WaitMs
    )

    if ([string]::IsNullOrWhiteSpace($Command)) {
        return
    }

    Write-TimedLine "TX " $Command
    $SerialPort.Write("$Command`n")
    Start-Sleep -Milliseconds $DelayMs
    Read-SerialWindow -SerialPort $SerialPort -DurationMs $WaitMs
}

function Show-InteractiveHelp {
    Write-Host "Interactive commands:"
    Write-Host "  M,<ch>,<pwm>   send motor command, example: M,1,300"
    Write-Host "  E,<ch>         query encoder, example: E,1"
    Write-Host "  STOP           stop all channels"
    Write-Host "  :reset         reset board via ST-Link"
    Write-Host "  :read [ms]     passive read, default 500ms"
    Write-Host "  :quit          exit"
}

$resolvedCli = Resolve-ProgrammerCliPath -RequestedPath $ProgrammerCli
$serialPort = New-Object System.IO.Ports.SerialPort $Port, $Baud, ([System.IO.Ports.Parity]::None), 8, ([System.IO.Ports.StopBits]::One)
$serialPort.NewLine = "`n"
$serialPort.ReadTimeout = 120
$serialPort.WriteTimeout = 500
$serialPort.DtrEnable = $false
$serialPort.RtsEnable = $false

try {
    $serialPort.Open()
    Write-TimedLine "" ("Opened {0} @ {1}" -f $Port, $Baud)

    if ($ResetAfterOpen) {
        Invoke-StlinkReset -CliPath $resolvedCli -SerialNumber $StlinkSn
        Start-Sleep -Milliseconds 150
    }

    if ($PassiveReadMs -gt 0) {
        Read-SerialWindow -SerialPort $serialPort -DurationMs $PassiveReadMs
    }

    if ($CommandScript) {
        $scriptCommands = $CommandScript.Split(";", [System.StringSplitOptions]::RemoveEmptyEntries)
        foreach ($item in $scriptCommands) {
            $Commands += $item.Trim()
        }
    }

    if ($Commands.Count -gt 0) {
        foreach ($command in $Commands) {
            Send-CsrCommand -SerialPort $serialPort -Command $command -WaitMs $ReadMs
        }
        return
    }

    if (-not $Interactive) {
        $Interactive = $true
    }

    if ($Interactive) {
        Show-InteractiveHelp
        while ($true) {
            $inputLine = Read-Host "csr"
            if ($null -eq $inputLine) {
                continue
            }

            $trimmed = $inputLine.Trim()
            if ($trimmed.Length -eq 0) {
                continue
            }

            if ($trimmed -eq ":quit" -or $trimmed -eq ":q" -or $trimmed -eq ":exit") {
                break
            }

            if ($trimmed -eq ":help") {
                Show-InteractiveHelp
                continue
            }

            if ($trimmed -eq ":reset") {
                Invoke-StlinkReset -CliPath $resolvedCli -SerialNumber $StlinkSn
                Start-Sleep -Milliseconds 150
                Read-SerialWindow -SerialPort $serialPort -DurationMs $ReadMs
                continue
            }

            if ($trimmed.StartsWith(":read")) {
                $parts = $trimmed.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
                $duration = 500
                if ($parts.Length -ge 2) {
                    [void][int]::TryParse($parts[1], [ref]$duration)
                }
                Read-SerialWindow -SerialPort $serialPort -DurationMs $duration
                continue
            }

            Send-CsrCommand -SerialPort $serialPort -Command $trimmed -WaitMs $ReadMs
        }
    }
}
finally {
    if ($serialPort.IsOpen) {
        $serialPort.Close()
    }
}
