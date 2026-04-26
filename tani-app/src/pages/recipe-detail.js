import { recipes } from '../data/seed-recipes.js';
import { escapeHtml, stars, outcomeLabel, methodTypeLabel } from '../lib/utils.js';

export const renderRecipeDetail = (id) => {
  const r = recipes.find((x) => x.id === id);
  if (!r) return renderNotFound();

  return `
<a class="detail-back" href="#/">← 戻る</a>

<div class="detail-header">
  <div class="breadcrumb">${escapeHtml(r.universityShort)} / ${escapeHtml(r.faculty || '')} / ${escapeHtml(r.subjectName)}</div>
  <h1>${escapeHtml(r.title)} ${r.isSample ? '<span class="sample-badge">サンプル</span>' : ''}</h1>
  <div class="meta-pills">
    <span class="pill">${stars(r.difficulty)} 難易度</span>
    <span class="pill">${escapeHtml(r.durationWeeks)} 週間 / ${escapeHtml(r.durationHours)} h</span>
    <span class="pill">${escapeHtml(methodTypeLabel(r.methodType))}</span>
    <span class="pill outcome-${escapeHtml(r.outcome)}">${escapeHtml(outcomeLabel(r.outcome))}</span>
    <span class="pill">${escapeHtml(r.obtainedYear)}年度</span>
  </div>
</div>

<div class="detail-author">
  <div class="avatar">${escapeHtml(r.authorAvatar || r.authorName?.[0] || '?')}</div>
  <div class="info">
    <div class="name">${escapeHtml(r.authorName)}</div>
    <div class="sub">${escapeHtml(r.authorMeta || '')}</div>
  </div>
</div>

${
  r.summary
    ? `<div class="detail-section">
        <h2>サマリ</h2>
        <p>${escapeHtml(r.summary)}</p>
      </div>`
    : ''
}

${
  r.steps && r.steps.length
    ? `<div class="detail-section">
        <h2>取得ステップ</h2>
        <div class="steps">
          ${r.steps
            .map(
              (s, i) => `
            <div class="step">
              <div class="step-num">${i + 1}</div>
              <div class="step-title">${escapeHtml(s.title)}</div>
              <div class="step-body">${escapeHtml(s.body || '')}</div>
              ${s.tips ? `<div class="step-tips"><strong>ヒント：</strong>${escapeHtml(s.tips)}</div>` : ''}
            </div>`
            )
            .join('')}
        </div>
      </div>`
    : ''
}

${
  r.tools && r.tools.length
    ? `<div class="detail-section">
        <h2>使った道具</h2>
        <div class="tools-list">
          ${r.tools
            .map(
              (t) => `
            <div class="item">
              <div class="name">${escapeHtml(t.name)}</div>
              ${t.note ? `<div class="note">${escapeHtml(t.note)}</div>` : ''}
            </div>`
            )
            .join('')}
        </div>
      </div>`
    : ''
}

${
  r.pitfalls && r.pitfalls.length
    ? `<div class="detail-section">
        <h2>つまずきポイント</h2>
        <div class="pitfalls-list">
          ${r.pitfalls
            .map(
              (p) => `
            <div class="item">
              <div class="situation">${escapeHtml(p.situation)}</div>
              <div class="solution">→ ${escapeHtml(p.solution)}</div>
            </div>`
            )
            .join('')}
        </div>
      </div>`
    : ''
}

<div class="actions">
  <button onclick="alert('α版のため、つくれぽ機能は未実装です')">私もこれで取得した</button>
  <button onclick="alert('α版のため、ブックマーク機能は未実装です')">ブックマーク</button>
  <button class="primary" onclick="alert('α版のため、投稿機能は未実装です')">私も書く</button>
</div>
`;
};

export const renderNotFound = () => `
<section class="hero">
  <h1>レシピが見つかりません</h1>
  <p>削除されたか、URL が間違っている可能性があります。</p>
  <p style="margin-top:24px;"><a href="#/" style="color:var(--accent);font-weight:700;">ホームに戻る →</a></p>
</section>
`;
