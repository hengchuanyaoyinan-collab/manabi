/**
 * 吹き出し。テキストが長い場合は自動折返し。
 * 手書き風のわずかに歪んだ枠線で紙芝居感を出す。
 */
import React from "react";

type Props = {
  text: string;
};

export const SpeechBubble: React.FC<Props> = ({text}) => {
  return (
    <div
      style={{
        position: "relative",
        background: "rgba(255,255,255,0.96)",
        border: "4px solid #000",
        borderRadius: 28,
        padding: "28px 38px",
        boxShadow: "4px 6px 0 rgba(0,0,0,0.15)",
        maxWidth: 1200,
        fontFamily: 'YuGothic, "Noto Sans JP", "Yu Gothic", "Hiragino Kaku Gothic ProN", sans-serif',
        fontSize: 56,
        fontWeight: 500,
        color: "#111",
        lineHeight: 1.5,
      }}
    >
      {text}
      {/* 尻尾 (右下に向けて) */}
      <svg
        viewBox="0 0 60 80"
        style={{
          position: "absolute",
          right: 40,
          bottom: -60,
          width: 60,
          height: 80,
          pointerEvents: "none",
        }}
      >
        <polygon points="0,0 50,70 40,5" fill="rgba(255,255,255,0.96)" stroke="#000" strokeWidth="4" strokeLinejoin="round" />
      </svg>
    </div>
  );
};
