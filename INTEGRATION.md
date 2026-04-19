# manabi — Supabase × Stripe 連携セットアップ手順

このドキュメントは、`index.html` と `supabase/` 以下のコードを
**実際の Supabase / Stripe アカウント** につなぐために必要な手順をまとめたものです。

- Supabase プロジェクト: `dajngnlvrwesosvgoilh` (ap-northeast-1)
- Stripe アカウント: `acct_1TKXBB2a0OoxzT5q`

MCP 経由で自動適用済みのものと、ダッシュボードで人手作業が必要なものを
明確に分けています。

---

## 0. すでに自動で完了している作業

| 項目 | 状態 |
|---|---|
| Supabase: `profiles` / `skills` / `bookings` / `payments` / `messages` テーブルの RLS 有効化と適切なポリシー追加 | ✅ 適用済み |
| Supabase: `payments` に `stripe_session_id` / `stripe_payment_intent_id` / `currency` / `updated_at` を追加 | ✅ 適用済み |
| Supabase: `auth.users` 作成時に `profiles` 行を自動生成するトリガ | ✅ 適用済み |
| Supabase Edge Function: `create-checkout-session` (verify_jwt = true) | ✅ デプロイ済み |
| Supabase Edge Function: `stripe-webhook` (verify_jwt = false) | ✅ デプロイ済み |
| Stripe: 1回払いセッション用の Product `prod_ULXjPQg07k5Uy7` を作成 | ✅ 作成済み |
| HTML: `STRIPE_PAYMENT_LINK` (固定リンク) を Edge Function 呼び出しに置換 | ✅ 適用済み |
| HTML: Supabase キーを legacy anon → 新 publishable key (`sb_publishable_...`) に変更 | ✅ 適用済み |

---

## 1. サイト側に必要なコード実装 (✅ 済み — このリポジトリに含まれます)

### 変更/新規ファイル

```
index.html                                                      # SPA (全 HTML/CSS/JS)
supabase/migrations/20260416_enable_rls_and_stripe_columns.sql  # スキーマ + RLS (適用済み)
supabase/migrations/20260417_create_reviews_table.sql            # レビュー + 信用スコア
supabase/functions/create-checkout-session/index.ts              # Stripe Checkout Session 作成
supabase/functions/stripe-webhook/index.ts                       # Stripe イベント受信 → DB 反映
```

### フロー概要

1. ユーザが先生を選んで「支払いへ進む」
2. クライアントは `sb.functions.invoke('create-checkout-session', { body: { teacher_name, amount, fee, ... } })` を呼ぶ
3. Edge Function が JWT を検証して `bookings` / `payments` 行を作成
4. Stripe Checkout Session を発行し、`{ url, session_id, booking_id }` を返却
5. クライアントは `window.location.href = url` で Stripe Checkout に遷移
6. 決済後、`?pay=success&session_id=...` に戻ってきて完了画面を表示
7. 並行して Stripe → `stripe-webhook` が呼ばれて `payments.status='paid'`, `bookings.status='confirmed'` に更新

---

## 2. 環境変数の整理

### サイト (HTML) に書いてあって良いもの

これらは公開しても安全です。`index.html` 内で直接定義しています。

| 変数名 | 値 | 使用箇所 |
|---|---|---|
| `SB_URL` | `https://dajngnlvrwesosvgoilh.supabase.co` | ファイル内 `SB_URL` |
| `SB_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (anon key) | ファイル内 `SB_KEY` |

### Supabase Edge Function Secrets (=サーバ側のシークレット)

**ここはダッシュボードで設定が必要です** (§3 参照)。これらの値は **絶対にクライアントに置かないこと**。

| 変数名 | 中身 | 設定先 |
|---|---|---|
| `STRIPE_SECRET_KEY` | Stripe の `sk_test_...` または `sk_live_...` | 両関数 |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook エンドポイント作成時に発行される `whsec_...` | `stripe-webhook` のみ |
| `STRIPE_PRICE_PRODUCT_ID` | `prod_ULXjPQg07k5Uy7` (上で MCP 経由で作成済み) | `create-checkout-session` のみ |
| `PUBLIC_SITE_URL` | 公開しているサイトの URL (例: `https://manabi.example.com`) | `create-checkout-session` のみ |
| `SUPABASE_URL` | (自動注入) | 触らなくてOK |
| `SUPABASE_SERVICE_ROLE_KEY` | (自動注入) | 触らなくてOK |

---

## 3. ダッシュボード上でやる設定 (人手作業)

### 3-1. Stripe ダッシュボード

1. **API キーの取得**
   - <https://dashboard.stripe.com/test/apikeys> (テストモード) を開く
   - **Secret key** (`sk_test_...`) をコピー
   - 本番に切り替えるときは `sk_live_...` を使用

2. **Webhook エンドポイントの作成**
   - <https://dashboard.stripe.com/test/webhooks> を開く
   - 「+ Add endpoint」
   - **Endpoint URL**:
     ```
     https://dajngnlvrwesosvgoilh.supabase.co/functions/v1/stripe-webhook
     ```
   - **Events to send** に以下を追加:
     - `checkout.session.completed`
     - `checkout.session.expired`
     - `checkout.session.async_payment_failed`
     - `charge.refunded`
     - `refund.created`
   - 作成後に表示される **Signing secret** (`whsec_...`) をコピー
     → これが `STRIPE_WEBHOOK_SECRET` になります

### 3-2. Supabase ダッシュボードで Edge Function のシークレットを設定

<https://supabase.com/dashboard/project/dajngnlvrwesosvgoilh/settings/functions>
の **Edge Function Secrets** で以下を追加してください:

| Name | Value |
|---|---|
| `STRIPE_SECRET_KEY` | `sk_test_...` (3-1 でコピーしたもの) |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` (3-1 でコピーしたもの) |
| `STRIPE_PRICE_PRODUCT_ID` | `prod_ULXjPQg07k5Uy7` |
| `PUBLIC_SITE_URL` | あなたのサイトの URL (例: `https://manabi.example.com`) |

> CLI でも `supabase secrets set STRIPE_SECRET_KEY=sk_test_xxx --project-ref dajngnlvrwesosvgoilh` で設定可能です。

### 3-3. Supabase Auth 設定

<https://supabase.com/dashboard/project/dajngnlvrwesosvgoilh/auth/url-configuration>
で以下を設定:

- **Site URL**: あなたの公開サイトの URL (`PUBLIC_SITE_URL` と同じ)
- **Redirect URLs**: 上の URL と、ローカル開発用の `http://localhost:5173` などを追加

オプション:
- <https://supabase.com/dashboard/project/dajngnlvrwesosvgoilh/auth/policies>
  → **Leaked Password Protection** を ON (advisor で警告が出ているため推奨)
- **Google ログイン** を使う場合は
  <https://supabase.com/dashboard/project/dajngnlvrwesosvgoilh/auth/providers>
  で Google プロバイダを有効化し、Google Cloud Console で OAuth クライアントを作成して
  Client ID / Secret を入力。Authorized redirect URI は
  `https://dajngnlvrwesosvgoilh.supabase.co/auth/v1/callback` です。

---

## 4. 動作確認手順

### 4-1. シークレット設定後の最低限のスモークテスト

1. ブラウザで `index.html` を開く (ローカル/ホスティング先どちらでも)
2. 新規ユーザで登録 → ログイン
   - ✅ 期待: `profiles` テーブルに自分の行が自動で作られている
     ```sql
     select * from profiles where id = auth.uid();
     ```
3. 任意の先生カードを開いて「予約する」→ 日時選択 → 「支払いへ進む」
4. 「支払い方法を選ぶ」→ 「¥xxx を支払う 🔒」
   - ✅ 期待: Stripe Checkout (`https://checkout.stripe.com/...`) にリダイレクトされる
   - ❌ 失敗時: ブラウザの DevTools Console と
     [Function logs](https://supabase.com/dashboard/project/dajngnlvrwesosvgoilh/functions/create-checkout-session/logs)
     を確認

5. **Stripe テストカード** で支払う
   - 番号: `4242 4242 4242 4242`
   - 有効期限: 任意の未来 (例: `12/34`)
   - CVC: 任意 (例: `123`)
   - 郵便番号: 任意 (例: `100-0001`)

6. 戻ってきたページで「支払い完了！」が表示される
   - ✅ 期待: URL に `?pay=success&session_id=cs_test_...`
   - ✅ 期待: 数秒以内に Webhook が発火して DB が更新される
     ```sql
     select id, status, stripe_session_id, stripe_payment_intent_id, updated_at
     from payments order by created_at desc limit 1;
     -- status = 'paid', stripe_payment_intent_id が埋まっていれば成功

     select id, status from bookings order by created_at desc limit 1;
     -- status = 'confirmed' になっていれば成功
     ```

### 4-2. Stripe ダッシュボードでも確認

- <https://dashboard.stripe.com/test/payments> に決済が入っていること
- <https://dashboard.stripe.com/test/webhooks> → 作成したエンドポイント →
  「Events」タブで `checkout.session.completed` が `200` で配信されていること

### 4-3. 失敗系のテスト

| ケース | 操作 | 期待 |
|---|---|---|
| キャンセル | Stripe Checkout で「← 戻る」 | `?pay=cancel` で戻り、通知に「キャンセルされました」 |
| 失敗カード | カード番号 `4000 0000 0000 0002` | Stripe 側で拒否され、`payments.status` は `pending` のまま (timeout で `expired` になれば `failed` に更新) |
| Webhook 不正署名 | curl で偽の body を POST | 400 `signature_invalid` |
| 未ログインで決済 | DevTools で `currentUser=null` のまま `startStripeCheckout()` を実行 | アラート「ログインしてください」 |

### 4-4. ログとエラーの場所

- Edge Function のログ:
  - <https://supabase.com/dashboard/project/dajngnlvrwesosvgoilh/functions/create-checkout-session/logs>
  - <https://supabase.com/dashboard/project/dajngnlvrwesosvgoilh/functions/stripe-webhook/logs>
- Stripe イベントログ:
  - <https://dashboard.stripe.com/test/events>

---

## 5. やっていない/オプション項目

- **本番モードへの切替**: 上の `sk_test_...` / `whsec_...` を本番の `sk_live_...` / `whsec_...` に置き換えるだけです (Webhook エンドポイントも本番モード側で再作成が必要)
- **Stripe Connect (先生への送金)**: 現状の payments 行は決済の記録のみ。先生口座への送金は未実装。必要なら Stripe Connect Express + Transfers API を追加してください
- **領収書/請求書**: Stripe Checkout の `invoice_creation: { enabled: true }` を `create-checkout-session/index.ts` に追加可能
- **メール通知 (購入完了)**: Supabase Auth の SMTP 設定 + DB トリガで送るか、Edge Function 内で Resend などに連携

---

## 6. Stripe テスト用の参考リンク

- テストカード一覧: <https://docs.stripe.com/testing#cards>
- Checkout のテスト方法: <https://docs.stripe.com/payments/checkout>
- Webhook のローカルデバッグ: `stripe listen --forward-to https://dajngnlvrwesosvgoilh.supabase.co/functions/v1/stripe-webhook`
