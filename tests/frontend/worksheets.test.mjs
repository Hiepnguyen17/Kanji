import assert from 'node:assert/strict';
import test from 'node:test';
import { paginateBlocks, selectWorksheetItems, shuffled } from '../../src/lib/worksheets.js';

test('pagination includes spacing and keeps blocks whole at page boundaries', () => {
  assert.deepEqual(paginateBlocks([40, 50, 30], 100, 10), [[0, 1], [2]]);
  assert.deepEqual(paginateBlocks([40, 51, 30], 100, 10), [[0], [1, 2]]);
  assert.deepEqual(paginateBlocks([], 100, 10), []);
  assert.deepEqual(paginateBlocks([120, 20], 100, 10), [[0], [1]]);
});

test('questions and answer keys use the same selected order without changing source data', () => {
  const items = [{ id: 1, word: '学校' }, { id: 2, word: '先生' }, { id: 3, word: '学生' }];
  const order = shuffled(['1', '2', '3'], () => 0);
  assert.deepEqual(order, ['2', '3', '1']);
  assert.deepEqual(selectWorksheetItems(items, new Set(['1', '3']), order).map(item => item.word), ['学生', '学校']);
  assert.deepEqual(items.map(item => item.id), [1, 2, 3]);
  assert.deepEqual(selectWorksheetItems(items, new Set(), order), []);
});

test('Kanji selection uses characters, ignores stale IDs from another source', () => {
  assert.deepEqual(selectWorksheetItems([{ char: '人' }, { char: '学' }], new Set(['学', '旧']), ['旧', '学', '人']), [{ char: '学' }]);
});
