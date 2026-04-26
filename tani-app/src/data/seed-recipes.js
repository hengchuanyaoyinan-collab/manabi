// シードデータ（=見本）。
// 本物の投稿が貯まるまでのプレースホルダー。
// すべて isSample: true でマークしているので、
// UI に「サンプル」バッジを出して、実投稿と区別する。

export const universities = [
  { slug: 'hosei-correspondence', name: '法政大学通信教育部', short: '法政通信' },
  { slug: 'open-university-japan', name: '放送大学', short: '放送大学' },
  { slug: 'keio-correspondence', name: '慶應義塾大学通信教育課程', short: '慶應通信' },
  { slug: 'nihon-correspondence', name: '日本大学通信教育部', short: '日大通信' }
];

export const subjects = [
  { id: 's1', universitySlug: 'hosei-correspondence', faculty: '法学部', name: '民法総則', credits: 4 },
  { id: 's2', universitySlug: 'hosei-correspondence', faculty: '法学部', name: '憲法', credits: 4 },
  { id: 's3', universitySlug: 'hosei-correspondence', faculty: '法学部', name: '行政法II', credits: 4 },
  { id: 's4', universitySlug: 'open-university-japan', faculty: '教養学部', name: '心理学概論', credits: 2 }
];

export const recipes = [
  {
    id: 'r1',
    isSample: true,
    universitySlug: 'hosei-correspondence',
    universityShort: '法政通信',
    faculty: '法学部',
    subjectName: '民法総則',
    title: '民法総則を3週間で取った方法（社会人・働きながら）',
    summary: '法律初学者の社会人が民法総則を3週間で取得した記録。最初は教科書を順に読んで詰まりましたが、設題集から逆算する方法に切り替えて成功しました。',
    difficulty: 3,
    durationWeeks: 3,
    durationHours: 30,
    methodType: 'report_exam',
    obtainedYear: 2025,
    outcome: 'obtained',
    authorName: 'サンプル太郎',
    authorAvatar: '太',
    authorMeta: '法政通信 法学部 4年',
    steps: [
      {
        title: '設題集を最初に読む（30分）',
        body: '設題から逆算して、教科書のどこを重点的に読むか決める。これをやらないと教科書全部読みになる。',
        tips: '初学者ほど教科書を順に読みたくなるが、それは罠。'
      },
      {
        title: '指定章だけ精読（10時間）',
        body: '設題に対応する3〜4章だけを読む。知らない用語は必ずメモ。',
        tips: '全体像は最後に掴めば良い。'
      },
      {
        title: '設題のレポート初稿（4時間）',
        body: '法律の三段論法（規範→当てはめ→結論）の型に合わせる。教科書の言い回しを引用しながら。',
        tips: '型に当てはめる練習。最初は不格好でいい。'
      },
      {
        title: 'AIで校正（30分）',
        body: '文法ミスのみAI、内容は自分で。代筆させない（学術不正回避）。',
        tips: 'AIは「文章の整え役」と割り切る。'
      },
      {
        title: '試験対策（10時間）',
        body: '過去の出題傾向を先輩から聞く。主要論点5つを暗記。論文形式の答案を3本書いて練習。',
        tips: '答案を書く練習をしないと本番で時間切れになる。'
      }
    ],
    tools: [
      { name: '教科書（指定）', note: 'これは必須。新品でなくても可。' },
      { name: 'Claude（AI）', note: '文章校正のみ。論述の代筆はNG。' },
      { name: '先輩の過去問メモ', note: 'コミュニティで共有してくれる人がいた。' }
    ],
    pitfalls: [
      { situation: '教科書を最初から読んで2週間ロス', solution: '設題集から逆算して必要な章だけ読む。' },
      { situation: '錯誤と詐欺の違いがわからない', solution: '比較表を自作して整理。' },
      { situation: '試験で時間配分ミス', solution: '時計を毎回確認、各問の配分を最初に決める。' }
    ]
  },
  {
    id: 'r2',
    isSample: true,
    universitySlug: 'hosei-correspondence',
    universityShort: '法政通信',
    faculty: '法学部',
    subjectName: '憲法',
    title: '憲法（人権編）を1ヶ月で取った社会人の戦略',
    summary: '判例を覚えるのが苦手な社会人が、判例カードを自作して暗記した記録。',
    difficulty: 4,
    durationWeeks: 4,
    durationHours: 40,
    methodType: 'report_exam',
    obtainedYear: 2025,
    outcome: 'obtained',
    authorName: 'サンプル花子',
    authorAvatar: '花',
    authorMeta: '法政通信 法学部 3年',
    steps: [
      { title: '判例カード自作', body: '主要判例30個をAnkiで暗記', tips: '通勤時間に。' },
      { title: '設題のキーワード抽出', body: '設題の文言から条文をマッピング', tips: '' }
    ],
    tools: [
      { name: 'Anki', note: '暗記カードアプリ' }
    ],
    pitfalls: []
  },
  {
    id: 'r3',
    isSample: true,
    universitySlug: 'hosei-correspondence',
    universityShort: '法政通信',
    faculty: '法学部',
    subjectName: '行政法II',
    title: '行政法II、最初は失敗→2回目で取得した話',
    summary: '1回目は試験対策不足で不合格。何が悪かったかを分析して2回目で合格。',
    difficulty: 4,
    durationWeeks: 8,
    durationHours: 50,
    methodType: 'report_exam',
    obtainedYear: 2025,
    outcome: 'obtained',
    authorName: 'サンプル次郎',
    authorAvatar: '次',
    authorMeta: '法政通信 法学部 3年',
    steps: [
      { title: '失敗から学んだこと', body: '範囲が広すぎて表面的にしか勉強しなかった', tips: '' }
    ],
    tools: [],
    pitfalls: []
  },
  {
    id: 'r4',
    isSample: true,
    universitySlug: 'open-university-japan',
    universityShort: '放送大学',
    faculty: '教養学部',
    subjectName: '心理学概論',
    title: '放送大学・心理学概論を放送授業だけで取った方法',
    summary: '通勤時間とスキマ時間で放送授業を消化、過去問演習で2週間で取得。',
    difficulty: 2,
    durationWeeks: 2,
    durationHours: 15,
    methodType: 'media',
    obtainedYear: 2024,
    outcome: 'obtained',
    authorName: 'サンプル一郎',
    authorAvatar: '一',
    authorMeta: '放送大学 教養学部 2年',
    steps: [],
    tools: [],
    pitfalls: []
  }
];
