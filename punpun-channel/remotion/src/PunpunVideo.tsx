/**
 * ぷんぷん動画のメインコンポジション。
 * 台本の各シーンを Sequence で並べて時系列で再生する。
 */
import React from "react";
import {AbsoluteFill, Sequence, useVideoConfig} from "remotion";
import {z} from "zod";
import {Scene, sceneSchema} from "./components/Scene";

export const videoSchema = z.object({
  topic: z.string(),
  title: z.string(),
  scenes: z.array(sceneSchema),
});

type VideoProps = z.infer<typeof videoSchema>;

export const PunpunVideo: React.FC<VideoProps> = ({script}: any) => {
  const {fps} = useVideoConfig();
  const scenes = script?.scenes ?? [];

  let cursorFrame = 0;
  return (
    <AbsoluteFill style={{backgroundColor: "#f5f0e8"}}>
      {scenes.map((scene: any, idx: number) => {
        const durSec = scene.duration_seconds ?? scene.text.length * 0.12 + 0.5;
        const durFrames = Math.ceil(durSec * fps);
        const startFrame = cursorFrame;
        cursorFrame += durFrames;

        return (
          <Sequence
            key={idx}
            from={startFrame}
            durationInFrames={durFrames}
            layout="none"
          >
            <Scene scene={scene} durationInFrames={durFrames} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
