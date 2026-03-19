#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "cj_bridge.h"
#include "cj_bridge_protocol.h"
#include "cj_ring_buffer.h"

#define UART_RX_BUFFER_SIZE 128U
#define UNO_LINE_BUFFER_SIZE 32U
#define REASON_BUFFER_LEN 48U
#define CPU_CLOCK_HZ 16000000UL
#define USART_BRR_9600 0x0683U
#define KEEPALIVE_INTERVAL_MS 1000UL
#define HEARTBEAT_SLOT_MS 100U
#define HEARTBEAT_PATTERN_PERIOD_MS 1000UL

#define RCC_BASE_ADDR 0x40023800UL
#define RCC_AHB1ENR (*(volatile uint32_t *)(RCC_BASE_ADDR + 0x30UL))
#define RCC_APB1ENR (*(volatile uint32_t *)(RCC_BASE_ADDR + 0x40UL))
#define RCC_APB2ENR (*(volatile uint32_t *)(RCC_BASE_ADDR + 0x44UL))

#define RCC_AHB1ENR_GPIOAEN (1UL << 0U)
#define RCC_AHB1ENR_GPIOBEN (1UL << 1U)
#define RCC_APB1ENR_USART2EN (1UL << 17U)
#define RCC_APB2ENR_USART1EN (1UL << 4U)

#define GPIOA_BASE_ADDR 0x40020000UL
#define GPIOB_BASE_ADDR 0x40020400UL

typedef struct {
  volatile uint32_t MODER;
  volatile uint32_t OTYPER;
  volatile uint32_t OSPEEDR;
  volatile uint32_t PUPDR;
  volatile uint32_t IDR;
  volatile uint32_t ODR;
  volatile uint32_t BSRR;
  volatile uint32_t LCKR;
  volatile uint32_t AFR[2];
} gpio_registers_t;

#define GPIOA ((gpio_registers_t *)GPIOA_BASE_ADDR)
#define GPIOB ((gpio_registers_t *)GPIOB_BASE_ADDR)

typedef struct {
  volatile uint32_t SR;
  volatile uint32_t DR;
  volatile uint32_t BRR;
  volatile uint32_t CR1;
  volatile uint32_t CR2;
  volatile uint32_t CR3;
  volatile uint32_t GTPR;
} usart_registers_t;

#define USART1_BASE_ADDR 0x40011000UL
#define USART2_BASE_ADDR 0x40004400UL
#define USART1_REGS ((usart_registers_t *)USART1_BASE_ADDR)
#define USART2_REGS ((usart_registers_t *)USART2_BASE_ADDR)

#define USART_SR_ERROR_MASK 0x0FU
#define USART_SR_RXNE (1UL << 5U)
#define USART_SR_TC (1UL << 6U)
#define USART_SR_TXE (1UL << 7U)
#define USART_CR1_RE (1UL << 2U)
#define USART_CR1_TE (1UL << 3U)
#define USART_CR1_RXNEIE (1UL << 5U)
#define USART_CR1_UE (1UL << 13U)

#define USART1_IRQn 37U
#define USART2_IRQn 38U
#define NVIC_ISER1 (*(volatile uint32_t *)0xE000E104UL)

#define SYST_CSR (*(volatile uint32_t *)0xE000E010UL)
#define SYST_RVR (*(volatile uint32_t *)0xE000E014UL)
#define SYST_CVR (*(volatile uint32_t *)0xE000E018UL)
#define SYST_CSR_ENABLE (1UL << 0U)
#define SYST_CSR_TICKINT (1UL << 1U)
#define SYST_CSR_CLKSOURCE (1UL << 2U)
#define SYSTICK_RELOAD_1MS ((CPU_CLOCK_HZ / 1000UL) - 1UL)

#define LED_PIN 2U
#define STATE_IDLE_FLASHES 1U
#define STATE_WAIT_STOP_FLASHES 2U
#define STATE_WAIT_J_FLASHES 3U
#define STATE_WAIT_RESUME_FLASHES 4U

static uint8_t uno_rx_storage[UART_RX_BUFFER_SIZE];
static uint8_t j_rx_storage[UART_RX_BUFFER_SIZE];
static cj_ring_buffer_t uno_rx_buffer;
static cj_ring_buffer_t j_rx_buffer;
static cj_bridge_t bridge;
static cj_parser_t j_parser;
static char uno_line_buffer[UNO_LINE_BUFFER_SIZE];
static uint8_t uno_line_length = 0U;

static volatile uint32_t g_ms_ticks = 0U;
static volatile cj_bridge_state_t diag_bridge_state = CJ_BRIDGE_IDLE;
static volatile uint32_t diag_last_state_transition_ms = 0U;
static volatile uint32_t diag_usart1_rx_count = 0U;
static volatile uint32_t diag_usart2_rx_count = 0U;
static volatile uint32_t diag_usart1_tx_count = 0U;
static volatile uint32_t diag_usart2_tx_count = 0U;
static volatile uint32_t diag_usart1_error_count = 0U;
static volatile uint32_t diag_usart2_error_count = 0U;
static volatile uint32_t diag_uno_pong_count = 0U;
static volatile uint32_t diag_uno_stop_ack_count = 0U;
static volatile uint32_t diag_uno_resume_ack_count = 0U;
static volatile uint32_t diag_uno_ping_sent_count = 0U;
static volatile uint32_t diag_j_ping_sent_count = 0U;
static volatile uint32_t diag_j_heartbeat_count = 0U;
static volatile uint32_t diag_j_ack_count = 0U;
static volatile uint32_t diag_j_frame_count = 0U;
static volatile uint32_t diag_color_found_count = 0U;
static volatile uint32_t diag_pick_window_sent_count = 0U;
static volatile uint32_t diag_pick_done_count = 0U;
static volatile uint32_t diag_pick_timeout_count = 0U;
static volatile uint32_t diag_arm_fail_count = 0U;
static volatile uint32_t diag_early_j_result_count = 0U;
static volatile bool diag_uno_link_confirmed = false;
static volatile bool diag_j_link_confirmed = false;
static volatile char diag_last_log_reason[REASON_BUFFER_LEN];
static volatile char diag_last_fault_reason[REASON_BUFFER_LEN];

static uint32_t last_uno_keepalive_ms = 0U;
static uint32_t last_j_keepalive_ms = 0U;
static cj_bridge_state_t observed_bridge_state = CJ_BRIDGE_FAULT;

static uint32_t platform_millis(void);
static void platform_send_uno_line(const char *line);
static void platform_send_j_bytes(const uint8_t *bytes, uint8_t length);
static void platform_log(const char *message);
static void platform_init_clock(void);
static void platform_init_led(void);
static void platform_init_uart_gpio(void);
static void platform_init_uart_uno(void);
static void platform_init_uart_j(void);
static void platform_toggle_led(void);
static void platform_set_led_sink(bool enabled);
static void platform_service_keepalives(void);
static void platform_observe_bridge_state(void);
static void process_uno_bytes(void);
static void process_j_bytes(void);
static void copy_reason(volatile char *dest, const char *src);
static void usart_send_blocking(usart_registers_t *uart, volatile uint32_t *tx_counter, const uint8_t *buffer, uint32_t length);
static void init_usart(usart_registers_t *uart, uint32_t brr);
static void send_j_ping_frame(void);
static uint8_t state_flash_count(cj_bridge_state_t state);

void usart2_rx_isr(uint8_t byte) {
  (void)cj_ring_buffer_push(&uno_rx_buffer, byte);
}

void usart1_rx_isr(uint8_t byte) {
  (void)cj_ring_buffer_push(&j_rx_buffer, byte);
}

void SysTick_Handler(void) {
  g_ms_ticks++;
}

void USART1_IRQHandler(void) {
  uint32_t status = USART1_REGS->SR;

  if ((status & USART_SR_ERROR_MASK) != 0U) {
    diag_usart1_error_count++;
  }

  if ((status & USART_SR_RXNE) != 0U) {
    uint8_t byte = (uint8_t)(USART1_REGS->DR & 0xFFU);
    diag_usart1_rx_count++;
    usart1_rx_isr(byte);
    return;
  }

  if ((status & USART_SR_ERROR_MASK) != 0U) {
    (void)USART1_REGS->DR;
  }
}

void USART2_IRQHandler(void) {
  uint32_t status = USART2_REGS->SR;

  if ((status & USART_SR_ERROR_MASK) != 0U) {
    diag_usart2_error_count++;
  }

  if ((status & USART_SR_RXNE) != 0U) {
    uint8_t byte = (uint8_t)(USART2_REGS->DR & 0xFFU);
    diag_usart2_rx_count++;
    usart2_rx_isr(byte);
    return;
  }

  if ((status & USART_SR_ERROR_MASK) != 0U) {
    (void)USART2_REGS->DR;
  }
}

int main(void) {
  cj_bridge_io_t io = {
    .millis = platform_millis,
    .send_uno_line = platform_send_uno_line,
    .send_j_bytes = platform_send_j_bytes,
    .log = platform_log,
  };

  copy_reason(diag_last_log_reason, "BOOT");
  copy_reason(diag_last_fault_reason, "NONE");

  platform_init_clock();
  platform_init_led();
  platform_init_uart_gpio();
  platform_init_uart_uno();
  platform_init_uart_j();

  cj_ring_buffer_init(&uno_rx_buffer, uno_rx_storage, sizeof(uno_rx_storage));
  cj_ring_buffer_init(&j_rx_buffer, j_rx_storage, sizeof(j_rx_storage));
  cj_protocol_parser_init(&j_parser);
  cj_bridge_init(&bridge, &io);
  observed_bridge_state = bridge.state;
  diag_bridge_state = bridge.state;
  diag_last_state_transition_ms = platform_millis();

  while (true) {
    process_uno_bytes();
    process_j_bytes();
    cj_bridge_tick(&bridge);
    platform_observe_bridge_state();
    platform_service_keepalives();
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

        if (strcmp(uno_line_buffer, "PONG") == 0) {
          diag_uno_link_confirmed = true;
          diag_uno_pong_count++;
        } else if (strcmp(uno_line_buffer, "STOP_ACK") == 0) {
          diag_uno_link_confirmed = true;
          diag_uno_stop_ack_count++;
        } else if (strcmp(uno_line_buffer, "RESUME_ACK") == 0) {
          diag_uno_link_confirmed = true;
          diag_uno_resume_ack_count++;
        }

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
      diag_j_link_confirmed = true;
      diag_j_frame_count++;

      if (frame.type == CJ_MSG_HEARTBEAT) {
        diag_j_heartbeat_count++;
      } else if (frame.type == CJ_MSG_ACK) {
        diag_j_ack_count++;
      }

      cj_bridge_on_j_frame(&bridge, &frame);
    }
  }
}

static uint32_t platform_millis(void) {
  return g_ms_ticks;
}

static void platform_send_uno_line(const char *line) {
  const uint8_t newline = (uint8_t)'\n';
  usart_send_blocking(USART2_REGS, &diag_usart2_tx_count, (const uint8_t *)line, (uint32_t)strlen(line));
  usart_send_blocking(USART2_REGS, &diag_usart2_tx_count, &newline, 1U);
}

static void platform_send_j_bytes(const uint8_t *bytes, uint8_t length) {
  usart_send_blocking(USART1_REGS, &diag_usart1_tx_count, bytes, length);
}

static void platform_log(const char *message) {
  copy_reason(diag_last_log_reason, message);
  if (strncmp(message, "FAULT:", 6U) == 0) {
    copy_reason(diag_last_fault_reason, message);
  }
}

static void platform_init_clock(void) {
  SYST_RVR = SYSTICK_RELOAD_1MS;
  SYST_CVR = 0UL;
  SYST_CSR = SYST_CSR_CLKSOURCE | SYST_CSR_TICKINT | SYST_CSR_ENABLE;
}

static void platform_init_led(void) {
  RCC_AHB1ENR |= RCC_AHB1ENR_GPIOBEN;

  GPIOB->MODER &= ~(0x3UL << (LED_PIN * 2U));
  GPIOB->MODER |= (0x1UL << (LED_PIN * 2U));
  GPIOB->OTYPER &= ~(1UL << LED_PIN);
  GPIOB->OSPEEDR |= (0x3UL << (LED_PIN * 2U));
  GPIOB->PUPDR &= ~(0x3UL << (LED_PIN * 2U));

  platform_set_led_sink(false);
}

static void platform_init_uart_gpio(void) {
  RCC_AHB1ENR |= RCC_AHB1ENR_GPIOAEN;

  GPIOA->MODER &= ~((0x3UL << (2U * 2U)) |
                    (0x3UL << (3U * 2U)) |
                    (0x3UL << (9U * 2U)) |
                    (0x3UL << (10U * 2U)));
  GPIOA->MODER |= ((0x2UL << (2U * 2U)) |
                   (0x2UL << (3U * 2U)) |
                   (0x2UL << (9U * 2U)) |
                   (0x2UL << (10U * 2U)));

  GPIOA->OTYPER &= ~((1UL << 2U) | (1UL << 3U) | (1UL << 9U) | (1UL << 10U));
  GPIOA->OSPEEDR |= ((0x3UL << (2U * 2U)) |
                     (0x3UL << (3U * 2U)) |
                     (0x3UL << (9U * 2U)) |
                     (0x3UL << (10U * 2U)));

  GPIOA->PUPDR &= ~((0x3UL << (2U * 2U)) |
                    (0x3UL << (3U * 2U)) |
                    (0x3UL << (9U * 2U)) |
                    (0x3UL << (10U * 2U)));
  GPIOA->PUPDR |= ((0x1UL << (3U * 2U)) |
                   (0x1UL << (10U * 2U)));

  GPIOA->AFR[0] &= ~((0xFUL << (2U * 4U)) |
                     (0xFUL << (3U * 4U)));
  GPIOA->AFR[0] |= ((0x7UL << (2U * 4U)) |
                    (0x7UL << (3U * 4U)));

  GPIOA->AFR[1] &= ~((0xFUL << ((9U - 8U) * 4U)) |
                     (0xFUL << ((10U - 8U) * 4U)));
  GPIOA->AFR[1] |= ((0x7UL << ((9U - 8U) * 4U)) |
                    (0x7UL << ((10U - 8U) * 4U)));
}

static void init_usart(usart_registers_t *uart, uint32_t brr) {
  uart->CR1 = 0U;
  uart->CR2 = 0U;
  uart->CR3 = 0U;
  uart->BRR = brr;
  uart->CR1 = USART_CR1_RE | USART_CR1_TE | USART_CR1_RXNEIE | USART_CR1_UE;
}

static void platform_init_uart_uno(void) {
  RCC_APB1ENR |= RCC_APB1ENR_USART2EN;
  init_usart(USART2_REGS, USART_BRR_9600);
  NVIC_ISER1 = (1UL << (USART2_IRQn - 32U));
}

static void platform_init_uart_j(void) {
  RCC_APB2ENR |= RCC_APB2ENR_USART1EN;
  init_usart(USART1_REGS, USART_BRR_9600);
  NVIC_ISER1 = (1UL << (USART1_IRQn - 32U));
}

static void usart_send_blocking(usart_registers_t *uart, volatile uint32_t *tx_counter, const uint8_t *buffer, uint32_t length) {
  uint32_t index = 0U;
  while (index < length) {
    while ((uart->SR & USART_SR_TXE) == 0U) {
    }
    uart->DR = buffer[index++];
    (*tx_counter)++;
  }

  while ((uart->SR & USART_SR_TC) == 0U) {
  }
}

static void send_j_ping_frame(void) {
  uint8_t frame[CJ_PROTOCOL_MAX_FRAME_SIZE] = {0};
  uint8_t frame_len = cj_protocol_build_frame(0U, CJ_MSG_PING, 0, 0U, frame, sizeof(frame));
  if (frame_len > 0U) {
    platform_send_j_bytes(frame, frame_len);
  }
}

static void platform_service_keepalives(void) {
  uint32_t now = platform_millis();

  if (bridge.state != CJ_BRIDGE_IDLE) {
    return;
  }

  if (!diag_uno_link_confirmed && (now - last_uno_keepalive_ms) >= KEEPALIVE_INTERVAL_MS) {
    last_uno_keepalive_ms = now;
    diag_uno_ping_sent_count++;
    platform_send_uno_line("PING");
  }

  if (!diag_j_link_confirmed && (now - last_j_keepalive_ms) >= KEEPALIVE_INTERVAL_MS) {
    last_j_keepalive_ms = now;
    diag_j_ping_sent_count++;
    send_j_ping_frame();
  }
}

static void platform_observe_bridge_state(void) {
  diag_color_found_count = bridge.diag_color_found_count;
  diag_pick_window_sent_count = bridge.diag_pick_window_sent_count;
  diag_pick_done_count = bridge.diag_pick_done_count;
  diag_pick_timeout_count = bridge.diag_pick_timeout_count;
  diag_arm_fail_count = bridge.diag_arm_fail_count;
  diag_early_j_result_count = bridge.diag_early_j_result_count;

  if (observed_bridge_state != bridge.state) {
    observed_bridge_state = bridge.state;
    diag_bridge_state = bridge.state;
    diag_last_state_transition_ms = platform_millis();
    copy_reason(diag_last_log_reason, cj_bridge_state_name(bridge.state));
  }
}

static uint8_t state_flash_count(cj_bridge_state_t state) {
  switch (state) {
    case CJ_BRIDGE_IDLE:
      return STATE_IDLE_FLASHES;
    case CJ_BRIDGE_WAIT_UNO_STOP_ACK:
      return STATE_WAIT_STOP_FLASHES;
    case CJ_BRIDGE_WAIT_J_RESULT:
      return STATE_WAIT_J_FLASHES;
    case CJ_BRIDGE_WAIT_UNO_RESUME_ACK:
      return STATE_WAIT_RESUME_FLASHES;
    case CJ_BRIDGE_FAULT:
    default:
      return 0U;
  }
}

static void platform_toggle_led(void) {
  uint32_t now = platform_millis();

  if (diag_bridge_state == CJ_BRIDGE_FAULT) {
    platform_set_led_sink(((now / HEARTBEAT_SLOT_MS) & 0x1U) == 0U);
    return;
  }

  uint8_t flashes = state_flash_count(diag_bridge_state);
  uint32_t phase = now % HEARTBEAT_PATTERN_PERIOD_MS;
  bool led_on = false;
  uint8_t flash_index = 0U;

  while (flash_index < flashes) {
    uint32_t slot_start = (uint32_t)flash_index * (HEARTBEAT_SLOT_MS * 2U);
    if (phase >= slot_start && phase < (slot_start + HEARTBEAT_SLOT_MS)) {
      led_on = true;
      break;
    }
    flash_index++;
  }

  platform_set_led_sink(led_on);
}

static void platform_set_led_sink(bool enabled) {
  if (enabled) {
    GPIOB->BSRR = (1UL << (LED_PIN + 16U));
    return;
  }

  GPIOB->BSRR = (1UL << LED_PIN);
}

static void copy_reason(volatile char *dest, const char *src) {
  size_t index = 0U;
  while (index < (REASON_BUFFER_LEN - 1U) && src[index] != '\0') {
    dest[index] = src[index];
    index++;
  }
  dest[index] = '\0';
  index++;
  while (index < REASON_BUFFER_LEN) {
    dest[index++] = '\0';
  }
}
