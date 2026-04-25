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

const requiredPages = ['home', 'explore', 'map', 'register', 'matching', 'chat', 'payment', 'profile', 'dashboard', 'admin', 'terms', 'privacy', 'tokushoho', 'contact'];
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

test('Has Stripe Connect integration', () => {
  assert(html.includes('function startStripeOnboarding'));
  assert(html.includes('function loadConnectStatus'));
  assert(html.includes('function requestPayout'));
  assert(html.includes('function openStripeDashboard'));
  assert(html.includes('id="stripe-connect-section"'));
});

test('Has refund request flow', () => {
  assert(html.includes('function requestRefund'));
  assert(html.includes('function submitRefundRequest'));
  assert(html.includes('function approveRefund'));
  assert(html.includes('function rejectRefund'));
  assert(html.includes('id="refund-modal"'));
});

test('Has video call integration', () => {
  assert(html.includes('function startVideoCall'));
  assert(html.includes('function closeVideoCall'));
  assert(html.includes('meet.jit.si'));
  assert(html.includes('id="video-modal"'));
  assert(html.includes('id="video-iframe"'));
});

// ── Legal/Compliance Tests ──
console.log('\n\x1b[36mLegal & Compliance\x1b[0m');

test('Has 特定商取引法 disclosure', () => {
  assert(html.includes('特定商取引法に基づく表記'));
  assert(html.includes('id="tokushoho"'));
});

test('Privacy policy lists all third-party services', () => {
  assert(html.includes('Supabase'), 'Missing Supabase in privacy');
  assert(html.includes('Stripe'), 'Missing Stripe in privacy');
  assert(html.includes('Google Analytics'), 'Missing GA in privacy');
  assert(html.includes('OpenAI'), 'Missing OpenAI in privacy');
  assert(html.includes('Jitsi'), 'Missing Jitsi in privacy');
});

test('Has cookie consent banner', () => {
  assert(html.includes('id="cookie-consent"'));
  assert(html.includes('function acceptCookies'));
  assert(html.includes('function rejectCookies'));
});

test('Has contact page', () => {
  assert(html.includes('id="contact"'));
  assert(html.includes('support@manabi-bay.vercel.app'));
});

// ── Edge Functions Tests ──
console.log('\n\x1b[36mEdge Functions\x1b[0m');

const edgeFunctionsDir = path.join(__dirname, '..', 'supabase', 'functions');

test('Has process-payout edge function', () => {
  const fp = path.join(edgeFunctionsDir, 'process-payout', 'index.ts');
  assert(fs.existsSync(fp), 'process-payout/index.ts missing');
  const src = fs.readFileSync(fp, 'utf8');
  assert(src.includes("action: 'onboard'") || src.includes("'onboard'"), 'Missing onboard action');
  assert(src.includes("action: 'payout'") || src.includes("'payout'"), 'Missing payout action');
  assert(src.includes('stripe.transfers') || src.includes('Transfer'), 'Missing Stripe transfer');
});

test('Has process-refund edge function', () => {
  const fp = path.join(edgeFunctionsDir, 'process-refund', 'index.ts');
  assert(fs.existsSync(fp), 'process-refund/index.ts missing');
  const src = fs.readFileSync(fp, 'utf8');
  assert(src.includes('request_refund'), 'Missing request_refund action');
  assert(src.includes('approve_refund'), 'Missing approve_refund action');
  assert(src.includes('stripe.refunds'), 'Missing Stripe refund');
});

test('Has create-checkout-session edge function', () => {
  const fp = path.join(edgeFunctionsDir, 'create-checkout-session', 'index.ts');
  assert(fs.existsSync(fp), 'create-checkout-session/index.ts missing');
  const src = fs.readFileSync(fp, 'utf8');
  assert(src.includes('checkout.sessions.create'), 'Missing Stripe checkout session creation');
});

test('All edge functions have config.toml', () => {
  const funcs = fs.readdirSync(edgeFunctionsDir).filter(f =>
    fs.statSync(path.join(edgeFunctionsDir, f)).isDirectory()
  );
  for (const fn of funcs) {
    const toml = path.join(edgeFunctionsDir, fn, 'config.toml');
    assert(fs.existsSync(toml), `${fn}/config.toml missing`);
    const content = fs.readFileSync(toml, 'utf8');
    assert(content.includes('verify_jwt'), `${fn}/config.toml missing verify_jwt`);
  }
});

test('Stripe webhook has verify_jwt = false', () => {
  const toml = fs.readFileSync(path.join(edgeFunctionsDir, 'stripe-webhook', 'config.toml'), 'utf8');
  assert(toml.includes('verify_jwt = false'), 'stripe-webhook must have verify_jwt = false');
});

test('User-facing functions have verify_jwt = true', () => {
  const userFuncs = ['create-checkout-session', 'process-payout', 'process-refund', 'generate-bio', 'analyze-profile', 'auto-match'];
  for (const fn of userFuncs) {
    const toml = fs.readFileSync(path.join(edgeFunctionsDir, fn, 'config.toml'), 'utf8');
    assert(toml.includes('verify_jwt = true'), `${fn} must have verify_jwt = true`);
  }
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

test('CSP allows Stripe Checkout iframe', () => {
  const csp = vercelConfig.headers.find(h => h.source === '/(.*)').headers.find(h => h.key === 'Content-Security-Policy').value;
  assert(csp.includes('checkout.stripe.com'), 'frame-src must allow checkout.stripe.com');
});

test('CSP allows Supabase connections', () => {
  const csp = vercelConfig.headers.find(h => h.source === '/(.*)').headers.find(h => h.key === 'Content-Security-Policy').value;
  assert(csp.includes('supabase.co'), 'connect-src must allow supabase.co');
  assert(csp.includes('wss://'), 'connect-src must allow WebSocket connections');
});

test('Has dashboard sub-path rewrite', () => {
  const dashRewrite = vercelConfig.rewrites.find(r => r.source.includes('/dashboard/:path'));
  assert(dashRewrite, 'Missing /dashboard/:path* rewrite');
});

test('Has service worker cache header', () => {
  const swHeaders = vercelConfig.headers.find(h => h.source === '/sw.js');
  assert(swHeaders, 'Missing sw.js header config');
  const cacheControl = swHeaders.headers.find(h => h.key === 'Cache-Control');
  assert(cacheControl && cacheControl.value.includes('no-cache'), 'sw.js must have no-cache');
});

// ── Zehitomo Features Tests ──
console.log('\n\x1b[36mZehitomo-Inspired Features\x1b[0m');

test('Has social proof on register page', () => {
  assert(html.includes('id="reg-benefits"'));
  assert(html.includes('reg-stat-teachers'));
});

test('Has tagline/キャッチコピー field', () => {
  assert(html.includes('id="reg-tagline"'));
  assert(html.includes('id="edit-tagline"'));
  assert(html.includes('キャッチコピー'));
});

test('Has profile completeness checklist', () => {
  assert(html.includes('tip:') && html.includes('action:'));
  assert(html.includes('プロフィール完成度'));
});

test('Has per-skill service area selection', () => {
  assert(html.includes('AREA_PRESETS'));
  assert(html.includes('id="reg-area-chips"'));
  assert(html.includes('service_areas'));
  assert(html.includes('toggleAreaChip'));
});

test('Has portfolio gallery system', () => {
  assert(html.includes('submitPortfolio'));
  assert(html.includes('loadPortfolios'));
  assert(html.includes('deletePortfolio'));
  assert(html.includes('id="modal-portfolio"'));
});

test('Has imported reviews system', () => {
  assert(html.includes('submitImportedReview'));
  assert(html.includes('loadImportedReviews'));
  assert(html.includes('id="modal-imported-reviews"'));
  assert(html.includes('source_platform'));
});

test('Has admin imported reviews approval', () => {
  assert(html.includes('loadAdminImportedReviews'));
  assert(html.includes('reviewImportedReview'));
  assert(html.includes('id="admin-imported-reviews"'));
});

// ── Production Readiness Tests ──
console.log('\n\x1b[36mProduction Readiness\x1b[0m');

test('Has AI rate limiting', () => {
  assert(html.includes('aiRateLimit'));
  assert(html.includes('_aiLastCall'));
});

test('Has form validation (required fields)', () => {
  assert(html.includes('id="signup-name"') && html.includes('required'));
  assert(html.includes('id="signup-email"') && html.includes('required'));
  assert(html.includes('minlength="8"'));
});

test('Has image alt attributes for accessibility', () => {
  assert(html.includes('alt="ポートフォリオ写真プレビュー"'));
  assert(html.includes('alt="本人確認書類プレビュー"'));
});

test('Edge functions have API timeouts', () => {
  const autoMatch = fs.readFileSync(path.join(edgeFunctionsDir, 'auto-match', 'index.ts'), 'utf8');
  const genBio = fs.readFileSync(path.join(edgeFunctionsDir, 'generate-bio', 'index.ts'), 'utf8');
  const analyze = fs.readFileSync(path.join(edgeFunctionsDir, 'analyze-profile', 'index.ts'), 'utf8');
  assert(autoMatch.includes('AbortController'), 'auto-match missing timeout');
  assert(genBio.includes('AbortController'), 'generate-bio missing timeout');
  assert(analyze.includes('AbortController'), 'analyze-profile missing timeout');
});

test('Sourcemaps disabled in production', () => {
  const vite = fs.readFileSync(path.join(__dirname, '..', 'vite.config.js'), 'utf8');
  assert(vite.includes('sourcemap: false'), 'Sourcemaps should be disabled');
});

test('SW has date-based cache version', () => {
  const sw = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');
  assert(sw.match(/manabi-\d{8}/), 'SW cache should use date-based version');
});

test('Valid pages includes all routes', () => {
  assert(html.includes("'tokushoho','contact','admin'"));
});

test('Has noscript fallback', () => {
  assert(html.includes('<noscript>'));
});

test('Has network offline/online handlers', () => {
  assert(html.includes("addEventListener('offline'"));
  assert(html.includes("addEventListener('online'"));
});

test('Has unhandled rejection handler', () => {
  assert(html.includes("addEventListener('unhandledrejection'"));
});

test('Has script preload hints', () => {
  assert(html.includes('rel="preload"') && html.includes('as="script"'));
});

test('Has meta keywords', () => {
  assert(html.includes('name="keywords"'));
});

test('Has catch-all 404 rewrite', () => {
  const hasWildcard = vercelConfig.rewrites.some(r => r.source.includes('(?!') || r.source === '/:path*');
  assert(hasWildcard, 'Missing catch-all rewrite for unknown routes');
});

test('Robots.txt blocks private paths', () => {
  const robots = fs.readFileSync(path.join(__dirname, '..', 'robots.txt'), 'utf8');
  assert(robots.includes('Disallow: /dashboard'));
  assert(robots.includes('Disallow: /admin'));
  assert(robots.includes('Disallow: /chat'));
});

test('Permissions-Policy allows camera for Jitsi', () => {
  const pp = vercelConfig.headers.find(h => h.source === '/(.*)').headers.find(h => h.key === 'Permissions-Policy').value;
  assert(pp.includes('camera=(self)'), 'Camera must be allowed for Jitsi video calls');
});

// ── Summary ──
console.log(`\n\x1b[1mResults: ${passed} passed, ${failed} failed\x1b[0m\n`);
process.exit(failed > 0 ? 1 : 0);
