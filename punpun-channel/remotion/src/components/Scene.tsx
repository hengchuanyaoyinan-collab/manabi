/**
 * 1 シーン分のコンポジション。
 * 背景 (Ken Burns) + 吹き出し (ポップイン) + ぷんぷん (感情 + 口パク) を重ねる。
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {z} from "zod";
import {Punpun} from "./Punpun";
import {SpeechBubble} from "./SpeechBubble";
import {Background} from "./Background";

export const sceneSchema = z.object({
  index: z.number(),
  chapter: z.number(),
  text: z.string(),
  emotion: z.string().default("normal"),
  image_hint: z.object({
    type: z.string(),
    keyword: z.string().optional().default(""),
    highlight: z.string().nullable().optional(),
    overlay_keyword: z.string().nullable().optional(),
  }),
  duration_seconds: z.number().nullable().optional(),
});

type SceneProps = {
  scene: z.infer<typeof sceneSchema>;
  durationInFrames: number;
};

export const Scene: React.FC<SceneProps> = ({scene, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // 頭尾のフェード
  const fadeInFrames = Math.min(6, durationInFrames);
  const fadeOutFrames = Math.min(4, durationInFrames);
  const opacity = interpolate(
    frame,
    [0, fadeInFrames, durationInFrames - fadeOutFrames, durationInFrames],
    [0, 1, 1, 0],
    {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
  );

  // 吹き出しのポップイン (spring)
  const bubbleScale = spring({
    frame,
    fps,
    from: 0.6,
    to: 1,
    durationInFrames: Math.min(12, durationInFrames),
    config: {damping: 12, stiffness: 150},
  });
  const bubbleOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Ken Burns (地図シーンは無効化)
  const isMap = scene.image_hint.type.startsWith("map_");
  const kenBurnsZoom = isMap
    ? 1
    : interpolate(frame, [0, durationInFrames], [1, 1.08]);

  return (
    <AbsoluteFill style={{opacity}}>
      <Background
        hint={scene.image_hint}
        zoom={kenBurnsZoom}
        chapter={scene.chapter}
      />

      {/* 吹き出し */}
      <div
        style={{
          position: "absolute",
          left: 80,
          bottom: 220,
          maxWidth: 1300,
          transform: `scale(${bubbleScale})`,
          opacity: bubbleOpacity,
          transformOrigin: "bottom left",
        }}
      >
        <SpeechBubble text={scene.text} />
      </div>

      {/* ぷんぷん */}
      <div
        style={{
          position: "absolute",
          right: 30,
          bottom: 30,
          width: 280,
          height: 280,
        }}
      >
        <Punpun
          emotion={scene.emotion || "normal"}
          audioPath={(scene as any).audio_path || null}
          frame={frame}
          durationInFrames={durationInFrames}
        />
      </div>
    </AbsoluteFill>
  );
};
