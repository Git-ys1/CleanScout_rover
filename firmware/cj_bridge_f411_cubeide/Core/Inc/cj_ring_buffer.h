#ifndef CJ_RING_BUFFER_H_
#define CJ_RING_BUFFER_H_

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
  uint8_t *storage;
  size_t capacity;
  volatile size_t head;
  volatile size_t tail;
} cj_ring_buffer_t;

void cj_ring_buffer_init(cj_ring_buffer_t *buffer, uint8_t *storage, size_t capacity);
bool cj_ring_buffer_push(cj_ring_buffer_t *buffer, uint8_t value);
bool cj_ring_buffer_pop(cj_ring_buffer_t *buffer, uint8_t *value);
size_t cj_ring_buffer_count(const cj_ring_buffer_t *buffer);
bool cj_ring_buffer_is_empty(const cj_ring_buffer_t *buffer);

#endif