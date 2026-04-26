import { escapeHtml, stars, outcomeLabel } from '../lib/utils.js';

export const renderRecipeCard = (r) => `
<a class="recipe-card" href="#/r/${escapeHtml(r.id)}">
  <div class="meta-row">
    <span class="uni">${escapeHtml(r.universityShort)}</span>
    <span>${escapeHtml(r.subjectName)}</span>
    ${r.isSample ? '<span class="sample-badge">サンプル</span>' : ''}
  </div>
  <h3>${escapeHtml(r.title)}</h3>
  <p class="summary">${escapeHtml(r.summary || '')}</p>
  <div class="stats">
    ${stars(r.difficulty)}
    <span>${escapeHtml(r.durationWeeks)} 週間</span>
    <span class="outcome-badge outcome-${escapeHtml(r.outcome)}">${escapeHtml(outcomeLabel(r.outcome))}</span>
  </div>
</a>
`;
