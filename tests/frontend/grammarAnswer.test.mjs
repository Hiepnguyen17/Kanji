import test from 'node:test';
import assert from 'node:assert/strict';
import { matchesGrammarReference, normalizeGrammarAnswer, preliminaryGrammarFeedback } from '../../src/lib/grammarAnswer.js';
import { grammarPractice, practiceQuestions } from '../../src/data/grammarPractice.js';

test('normalizes spacing, width and final punctuation only', () => {
  assert.equal(normalizeGrammarAnswer(' これは　本 です。 '), 'これは本です');
  assert.equal(matchesGrammarReference('これは本です', 'これは本です。'), true);
  assert.equal(matchesGrammarReference('これはペンです。', 'これは本です。'), false);
  assert.equal(matchesGrammarReference('', 'これは本です。'), false);
});

test('preliminary feedback never claims a different translation is wrong', () => {
  assert.match(preliminaryGrammarFeedback('これはほんです。', 'これは本です。'), /chưa chắc sai/);
  assert.match(preliminaryGrammarFeedback('こんにちは。', 'これは本です。'), /chưa chấm được/);
});

test('N5 first-lesson patterns have five distinct sentences', () => {
  const pattern = { formula: 'N + です', examples: [{ japanese: 'これは本です。', meaning_vi: 'Đây là sách.' }] };
  const questions = practiceQuestions(pattern, 'N5');
  assert.equal(questions.length, 5);
  assert.equal(new Set(questions.map(item => item.japanese)).size, 5);
});

test('never mixes another grammar pattern into the questions', () => {
  const pattern = { formula: 'Câu + か', examples: [{ japanese: 'これは何ですか。', meaning_vi: 'Đây là gì?' }] };
  const questions = practiceQuestions(pattern, 'N5');
  assert.equal(questions.length, 5);
  assert.ok(questions.every(item => item.japanese.endsWith('か。')));
});

test('all 77 N5 grammar patterns have four unique supplementary pairs', () => {
  assert.equal(Object.keys(grammarPractice).length, 77);
  for (const [key, pairs] of Object.entries(grammarPractice)) {
    assert.ok(key.startsWith('N5|'), key);
    assert.equal(pairs.length, 4, key);
    assert.equal(new Set(pairs.map(([japanese]) => japanese)).size, 4, key);
    assert.ok(pairs.every(([japanese, meaning]) => japanese.trim() && meaning.trim()), key);
  }
});
