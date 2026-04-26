import { renderHeader } from './components/header.js';
import { renderFooter } from './components/footer.js';
import { resolve, currentPath } from './router.js';

const root = document.getElementById('app');

const render = () => {
  root.innerHTML = `
    ${renderHeader()}
    <main>${resolve(currentPath())}</main>
    ${renderFooter()}
  `;
  window.scrollTo(0, 0);
};

window.addEventListener('hashchange', render);
window.addEventListener('DOMContentLoaded', render);
render();
