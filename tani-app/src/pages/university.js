import { universities, recipes, subjects } from '../data/seed-recipes.js';
import { renderRecipeCard } from '../components/recipe-card.js';
import { escapeHtml } from '../lib/utils.js';
import { renderNotFound } from './recipe-detail.js';

export const renderUniversity = (slug) => {
  const u = universities.find((x) => x.slug === slug);
  if (!u) return renderNotFound();

  const uniRecipes = recipes.filter((r) => r.universitySlug === slug);
  const uniSubjects = subjects.filter((s) => s.universitySlug === slug);

  const subjectsByName = {};
  uniSubjects.forEach((s) => {
    subjectsByName[s.name] = subjectsByName[s.name] || s;
  });

  const subjectsWithCounts = uniSubjects.map((s) => ({
    ...s,
    count: uniRecipes.filter((r) => r.subjectName === s.name).length
  }));

  return `
<a class="detail-back" href="#/">← 大学一覧</a>

<section class="hero">
  <h1>${escapeHtml(u.name)}</h1>
  <p>${uniRecipes.length} 件のレシピ / ${uniSubjects.length} 科目</p>
</section>

<section class="section">
  <div class="section-title">
    <h2>科目</h2>
  </div>
  <div class="uni-list">
    ${subjectsWithCounts
      .map(
        (s) => `
      <div class="uni-card">
        ${escapeHtml(s.name)}
        <span class="uni-count">${s.count} レシピ${s.count === 0 ? '（未投稿）' : ''}</span>
      </div>`
      )
      .join('')}
  </div>
</section>

<section class="section">
  <div class="section-title">
    <h2>レシピ</h2>
  </div>
  <div class="recipe-grid">
    ${uniRecipes.length ? uniRecipes.map(renderRecipeCard).join('') : '<div class="empty"><strong>まだレシピがありません</strong>あなたが最初の投稿者になりませんか</div>'}
  </div>
</section>
`;
};
