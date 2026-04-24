/**
 * Remotion ルート: コンポジション定義。
 *
 * 台本 JSON を読み込んで、各シーンから Remotion 動画を構築する。
 */
import React from "react";
import {Composition} from "remotion";
import {PunpunVideo, videoSchema} from "./PunpunVideo";
import scriptData from "../../test_data/chinghis_khan_v4.json";

const FPS = 30;
const WIDTH = 1920;
const HEIGHT = 1080;

/**
 * シーンごとの秒数を計算。Python 側で .duration_seconds が付与されてない場合は
 * テキスト長から推定 (1 文字 = 0.12 秒)。
 */
function computeDurationFrames(scenes: any[]): number {
  const totalSec = scenes.reduce((acc, s) => {
    const dur = s.duration_seconds ?? s.text.length * 0.12 + 0.5;
    return acc + dur;
  }, 0);
  return Math.ceil(totalSec * FPS);
}

export const RemotionRoot: React.FC = () => {
  const totalFrames = computeDurationFrames(scriptData.scenes);
  return (
    <>
      <Composition
        id="PunpunVideo"
        component={PunpunVideo}
        durationInFrames={totalFrames}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{
          script: scriptData as any,
        }}
        schema={videoSchema}
      />
    </>
  );
};
