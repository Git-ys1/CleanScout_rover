$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$user = Join-Path $root 'User'
$project = Join-Path $root 'CleanScout_Combined.uvprojx'

function Assert-Count([string]$Pattern, [int]$Expected, [string]$Label) {
    $matches = @(rg -n --glob '*.c' $Pattern $user)
    if ($matches.Count -ne $Expected) {
        $matches | ForEach-Object { Write-Host $_ }
        throw "$Label count must be $Expected; actual=$($matches.Count)"
    }
}

Assert-Count '^int main\(void\)' 1 'main()'
Assert-Count '^void SysTick_Handler\(void\)' 1 'SysTick_Handler'
Assert-Count '^void USART2_IRQHandler\(void\)' 1 'USART2_IRQHandler'
Assert-Count '^void USART3_IRQHandler\(void\)' 1 'USART3_IRQHandler'
Assert-Count '^void UART5_IRQHandler\(void\)' 1 'UART5_IRQHandler'

$projectText = Get-Content -LiteralPath $project -Raw
foreach ($forbidden in @('y_usart.c', 'y_servo.c', 'TIM7', 'mechanical_arm_controller')) {
    if ($projectText -match [regex]::Escape($forbidden)) { throw "Keil target contains forbidden resource: $forbidden" }
}

$sharedState = @(rg -n 'uart_receive_buf|\bbuf_index\b|\buart_mode\b' $user)
if ($sharedState.Count -ne 0) {
    $sharedState | ForEach-Object { Write-Host $_ }
    throw 'Found legacy shared UART receive state.'
}

$motionSource = Get-Content -LiteralPath (Join-Path $user 'csr_motion_link.c') -Raw
$armSource = Get-Content -LiteralPath (Join-Path $user 'arm_host_link.c') -Raw
if ($motionSource -match '@READY|#000P|PDST|PRAD') { throw 'USART2 motion link contains arm output.' }
if ($armSource -match 'CSR_RF1_READY|NAVDBG|VEL,|PWM,|ACK:W') { throw 'USART3 arm link contains motion output.' }

$irqBlocks = @(rg -n -g '*.c' 'strtok|strtod|sprintf|arm_protocol_parse|csr_motion_parse_line' $user)

# Parsing is allowed in main-loop modules; IRQ handlers only move ring bytes.
$irqSources = @(
    Join-Path $user 'csr_motion_link.c'
    Join-Path $user 'arm_host_link.c'
    Join-Path $user 'arm_servo_bus.c'
)
foreach ($source in $irqSources) {
    $text = Get-Content -LiteralPath $source -Raw
    if ($text -match 'while \(USART_GetFlagStatus') { throw "Found blocking USART polling: $source" }
}

Write-Host 'STATIC_AUDIT=PASS'
exit 0
