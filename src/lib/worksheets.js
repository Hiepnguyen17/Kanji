export const WORKSHEET_LIMIT = 100;

export function shuffled(items, random = Math.random) {
  const result = [...items];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

// Measured block heights keep each word/character together on a physical page.
export function paginateBlocks(heights, available, gap = 0) {
  const pages = [];
  let page = [], used = 0;
  heights.forEach((height, index) => {
    if (page.length && used + gap + height > available) {
      pages.push(page); page = []; used = 0;
    }
    used += (page.length ? gap : 0) + height;
    page.push(index);
  });
  if (page.length) pages.push(page);
  return pages;
}

export const worksheetKey = item => String(item.char || item.id);

export function selectWorksheetItems(items, selected, order) {
  const byId = new Map(items.map(item => [worksheetKey(item), item]));
  return order.filter(id => selected.has(id) && byId.has(id)).map(id => byId.get(id));
}
