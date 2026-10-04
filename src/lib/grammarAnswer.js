export function normalizeGrammarAnswer(value) {
  return String(value || '')
    .normalize('NFKC')
    .replace(/[\s\u3000]+/g, '')
    .replace(/[。．.!！?？]+$/u, '');
}

export function matchesGrammarReference(answer, reference) {
  const normalized = normalizeGrammarAnswer(answer);
  return normalized.length > 0 && normalized === normalizeGrammarAnswer(reference);
}

// Phản hồi dựa trên độ gần của câu mẫu, không phải chấm ngữ nghĩa hay AI.
export function preliminaryGrammarFeedback(answer, reference) {
  const entered = Array.from(normalizeGrammarAnswer(answer));
  const expected = Array.from(normalizeGrammarAnswer(reference));
  if (!entered.length) return 'Hãy nhập một câu tiếng Nhật trước khi đánh giá.';
  if (entered.join('') === expected.join('')) return 'Câu của bạn trùng với đáp án mẫu.';

  const previous = Array.from({ length: expected.length + 1 }, (_, index) => index);
  for (let index = 0; index < entered.length; index += 1) {
    const current = [index + 1];
    for (let offset = 0; offset < expected.length; offset += 1) {
      current.push(Math.min(
        current[offset] + 1,
        previous[offset + 1] + 1,
        previous[offset] + (entered[index] === expected[offset] ? 0 : 1),
      ));
    }
    previous.splice(0, previous.length, ...current);
  }
  const similarity = 1 - previous[expected.length] / Math.max(entered.length, expected.length);
  if (similarity >= 0.7) return 'Câu của bạn gần câu mẫu. Hãy xem lại chữ và trợ từ khác nhau; câu khác mẫu chưa chắc sai.';
  return 'Câu của bạn khác câu mẫu khá nhiều. Hãy xem gợi ý hoặc đáp án để đối chiếu; chức năng này chưa chấm được các cách dịch khác.';
}
