(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin===`use-credentials`?t.credentials=`include`:e.crossOrigin===`anonymous`?t.credentials=`omit`:t.credentials=`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e=()=>`
<header class="app-header">
  <a href="#/" class="logo">Tan-i<span class="badge">α</span></a>
  <nav>
    <a href="#/">ホーム</a>
    <a href="#/new">投稿</a>
  </nav>
</header>
`,t=()=>`
<footer class="app-footer">
  <div>Tan-i — 単位取得レシピ・プラットフォーム（α版）</div>
  <div class="disclaimer">
    本サービスは個人が運営する非公式なものであり、いかなる大学とも提携・関係ありません。
    投稿された内容は投稿者の体験に基づくものであり、単位取得を保証するものではありません。
    各大学の学術不正規定（代筆・剽窃の禁止）および試験規則を遵守してください。
  </div>
</footer>
`,n=[{slug:`hosei-correspondence`,name:`法政大学通信教育部`,short:`法政通信`},{slug:`open-university-japan`,name:`放送大学`,short:`放送大学`},{slug:`keio-correspondence`,name:`慶應義塾大学通信教育課程`,short:`慶應通信`},{slug:`nihon-correspondence`,name:`日本大学通信教育部`,short:`日大通信`}],r=[{id:`s1`,universitySlug:`hosei-correspondence`,faculty:`法学部`,name:`民法総則`,credits:4},{id:`s2`,universitySlug:`hosei-correspondence`,faculty:`法学部`,name:`憲法`,credits:4},{id:`s3`,universitySlug:`hosei-correspondence`,faculty:`法学部`,name:`行政法II`,credits:4},{id:`s4`,universitySlug:`open-university-japan`,faculty:`教養学部`,name:`心理学概論`,credits:2}],i=[{id:`r1`,isSample:!0,universitySlug:`hosei-correspondence`,universityShort:`法政通信`,faculty:`法学部`,subjectName:`民法総則`,title:`民法総則を3週間で取った方法（社会人・働きながら）`,summary:`法律初学者の社会人が民法総則を3週間で取得した記録。最初は教科書を順に読んで詰まりましたが、設題集から逆算する方法に切り替えて成功しました。`,difficulty:3,durationWeeks:3,durationHours:30,methodType:`report_exam`,obtainedYear:2025,outcome:`obtained`,authorName:`サンプル太郎`,authorAvatar:`太`,authorMeta:`法政通信 法学部 4年`,steps:[{title:`設題集を最初に読む（30分）`,body:`設題から逆算して、教科書のどこを重点的に読むか決める。これをやらないと教科書全部読みになる。`,tips:`初学者ほど教科書を順に読みたくなるが、それは罠。`},{title:`指定章だけ精読（10時間）`,body:`設題に対応する3〜4章だけを読む。知らない用語は必ずメモ。`,tips:`全体像は最後に掴めば良い。`},{title:`設題のレポート初稿（4時間）`,body:`法律の三段論法（規範→当てはめ→結論）の型に合わせる。教科書の言い回しを引用しながら。`,tips:`型に当てはめる練習。最初は不格好でいい。`},{title:`AIで校正（30分）`,body:`文法ミスのみAI、内容は自分で。代筆させない（学術不正回避）。`,tips:`AIは「文章の整え役」と割り切る。`},{title:`試験対策（10時間）`,body:`過去の出題傾向を先輩から聞く。主要論点5つを暗記。論文形式の答案を3本書いて練習。`,tips:`答案を書く練習をしないと本番で時間切れになる。`}],tools:[{name:`教科書（指定）`,note:`これは必須。新品でなくても可。`},{name:`Claude（AI）`,note:`文章校正のみ。論述の代筆はNG。`},{name:`先輩の過去問メモ`,note:`コミュニティで共有してくれる人がいた。`}],pitfalls:[{situation:`教科書を最初から読んで2週間ロス`,solution:`設題集から逆算して必要な章だけ読む。`},{situation:`錯誤と詐欺の違いがわからない`,solution:`比較表を自作して整理。`},{situation:`試験で時間配分ミス`,solution:`時計を毎回確認、各問の配分を最初に決める。`}]},{id:`r2`,isSample:!0,universitySlug:`hosei-correspondence`,universityShort:`法政通信`,faculty:`法学部`,subjectName:`憲法`,title:`憲法（人権編）を1ヶ月で取った社会人の戦略`,summary:`判例を覚えるのが苦手な社会人が、判例カードを自作して暗記した記録。`,difficulty:4,durationWeeks:4,durationHours:40,methodType:`report_exam`,obtainedYear:2025,outcome:`obtained`,authorName:`サンプル花子`,authorAvatar:`花`,authorMeta:`法政通信 法学部 3年`,steps:[{title:`判例カード自作`,body:`主要判例30個をAnkiで暗記`,tips:`通勤時間に。`},{title:`設題のキーワード抽出`,body:`設題の文言から条文をマッピング`,tips:``}],tools:[{name:`Anki`,note:`暗記カードアプリ`}],pitfalls:[]},{id:`r3`,isSample:!0,universitySlug:`hosei-correspondence`,universityShort:`法政通信`,faculty:`法学部`,subjectName:`行政法II`,title:`行政法II、最初は失敗→2回目で取得した話`,summary:`1回目は試験対策不足で不合格。何が悪かったかを分析して2回目で合格。`,difficulty:4,durationWeeks:8,durationHours:50,methodType:`report_exam`,obtainedYear:2025,outcome:`obtained`,authorName:`サンプル次郎`,authorAvatar:`次`,authorMeta:`法政通信 法学部 3年`,steps:[{title:`失敗から学んだこと`,body:`範囲が広すぎて表面的にしか勉強しなかった`,tips:``}],tools:[],pitfalls:[]},{id:`r4`,isSample:!0,universitySlug:`open-university-japan`,universityShort:`放送大学`,faculty:`教養学部`,subjectName:`心理学概論`,title:`放送大学・心理学概論を放送授業だけで取った方法`,summary:`通勤時間とスキマ時間で放送授業を消化、過去問演習で2週間で取得。`,difficulty:2,durationWeeks:2,durationHours:15,methodType:`media`,obtainedYear:2024,outcome:`obtained`,authorName:`サンプル一郎`,authorAvatar:`一`,authorMeta:`放送大学 教養学部 2年`,steps:[],tools:[],pitfalls:[]}],a=e=>String(e??``).replaceAll(`&`,`&amp;`).replaceAll(`<`,`&lt;`).replaceAll(`>`,`&gt;`).replaceAll(`"`,`&quot;`).replaceAll(`'`,`&#39;`),o=e=>{let t=Math.max(0,Math.min(5,Number(e)||0)),n=`<span class="difficulty">`;for(let e=0;e<5;e++)n+=`<span class="${e<t?`filled`:`empty`}">★</span>`;return n+`</span>`},s=e=>e===`obtained`?`取得`:e===`failed`?`失敗`:e===`in_progress`?`進行中`:e,c=e=>{switch(e){case`exam_only`:return`試験のみ`;case`report_exam`:return`レポート + 試験`;case`schooling`:return`スクーリング`;case`media`:return`メディア授業`;default:return e||`その他`}},l=e=>`
<a class="recipe-card" href="#/r/${a(e.id)}">
  <div class="meta-row">
    <span class="uni">${a(e.universityShort)}</span>
    <span>${a(e.subjectName)}</span>
    ${e.isSample?`<span class="sample-badge">サンプル</span>`:``}
  </div>
  <h3>${a(e.title)}</h3>
  <p class="summary">${a(e.summary||``)}</p>
  <div class="stats">
    ${o(e.difficulty)}
    <span>${a(e.durationWeeks)} 週間</span>
    <span class="outcome-badge outcome-${a(e.outcome)}">${a(s(e.outcome))}</span>
  </div>
</a>
`,u=()=>{let e=n.reduce((e,t)=>(e[t.slug]=i.filter(e=>e.universitySlug===t.slug).length,e),{}),t=[...i].sort((e,t)=>t.difficulty-e.difficulty);return`
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
    ${n.map(t=>`
      <a class="uni-card" href="#/u/${a(t.slug)}">
        ${a(t.short)}
        <span class="uni-count">${e[t.slug]||0} レシピ</span>
      </a>`).join(``)}
  </div>
</section>

<section class="section">
  <div class="section-title">
    <h2>最新の単位取得レシピ</h2>
  </div>
  <div class="recipe-grid">
    ${t.map(l).join(``)}
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
`},d=e=>{let t=i.find(t=>t.id===e);return t?`
<a class="detail-back" href="#/">← 戻る</a>

<div class="detail-header">
  <div class="breadcrumb">${a(t.universityShort)} / ${a(t.faculty||``)} / ${a(t.subjectName)}</div>
  <h1>${a(t.title)} ${t.isSample?`<span class="sample-badge">サンプル</span>`:``}</h1>
  <div class="meta-pills">
    <span class="pill">${o(t.difficulty)} 難易度</span>
    <span class="pill">${a(t.durationWeeks)} 週間 / ${a(t.durationHours)} h</span>
    <span class="pill">${a(c(t.methodType))}</span>
    <span class="pill outcome-${a(t.outcome)}">${a(s(t.outcome))}</span>
    <span class="pill">${a(t.obtainedYear)}年度</span>
  </div>
</div>

<div class="detail-author">
  <div class="avatar">${a(t.authorAvatar||t.authorName?.[0]||`?`)}</div>
  <div class="info">
    <div class="name">${a(t.authorName)}</div>
    <div class="sub">${a(t.authorMeta||``)}</div>
  </div>
</div>

${t.summary?`<div class="detail-section">
        <h2>サマリ</h2>
        <p>${a(t.summary)}</p>
      </div>`:``}

${t.steps&&t.steps.length?`<div class="detail-section">
        <h2>取得ステップ</h2>
        <div class="steps">
          ${t.steps.map((e,t)=>`
            <div class="step">
              <div class="step-num">${t+1}</div>
              <div class="step-title">${a(e.title)}</div>
              <div class="step-body">${a(e.body||``)}</div>
              ${e.tips?`<div class="step-tips"><strong>ヒント：</strong>${a(e.tips)}</div>`:``}
            </div>`).join(``)}
        </div>
      </div>`:``}

${t.tools&&t.tools.length?`<div class="detail-section">
        <h2>使った道具</h2>
        <div class="tools-list">
          ${t.tools.map(e=>`
            <div class="item">
              <div class="name">${a(e.name)}</div>
              ${e.note?`<div class="note">${a(e.note)}</div>`:``}
            </div>`).join(``)}
        </div>
      </div>`:``}

${t.pitfalls&&t.pitfalls.length?`<div class="detail-section">
        <h2>つまずきポイント</h2>
        <div class="pitfalls-list">
          ${t.pitfalls.map(e=>`
            <div class="item">
              <div class="situation">${a(e.situation)}</div>
              <div class="solution">→ ${a(e.solution)}</div>
            </div>`).join(``)}
        </div>
      </div>`:``}

<div class="actions">
  <button onclick="alert('α版のため、つくれぽ機能は未実装です')">私もこれで取得した</button>
  <button onclick="alert('α版のため、ブックマーク機能は未実装です')">ブックマーク</button>
  <button class="primary" onclick="alert('α版のため、投稿機能は未実装です')">私も書く</button>
</div>
`:f()},f=()=>`
<section class="hero">
  <h1>レシピが見つかりません</h1>
  <p>削除されたか、URL が間違っている可能性があります。</p>
  <p style="margin-top:24px;"><a href="#/" style="color:var(--accent);font-weight:700;">ホームに戻る →</a></p>
</section>
`,p=e=>{let t=n.find(t=>t.slug===e);if(!t)return f();let o=i.filter(t=>t.universitySlug===e),s=r.filter(t=>t.universitySlug===e),c={};s.forEach(e=>{c[e.name]=c[e.name]||e});let u=s.map(e=>({...e,count:o.filter(t=>t.subjectName===e.name).length}));return`
<a class="detail-back" href="#/">← 大学一覧</a>

<section class="hero">
  <h1>${a(t.name)}</h1>
  <p>${o.length} 件のレシピ / ${s.length} 科目</p>
</section>

<section class="section">
  <div class="section-title">
    <h2>科目</h2>
  </div>
  <div class="uni-list">
    ${u.map(e=>`
      <div class="uni-card">
        ${a(e.name)}
        <span class="uni-count">${e.count} レシピ${e.count===0?`（未投稿）`:``}</span>
      </div>`).join(``)}
  </div>
</section>

<section class="section">
  <div class="section-title">
    <h2>レシピ</h2>
  </div>
  <div class="recipe-grid">
    ${o.length?o.map(l).join(``):`<div class="empty"><strong>まだレシピがありません</strong>あなたが最初の投稿者になりませんか</div>`}
  </div>
</section>
`},m=()=>`
<a class="detail-back" href="#/">← 戻る</a>
<section class="hero">
  <h1>レシピを投稿する</h1>
  <p>α版のため、投稿フォームは未実装です。<br>朝、<code>docs/SEED_RECIPES.md</code> のテンプレに沿って手書きで5本書いてみてください。</p>
  <p style="margin-top:24px;font-size:13px;color:var(--muted);">手書き 5 本のあとに、ここに本物の投稿フォームを実装します。</p>
</section>
`,h=[{match:/^\/?$/,render:()=>u()},{match:/^\/r\/(.+)$/,render:e=>d(e[1])},{match:/^\/u\/([^/]+)$/,render:e=>p(e[1])},{match:/^\/new$/,render:()=>m()}],g=e=>{for(let t of h){let n=e.match(t.match);if(n)return t.render(n)}return f()},_=()=>(window.location.hash||`#/`).replace(/^#/,``)||`/`,v=document.getElementById(`app`),y=()=>{v.innerHTML=`
    ${e()}
    <main>${g(_())}</main>
    ${t()}
  `,window.scrollTo(0,0)};window.addEventListener(`hashchange`,y),window.addEventListener(`DOMContentLoaded`,y),y();
//# sourceMappingURL=index-DP7HvsFC.js.map