import assert from 'node:assert/strict';
import test from 'node:test';
import { tokenizeFormula } from '../../src/lib/grammarFormula.js';

test('renders learner placeholders as typed chips', () => {
  assert.deepEqual(tokenizeFormula('N1 + Vます + たい'), [
    { type: 'chip', label: 'N1', variant: 'noun' },
    { type: 'separator', label: '+' },
    { type: 'chip', label: 'Vます', variant: 'verb' },
    { type: 'separator', label: '+' },
    { type: 'text', label: 'たい' },
  ]);
});

test('normalizes legacy English grammar labels before rendering', () => {
  const parts = tokenizeFormula('Noun + Verb stem + Plain form');
  assert.deepEqual(parts.filter(part => part.type === 'chip'), [
    { type: 'chip', label: 'N', variant: 'noun' },
    { type: 'chip', label: 'Vます', variant: 'verb' },
    { type: 'chip', label: 'TTT', variant: 'plain' },
  ]);
});

test('keeps Japanese grammar text as ordinary text', () => {
  assert.deepEqual(tokenizeFormula('Vる + ことにする').at(-1), {
    type: 'text', label: 'ことにする',
  });
});
