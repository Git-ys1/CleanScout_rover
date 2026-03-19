#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "cj_bridge.h"
#include "cj_ring_buffer.h"
#include "cj_bridge_protocol.h"

#define UART_RX_BUFFER_SIZE 128U
#define UNO_LINE_BUFFER_SIZE 32U

static uint8_t uno_rx_storage[UART_RX_BUFFER_SIZE];
static uint8_t j_rx_storage[UART_RX_BUFFER_SIZE];
static cj_ring_buffer_t uno_rx_buffer;
static cj_ring_buffer_t j_rx_buffer;
static cj_bridge_t bridge;
static cj_parser_t j_parser;
static char uno_line_buffer[UNO_LINE_BUFFER_SIZE];
static uint8_t uno_line_length = 0U;

static uint32_t platform_millis(void);
static void platform_send_uno_line(const char *line);
static void platform_send_j_bytes(const uint8_t *bytes, uint8_t length);
static void platform_log(const char *message);
static void platform_init_clock(void);
static void platform_init_led(void);
static void platform_init_uart_uno(void);
static void platform_init_uart_j(void);
static void platform_toggle_led(void);
static void process_uno_bytes(void);
static void process_j_bytes(void);

void usart2_rx_isr(uint8_t byte) {
  (void)cj_ring_buffer_push(&uno_rx_buffer, byte);
}

void usart1_rx_isr(uint8_t byte) {
  (void)cj_ring_buffer_push(&j_rx_buffer, byte);
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
 * 下面这些 platform_* 函数故意只保留最小桩。
 * 在真正的 STM32CubeIDE 工程里，应替换为：
 * - SysTick/HAL_GetTick 或手写 timer tick
 * - USART1/USART2 初始化
 * - 中断驱动的 RX IRQ 推送
 * - 非阻塞 TX 发送
 * - LED 心跳 GPIO
 */
static uint32_t platform_millis(void) {
  return 0U;
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
}

static void platform_init_led(void) {
}

static void platform_init_uart_uno(void) {
}

static void platform_init_uart_j(void) {
}

static void platform_toggle_led(void) {
}