export const escapeHtml = (s) =>
  String(s ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

export const stars = (n) => {
  const full = Math.max(0, Math.min(5, Number(n) || 0));
  let html = '<span class="difficulty">';
  for (let i = 0; i < 5; i++) {
    html += `<span class="${i < full ? 'filled' : 'empty'}">★</span>`;
  }
  return html + '</span>';
};

export const outcomeLabel = (outcome) => {
  if (outcome === 'obtained') return '取得';
  if (outcome === 'failed') return '失敗';
  if (outcome === 'in_progress') return '進行中';
  return outcome;
};

export const methodTypeLabel = (m) => {
  switch (m) {
    case 'exam_only': return '試験のみ';
    case 'report_exam': return 'レポート + 試験';
    case 'schooling': return 'スクーリング';
    case 'media': return 'メディア授業';
    default: return m || 'その他';
  }
};
