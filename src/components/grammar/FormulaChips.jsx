import { tokenizeFormula } from '../../lib/grammarFormula';

export default function FormulaChips({ formula }) {
  return <div className="formula-chips">{tokenizeFormula(formula).map((part, index) => {
    if (part.type === 'chip') return <b className={`grammar-chip ${part.variant}`} key={`${part.label}-${index}`}>{part.label}</b>;
    if (part.type === 'separator') return <i key={`${part.label}-${index}`}>{part.label}</i>;
    return <span key={`${part.label}-${index}`}>{part.label}</span>;
  })}</div>;
}
