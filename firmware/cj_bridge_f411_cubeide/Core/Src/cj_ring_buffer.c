#include "cj_ring_buffer.h"

void cj_ring_buffer_init(cj_ring_buffer_t *buffer, uint8_t *storage, size_t capacity) {
  buffer->storage = storage;
  buffer->capacity = capacity;
  buffer->head = 0;
  buffer->tail = 0;
}

bool cj_ring_buffer_push(cj_ring_buffer_t *buffer, uint8_t value) {
  size_t next = (buffer->head + 1U) % buffer->capacity;
  if (next == buffer->tail) {
    return false;
  }

  buffer->storage[buffer->head] = value;
  buffer->head = next;
  return true;
}

bool cj_ring_buffer_pop(cj_ring_buffer_t *buffer, uint8_t *value) {
  if (buffer->head == buffer->tail) {
    return false;
  }

  *value = buffer->storage[buffer->tail];
  buffer->tail = (buffer->tail + 1U) % buffer->capacity;
  return true;
}

size_t cj_ring_buffer_count(const cj_ring_buffer_t *buffer) {
  if (buffer->head >= buffer->tail) {
    return buffer->head - buffer->tail;
  }

  return buffer->capacity - buffer->tail + buffer->head;
}

bool cj_ring_buffer_is_empty(const cj_ring_buffer_t *buffer) {
  return buffer->head == buffer->tail;
}