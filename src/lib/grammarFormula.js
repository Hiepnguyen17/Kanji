const grammarSymbol = token => {
  const value = token.trim();
  if (/^N\d*$/.test(value)) return [value, 'noun'];
  if (value === 'Gốc Vます') return ['Vます', 'verb'];
  if (/^V\d*$/.test(value) || /^V(?:ます|て|た|ない|る)$/.test(value)) return [value, 'verb'];
  if (value === 'A') return ['A', 'adj'];
  if (value === 'Aい') return ['Aい', 'iadj'];
  if (value === 'Aな') return ['Aな', 'naadj'];
  if (value === 'TTT') return ['TTT', 'plain'];
  if (value === 'Câu' || value === 'Cụm trích dẫn') return ['S', 'sentence'];
  if (value === 'Số') return ['Số', 'number'];
  if (value === 'Địa điểm') return ['Địa điểm', 'place'];
  if (value === 'Thời gian') return ['Thời gian', 'time'];
  return null;
};

export const localizeLegacyFormula = formula => String(formula || '')
  .replace(/Sino-Japanese noun|Noun/gi, 'N')
  .replace(/Verb stem|V[ -]stem|Vます-stem|Verb ます-stem/gi, 'Gốc Vます')
  .replace(/V-dictionary form|Verb \(dictionary form\)|dictionary form/gi, 'Vる')
  .replace(/Plain form/gi, 'TTT').replace(/plain non-past/gi, 'TTT không quá khứ')
  .replace(/i-adjective|i-adj/gi, 'Aい').replace(/na-adjective|na-adj/gi, 'Aな')
  .replace(/Sentence|Clause/gi, 'Câu').replace(/Quoted phrase/gi, 'Cụm trích dẫn')
  .replace(/Number/gi, 'Số').replace(/Place/gi, 'Địa điểm').replace(/Time/gi, 'Thời gian');

// A serializable representation lets tests cover the visible chip contract
// without a browser or JSX renderer.
export const tokenizeFormula = formula => localizeLegacyFormula(formula)
  .split(/(Gốc Vます|V(?:ます|て|た|ない|る|\d+)?|TTT|Cụm trích dẫn|Câu|Địa điểm|Thời gian|Số|Aい|Aな|N\d*|A|[+／/])/g)
  .filter(part => part && part.trim())
  .map(part => {
    const symbol = grammarSymbol(part);
    if (symbol) return { type: 'chip', label: symbol[0], variant: symbol[1] };
    if (/^[+／/]$/.test(part)) return { type: 'separator', label: part };
    return { type: 'text', label: part.trim() };
  });
