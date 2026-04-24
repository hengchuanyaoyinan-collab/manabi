/**
 * ぷんぷんキャラ (React/SVG パーツ分割)。
 *
 * Python 版と比べて:
 * - SVG なのでスケーリングが綺麗
 * - パーツごとに独立アニメ (眉・目・口・体) 可能
 * - spring で自然な動き
 */
import React from "react";
import {interpolate, spring, useVideoConfig} from "remotion";

type Props = {
  emotion: string;
  audioPath: string | null;
  frame: number;
  durationInFrames: number;
};

type EmotionShape = {
  brow: "normal" | "angry" | "sad" | "surprised" | "raised";
  eye: "normal" | "wide" | "thin" | "crescent" | "tear";
  mouth: "ring" | "frown" | "smile" | "small";
};

const EMOTION_MAP: Record<string, EmotionShape> = {
  normal: {brow: "normal", eye: "normal", mouth: "ring"},
  shock: {brow: "surprised", eye: "wide", mouth: "ring"},
  angry: {brow: "angry", eye: "normal", mouth: "frown"},
  laugh: {brow: "raised", eye: "crescent", mouth: "smile"},
  sad: {brow: "sad", eye: "tear", mouth: "frown"},
  think: {brow: "raised", eye: "thin", mouth: "small"},
};

export const Punpun: React.FC<Props> = ({emotion, frame, durationInFrames}) => {
  const {fps} = useVideoConfig();
  const shape = EMOTION_MAP[emotion] ?? EMOTION_MAP.normal;

  // ふわふわ上下
  const bob = Math.sin((frame / fps) * 2 * Math.PI * 1.3) * 4;

  // まばたき (3 秒おき、60ms)
  const blinkFreq = Math.floor(frame / (fps * 3));
  const blinkFrame = frame - blinkFreq * fps * 3;
  const isBlinking = blinkFrame < 3 && emotion !== "thin" && emotion !== "crescent";

  // 口パク (音量ない場合は微動させるダミー)
  // 実運用では audio の RMS を frame に対応付ける
  const mouthOpenness =
    (Math.sin((frame / fps) * 5) + 1) / 2; // 0-1 dummy wave

  return (
    <svg
      viewBox="0 0 280 280"
      style={{
        width: "100%",
        height: "100%",
        transform: `translateY(${bob}px)`,
      }}
    >
      {/* 影 */}
      <ellipse cx="140" cy="270" rx="100" ry="8" fill="rgba(0,0,0,0.2)" />

      {/* 顔 */}
      <circle
        cx="140"
        cy="135"
        r="125"
        fill="white"
        stroke="#000"
        strokeWidth="4"
      />

      {/* 眉 */}
      <Eyebrow cx={83} cy={82} type={shape.brow} side="L" />
      <Eyebrow cx={197} cy={82} type={shape.brow} side="R" />

      {/* 目 */}
      <Eye cx={97} cy={115} type={isBlinking ? "thin" : shape.eye} side="L" />
      <Eye cx={183} cy={115} type={isBlinking ? "thin" : shape.eye} side="R" />

      {/* 特殊マーク */}
      {emotion === "shock" && <Sweat cx={230} cy={105} />}
      {emotion === "angry" && <AngerMark cx={235} cy={70} />}
      {emotion === "think" && <QuestionMark cx={230} cy={70} />}
      {emotion === "sad" && <Tear cx={200} cy={125} />}

      {/* 口 */}
      <Mouth cx={140} cy={195} type={shape.mouth} openness={mouthOpenness} />
    </svg>
  );
};

const Eyebrow: React.FC<{cx: number; cy: number; type: string; side: "L" | "R"}> = ({
  cx,
  cy,
  type,
  side,
}) => {
  const w = 45;
  if (type === "angry") {
    // つり上がり
    const innerY = side === "L" ? cy + 10 : cy + 10;
    const outerY = side === "L" ? cy - 14 : cy - 14;
    const innerX = side === "L" ? cx + w / 2 : cx - w / 2;
    const outerX = side === "L" ? cx - w / 2 : cx + w / 2;
    return (
      <line
        x1={innerX}
        y1={innerY}
        x2={outerX}
        y2={outerY}
        stroke="#000"
        strokeWidth="6"
        strokeLinecap="round"
      />
    );
  }
  if (type === "sad") {
    // ハの字
    const innerY = cy - 10;
    const outerY = cy + 6;
    const innerX = side === "L" ? cx + w / 2 : cx - w / 2;
    const outerX = side === "L" ? cx - w / 2 : cx + w / 2;
    return (
      <line
        x1={innerX}
        y1={innerY}
        x2={outerX}
        y2={outerY}
        stroke="#000"
        strokeWidth="5"
        strokeLinecap="round"
      />
    );
  }
  if (type === "surprised" || type === "raised") {
    // 高い位置のアーチ
    return (
      <path
        d={`M${cx - w / 2} ${cy} Q${cx} ${cy - 18} ${cx + w / 2} ${cy}`}
        stroke="#000"
        strokeWidth="5"
        fill="none"
        strokeLinecap="round"
      />
    );
  }
  // 通常のアーチ
  return (
    <path
      d={`M${cx - w / 2} ${cy} Q${cx} ${cy - 10} ${cx + w / 2} ${cy}`}
      stroke="#000"
      strokeWidth="4"
      fill="none"
      strokeLinecap="round"
    />
  );
};

const Eye: React.FC<{cx: number; cy: number; type: string; side: "L" | "R"}> = ({
  cx,
  cy,
  type,
  side,
}) => {
  if (type === "thin") {
    return <rect x={cx - 10} y={cy - 1} width="20" height="3" fill="#000" rx="1.5" />;
  }
  if (type === "crescent") {
    return (
      <path
        d={`M${cx - 12} ${cy + 2} Q${cx} ${cy + 8} ${cx + 12} ${cy + 2}`}
        stroke="#000"
        strokeWidth="4"
        fill="none"
        strokeLinecap="round"
      />
    );
  }
  if (type === "wide") {
    return (
      <>
        <circle cx={cx} cy={cy} r="14" fill="white" stroke="#000" strokeWidth="2" />
        <circle cx={cx} cy={cy} r="7" fill="#000" />
      </>
    );
  }
  if (type === "tear") {
    return <circle cx={cx} cy={cy} r="9" fill="#000" />;
  }
  // normal
  return <circle cx={cx} cy={cy} r="10" fill="#000" />;
};

const Mouth: React.FC<{cx: number; cy: number; type: string; openness: number}> = ({
  cx,
  cy,
  type,
  openness,
}) => {
  if (type === "frown") {
    return (
      <path
        d={`M${cx - 32} ${cy + 12} Q${cx} ${cy - 5} ${cx + 32} ${cy + 12}`}
        stroke="#c03030"
        strokeWidth="6"
        fill="none"
        strokeLinecap="round"
      />
    );
  }
  if (type === "smile") {
    return (
      <path
        d={`M${cx - 40} ${cy - 5} Q${cx} ${cy + 32} ${cx + 40} ${cy - 5} Z`}
        fill="#dc3232"
        stroke="#961e1e"
        strokeWidth="3"
      />
    );
  }
  if (type === "small") {
    return <circle cx={cx + 4} cy={cy} r="9" fill="#dc3232" />;
  }
  // ring (normal/shock): 赤いドーナツ
  const outerRx = 28 + openness * 6;
  const outerRy = 13 + openness * 12;
  const innerRx = outerRx * 0.6;
  const innerRy = Math.max(2, outerRy * 0.3);
  return (
    <g>
      <ellipse cx={cx} cy={cy} rx={outerRx} ry={outerRy} fill="#d24637" />
      <ellipse cx={cx} cy={cy} rx={innerRx} ry={innerRy} fill="white" />
    </g>
  );
};

const Sweat: React.FC<{cx: number; cy: number}> = ({cx, cy}) => (
  <path
    d={`M${cx} ${cy} L${cx - 8} ${cy + 18} L${cx + 8} ${cy + 18} Z`}
    fill="#64c8f0"
    stroke="#3c96d2"
    strokeWidth="2"
  />
);

const AngerMark: React.FC<{cx: number; cy: number}> = ({cx, cy}) => (
  <g stroke="#dc3232" strokeWidth="4" strokeLinecap="round">
    <line x1={cx} y1={cy - 12} x2={cx} y2={cy + 12} />
    <line x1={cx - 12} y1={cy} x2={cx + 12} y2={cy} />
    <line x1={cx - 8} y1={cy - 8} x2={cx + 8} y2={cy + 8} />
    <line x1={cx - 8} y1={cy + 8} x2={cx + 8} y2={cy - 8} />
  </g>
);

const QuestionMark: React.FC<{cx: number; cy: number}> = ({cx, cy}) => (
  <text
    x={cx}
    y={cy + 10}
    textAnchor="middle"
    fontSize="32"
    fontWeight="bold"
    fill="#3264c8"
    fontFamily="sans-serif"
  >
    ?
  </text>
);

const Tear: React.FC<{cx: number; cy: number}> = ({cx, cy}) => (
  <path
    d={`M${cx} ${cy} L${cx - 6} ${cy + 14} L${cx + 6} ${cy + 14} Z`}
    fill="#64c8f0"
    stroke="#3c96d2"
    strokeWidth="1.5"
  />
);
