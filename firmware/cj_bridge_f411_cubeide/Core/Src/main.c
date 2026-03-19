#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "cj_bridge.h"
#include "cj_ring_buffer.h"
#include "cj_bridge_protocol.h"

#define UART_RX_BUFFER_SIZE 128U
#define UNO_LINE_BUFFER_SIZE 32U
#define CPU_CLOCK_HZ 16000000UL
#define SYSTICK_RELOAD_1MS ((CPU_CLOCK_HZ / 1000UL) - 1UL)
#define HEARTBEAT_ON_MS 100UL
#define HEARTBEAT_OFF_MS 900UL

#define RCC_BASE_ADDR 0x40023800UL
#define RCC_AHB1ENR (*(volatile uint32_t *)(RCC_BASE_ADDR + 0x30UL))

#define GPIOB_BASE_ADDR 0x40020400UL
#define GPIOB_MODER (*(volatile uint32_t *)(GPIOB_BASE_ADDR + 0x00UL))
#define GPIOB_OTYPER (*(volatile uint32_t *)(GPIOB_BASE_ADDR + 0x04UL))
#define GPIOB_OSPEEDR (*(volatile uint32_t *)(GPIOB_BASE_ADDR + 0x08UL))
#define GPIOB_PUPDR (*(volatile uint32_t *)(GPIOB_BASE_ADDR + 0x0CUL))
#define GPIOB_BSRR (*(volatile uint32_t *)(GPIOB_BASE_ADDR + 0x18UL))

#define SYST_CSR (*(volatile uint32_t *)0xE000E010UL)
#define SYST_RVR (*(volatile uint32_t *)0xE000E014UL)
#define SYST_CVR (*(volatile uint32_t *)0xE000E018UL)

#define RCC_AHB1ENR_GPIOBEN (1UL << 1U)
#define SYST_CSR_ENABLE (1UL << 0U)
#define SYST_CSR_TICKINT (1UL << 1U)
#define SYST_CSR_CLKSOURCE (1UL << 2U)
#define LED_PIN 2U

static uint8_t uno_rx_storage[UART_RX_BUFFER_SIZE];
static uint8_t j_rx_storage[UART_RX_BUFFER_SIZE];
static cj_ring_buffer_t uno_rx_buffer;
static cj_ring_buffer_t j_rx_buffer;
static cj_bridge_t bridge;
static cj_parser_t j_parser;
static char uno_line_buffer[UNO_LINE_BUFFER_SIZE];
static uint8_t uno_line_length = 0U;
static volatile uint32_t g_ms_ticks = 0U;
static uint32_t next_led_transition_ms = 0U;
static bool heartbeat_sink_active = false;

static uint32_t platform_millis(void);
static void platform_send_uno_line(const char *line);
static void platform_send_j_bytes(const uint8_t *bytes, uint8_t length);
static void platform_log(const char *message);
static void platform_init_clock(void);
static void platform_init_led(void);
static void platform_init_uart_uno(void);
static void platform_init_uart_j(void);
static void platform_toggle_led(void);
static void platform_set_led_sink(bool enabled);
static void process_uno_bytes(void);
static void process_j_bytes(void);

void usart2_rx_isr(uint8_t byte) {
  (void)cj_ring_buffer_push(&uno_rx_buffer, byte);
}

void usart1_rx_isr(uint8_t byte) {
  (void)cj_ring_buffer_push(&j_rx_buffer, byte);
}

void SysTick_Handler(void) {
  g_ms_ticks++;
}

int main(void) {
  cj_bridge_io_t io = {
    .millis = platform_millis,
    .send_uno_line = platform_send_uno_line,
    .send_j_bytes = platform_send_j_bytes,
    .log = platform_log,
  };

  platform_init_clock();
  platform_init_led();
  platform_init_uart_uno();
  platform_init_uart_j();

  cj_ring_buffer_init(&uno_rx_buffer, uno_rx_storage, sizeof(uno_rx_storage));
  cj_ring_buffer_init(&j_rx_buffer, j_rx_storage, sizeof(j_rx_storage));
  cj_protocol_parser_init(&j_parser);
  cj_bridge_init(&bridge, &io);

  while (true) {
    process_uno_bytes();
    process_j_bytes();
    cj_bridge_tick(&bridge);
    platform_toggle_led();
  }
}

static void process_uno_bytes(void) {
  uint8_t byte = 0U;
  while (cj_ring_buffer_pop(&uno_rx_buffer, &byte)) {
    if (byte == '\r') {
      continue;
    }

    if (byte == '\n') {
      if (uno_line_length > 0U) {
        uno_line_buffer[uno_line_length] = '\0';
        cj_bridge_on_uno_line(&bridge, uno_line_buffer);
        uno_line_length = 0U;
      }
      continue;
    }

    if (uno_line_length < (UNO_LINE_BUFFER_SIZE - 1U)) {
      uno_line_buffer[uno_line_length++] = (char)byte;
    } else {
      uno_line_length = 0U;
    }
  }
}

static void process_j_bytes(void) {
  uint8_t byte = 0U;
  cj_frame_t frame;

  while (cj_ring_buffer_pop(&j_rx_buffer, &byte)) {
    if (cj_protocol_parser_push(&j_parser, byte, &frame)) {
      cj_bridge_on_j_frame(&bridge, &frame);
    }
  }
}

/*
 * 下面这些 platform_* 函数当前只补到了最小 Gate0 级别：
 * - SysTick 毫秒时基
 * - PB2 心跳灯（外接 LED 阴极 -> PB2，主动下拉点亮）
 * - USART1/USART2 初始化
 * - 中断驱动的 RX IRQ 推送
 * - 非阻塞 TX 发送
 *
 * 也就是说：本文件现在能验证“板子活着 + 心跳能跑”，
 * 但 UART 发送接收仍然是桩，真正的桥接闭环还没上板打通。
 */
static uint32_t platform_millis(void) {
  return g_ms_ticks;
}

static void platform_send_uno_line(const char *line) {
  (void)line;
}

static void platform_send_j_bytes(const uint8_t *bytes, uint8_t length) {
  (void)bytes;
  (void)length;
}

static void platform_log(const char *message) {
  (void)message;
}

static void platform_init_clock(void) {
  SYST_RVR = SYSTICK_RELOAD_1MS;
  SYST_CVR = 0UL;
  SYST_CSR = SYST_CSR_CLKSOURCE | SYST_CSR_TICKINT | SYST_CSR_ENABLE;
}

static void platform_init_led(void) {
  RCC_AHB1ENR |= RCC_AHB1ENR_GPIOBEN;

  GPIOB_MODER &= ~(0x3UL << (LED_PIN * 2U));
  GPIOB_MODER |= (0x1UL << (LED_PIN * 2U));
  GPIOB_OTYPER &= ~(1UL << LED_PIN);
  GPIOB_OSPEEDR &= ~(0x3UL << (LED_PIN * 2U));
  GPIOB_PUPDR &= ~(0x3UL << (LED_PIN * 2U));

  heartbeat_sink_active = false;
  next_led_transition_ms = 0U;
  platform_set_led_sink(false);
}

static void platform_init_uart_uno(void) {
}

static void platform_init_uart_j(void) {
}

static void platform_toggle_led(void) {
  uint32_t now = platform_millis();
  if (now < next_led_transition_ms) {
    return;
  }

  heartbeat_sink_active = !heartbeat_sink_active;
  platform_set_led_sink(heartbeat_sink_active);
  next_led_transition_ms = now + (heartbeat_sink_active ? HEARTBEAT_ON_MS : HEARTBEAT_OFF_MS);
}

static void platform_set_led_sink(bool enabled) {
  if (enabled) {
    GPIOB_BSRR = (1UL << (LED_PIN + 16U));
    return;
  }

  GPIOB_BSRR = (1UL << LED_PIN);
}
