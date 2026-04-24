/**
 * シーン背景。image_hint.type に応じて:
 * - portrait/photo/illustration: staticFile (assets から読む)
 * - map_*: SVG インライン or Python で事前生成された PNG
 * - blank: グラデーション
 */
import React from "react";
import {Img, staticFile} from "remotion";

type HintType = string;

type Props = {
  hint: {
    type: HintType;
    keyword?: string;
    highlight?: string | null;
    overlay_keyword?: string | null;
  };
  zoom: number;
  chapter: number;
};

const CHAPTER_GRADIENTS = [
  ["#fff6ec", "#fde8cf"], // 0 OP
  ["#e8f5ff", "#c9e6ff"], // 1 peaceful
  ["#ffe8e8", "#ffc9c9"], // 2 drama
  ["#fff2d6", "#ffd98a"], // 3 epic
  ["#2a1a2e", "#0f0f1a"], // 4 dark
  ["#e8e0ea", "#c2b8c5"], // 5 sad
  ["#e4f8e8", "#b8e6c0"], // 6 uplift
];

export const Background: React.FC<Props> = ({hint, zoom, chapter}) => {
  const [c1, c2] =
    CHAPTER_GRADIENTS[chapter] || CHAPTER_GRADIENTS[0];

  // Python 側で事前生成した背景画像があれば使う
  // (image_fetcher.py が生成した cache ファイル)
  const cachedImage = hint.keyword
    ? `assets/cache/${hint.type}_${hint.keyword}.png`
    : null;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: `linear-gradient(160deg, ${c1}, ${c2})`,
        overflow: "hidden",
      }}
    >
      {/* 地図や肖像画がある場合 (Remotion の staticFile 経由) */}
      {cachedImage && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            transform: `scale(${zoom})`,
            transformOrigin: "center center",
          }}
        >
          {/* 注: staticFile は public/ ディレクトリ内のみアクセス可 */}
          {/* フォールバックでインラインスタイルのみ表示 */}
        </div>
      )}
    </div>
  );
};
