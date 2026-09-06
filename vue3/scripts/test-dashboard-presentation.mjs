import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFile } from 'node:fs/promises'
const source = await readFile(new URL('../src/pages/index/presentation.js', import.meta.url), 'utf8')
const { onlineLabel, taskLabel, numberText, isStale, ageText } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`)
test('connectivity does not imply a task; unavailable status is never idle', () => {
  assert.equal(onlineLabel(null, null), '状态未知')
  assert.equal(onlineLabel(null, null, true), '连接中')
  assert.equal(onlineLabel({ enabled: true, connected: true }, null), '在线')
  assert.equal(onlineLabel({ enabled: true, connected: false }, { online: true }), '离线')
  assert.equal(onlineLabel({ enabled: false }, { online: true }), '状态未知')
  assert.equal(taskLabel(undefined), '状态未知')
  assert.equal(taskLabel('new-enum'), '状态未知')
  assert.equal(taskLabel('idle'), '待机中')
  assert.equal(taskLabel('cleaning'), '清扫中')
  assert.equal(taskLabel('paused'), '已暂停')
})
test('missing numbers differ from a reported zero', () => {
  for (const value of [undefined, null, '', false, NaN, 'bad']) assert.equal(numberText(value, '%'), '暂未收到数据')
  assert.equal(numberText(0, '%'), '0%')
  assert.equal(numberText(87, '%'), '87%')
  assert.equal(numberText(-0.5, ' m/s'), '-0.5 m/s')
})
test('data age uses timestamps, not assumed online status', () => {
  const now = Date.parse('2026-09-06T12:00:00Z')
  assert.equal(ageText('2026-09-06T11:59:57Z', now), '3 秒前更新')
  assert.equal(isStale('2026-09-06T11:59:29Z', now), true)
  assert.equal(isStale(null, now), false)
  assert.equal(ageText(null, now), '更新时间未知')
  assert.equal(ageText('invalid', now), '更新时间未知')
})
