import { renderHome } from './pages/home.js';
import { renderRecipeDetail, renderNotFound } from './pages/recipe-detail.js';
import { renderUniversity } from './pages/university.js';
import { renderNewRecipe } from './pages/new-recipe.js';

const routes = [
  { match: /^\/?$/, render: () => renderHome() },
  { match: /^\/r\/(.+)$/, render: (m) => renderRecipeDetail(m[1]) },
  { match: /^\/u\/([^/]+)$/, render: (m) => renderUniversity(m[1]) },
  { match: /^\/new$/, render: () => renderNewRecipe() }
];

export const resolve = (path) => {
  for (const r of routes) {
    const m = path.match(r.match);
    if (m) return r.render(m);
  }
  return renderNotFound();
};

export const currentPath = () => {
  const hash = window.location.hash || '#/';
  return hash.replace(/^#/, '') || '/';
};
