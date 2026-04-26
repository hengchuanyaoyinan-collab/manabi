import { universities, recipes } from '../data/seed-recipes.js';
import { renderRecipeCard } from '../components/recipe-card.js';
import { escapeHtml } from '../lib/utils.js';

export const renderHome = () => {
  const recipeCountByUni = universities.reduce((acc, u) => {
    acc[u.slug] = recipes.filter((r) => r.universitySlug === u.slug).length;
    return acc;
  }, {});

  const sortedRecipes = [...recipes].sort((a, b) => b.difficulty - a.difficulty);

  return `
<section class="hero">
  <h1>あなたの単位取得経験が、誰かの卒業を後押しする</h1>
  <p>通信制大学の「単位の取り方」を、構造化されたレシピとして共有。<br>難易度・期間・取得方法で検索できる。</p>
  <span class="alpha-note">α版・現在は見本のみ表示中</span>
</section>

<section class="section">
  <div class="section-title">
    <h2>大学を選ぶ</h2>
  </div>
  <div class="uni-list">
    ${universities
      .map(
        (u) => `
      <a class="uni-card" href="#/u/${escapeHtml(u.slug)}">
        ${escapeHtml(u.short)}
        <span class="uni-count">${recipeCountByUni[u.slug] || 0} レシピ</span>
      </a>`
      )
      .join('')}
  </div>
</section>

<section class="section">
  <div class="section-title">
    <h2>最新の単位取得レシピ</h2>
  </div>
  <div class="recipe-grid">
    ${sortedRecipes.map(renderRecipeCard).join('')}
  </div>
</section>

<section class="section">
  <div class="section-title">
    <h2>あなたが最初の投稿者になりませんか</h2>
  </div>
  <div class="empty">
    <strong>科目を絞ると、まだ誰もレシピを書いていない科目が表示されます</strong>
    あなたが取得済みの科目があれば、後輩の役に立ちます。
  </div>
</section>
`;
};
