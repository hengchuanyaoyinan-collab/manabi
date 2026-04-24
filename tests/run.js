const fs = require('fs');
const assert = require('assert');
const path = require('path');

let passed = 0, failed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log(`  \x1b[32m✓\x1b[0m ${name}`); }
  catch(e) { failed++; console.log(`  \x1b[31m✗\x1b[0m ${name}\n    ${e.message}`); }
}

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

console.log('\n\x1b[1mManabi Test Suite\x1b[0m\n');

// ── Structure Tests ──
console.log('\x1b[36mHTML Structure\x1b[0m');

test('Has valid DOCTYPE', () => {
  assert(html.startsWith('<!DOCTYPE html>'));
});

test('Has lang=ja', () => {
  assert(html.includes('<html lang="ja">'));
});

test('Has meta description', () => {
  assert(html.includes('<meta name="description"'));
});

test('Has canonical URL', () => {
  assert(html.includes('<link rel="canonical"'));
});

test('Has Open Graph tags', () => {
  assert(html.includes('og:title'));
  assert(html.includes('og:description'));
  assert(html.includes('og:image'));
});

test('Has JSON-LD structured data', () => {
  assert(html.includes('application/ld+json'));
  assert(html.includes('"@type":"WebApplication"'));
});

test('Has manifest.json link', () => {
  assert(html.includes('rel="manifest"'));
});

test('Has robots meta', () => {
  assert(html.includes('name="robots"'));
});

// ── Page Structure Tests ──
console.log('\n\x1b[36mPage Structure\x1b[0m');

const requiredPages = ['home', 'explore', 'map', 'register', 'matching', 'chat', 'payment', 'profile', 'dashboard', 'admin', 'terms', 'privacy'];
requiredPages.forEach(page => {
  test(`Has "${page}" page`, () => {
    assert(html.includes(`id="${page}"`), `Missing page: ${page}`);
  });
});

// ── Routing Tests ──
console.log('\n\x1b[36mRouting\x1b[0m');

test('Uses History API pushState (not hash)', () => {
  const showPageMatch = html.match(/function showPage[\s\S]*?^}/m);
  assert(!html.includes("'#' + id"), 'Still using hash routing');
  assert(html.includes("history.pushState({ page: id }"), 'Missing pushState');
});

test('Has path-based route parsing in init', () => {
  assert(html.includes("location.pathname.replace"));
});

test('Has popstate handler for path routing', () => {
  assert(html.includes("location.pathname.replace(/^\\//, '')") || html.includes("e.state?.page"));
});

test('Teacher URLs use /teacher/ path', () => {
  assert(html.includes("'/teacher/' + id") || html.includes("'/teacher/'"));
});

// ── Security Tests ──
console.log('\n\x1b[36mSecurity\x1b[0m');

test('Has escapeHtml function', () => {
  assert(html.includes('function escapeHtml'));
});

test('Has CSRF-safe Supabase auth', () => {
  assert(html.includes('supabase.createClient'));
});

test('Uses safe img URL helper', () => {
  assert(html.includes('safeImgUrl'));
});

test('No inline eval() usage', () => {
  const scriptContent = html.replace(/<style[\s\S]*?<\/style>/g, '');
  const evalMatches = scriptContent.match(/[^.]eval\s*\(/g);
  assert(!evalMatches, 'Found eval() usage');
});

// ── Feature Tests ──
console.log('\n\x1b[36mFeatures\x1b[0m');

test('Has report modal', () => {
  assert(html.includes('id="report-modal"'));
  assert(html.includes('function openReportModal'));
  assert(html.includes('function submitReport'));
});

test('Has block functionality', () => {
  assert(html.includes('function blockUser'));
});

test('Has admin dashboard', () => {
  assert(html.includes('function loadAdminReports'));
  assert(html.includes('function isAdmin'));
});

test('Has verification flow', () => {
  assert(html.includes('function requestVerification'));
  assert(html.includes('function submitVerification'));
});

test('Has notification preferences', () => {
  assert(html.includes('pref-push'));
  assert(html.includes('function toggleNotifPref'));
});

test('Has push notification support', () => {
  assert(html.includes('_sendPushNotif'));
});

test('Has GA4 analytics', () => {
  assert(html.includes('googletagmanager.com'));
  assert(html.includes('function trackEvent'));
});

test('Has JSON-LD for teachers', () => {
  assert(html.includes('_injectTeacherJsonLd'));
  assert(html.includes('_removeTeacherJsonLd'));
});

test('Has teacher cache system', () => {
  assert(html.includes('function cacheTeacher'));
  assert(html.includes('function getTeacher'));
});

test('Has server-side pagination', () => {
  assert(html.includes('.range('));
  assert(html.includes('_exploreOffset'));
});

test('Has review integrity (booking-based)', () => {
  assert(html.includes('reviewBookingId'));
});

// ── Vercel Config Tests ──
console.log('\n\x1b[36mVercel Config\x1b[0m');

const vercelConfig = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'vercel.json'), 'utf8'));

test('Has rewrites for SPA routing', () => {
  assert(vercelConfig.rewrites && vercelConfig.rewrites.length > 0);
});

test('Has teacher URL rewrite', () => {
  const teacherRewrite = vercelConfig.rewrites.find(r => r.source.includes('/teacher/'));
  assert(teacherRewrite, 'Missing /teacher/:id rewrite');
});

test('Has security headers', () => {
  const mainHeaders = vercelConfig.headers.find(h => h.source === '/(.*)');
  assert(mainHeaders);
  const headerKeys = mainHeaders.headers.map(h => h.key);
  assert(headerKeys.includes('Content-Security-Policy'));
  assert(headerKeys.includes('Strict-Transport-Security'));
  assert(headerKeys.includes('X-Content-Type-Options'));
  assert(headerKeys.includes('X-Frame-Options'));
});

test('CSP allows Google Analytics', () => {
  const csp = vercelConfig.headers.find(h => h.source === '/(.*)').headers.find(h => h.key === 'Content-Security-Policy').value;
  assert(csp.includes('googletagmanager.com'));
  assert(csp.includes('google-analytics.com'));
});

// ── Summary ──
console.log(`\n\x1b[1mResults: ${passed} passed, ${failed} failed\x1b[0m\n`);
process.exit(failed > 0 ? 1 : 0);
