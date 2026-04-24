"""パイプライン全体を実行するオーケストレータ。

毎日 19:00 にこのスクリプトが起動 (Windows タスクスケジューラ等) して、
1 本動画を生成してアップロードする。

使い方:
    # 次の題材を自動選定して本番投稿
    python3 src/orchestrator.py

    # 題材を指定してテストモード
    python3 src/orchestrator.py --topic "エリザベート・バートリ" --test

    # 既存の台本 JSON から動画だけ作る
    python3 src/orchestrator.py --script output/script.json --test

    # 投稿時刻指定 (ISO8601)
    python3 src/orchestrator.py --publish-at 2026-04-23T19:00:00+09:00
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

# プロジェクトルートを sys.path に追加 (どこから呼んでも src.* を import できるように)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.config import OUTPUT_DIR, channel_config
from src.generator import topic_selector
from src.generator.script_generator import generate_script, load_script
from src.models import VideoScript
from src.video.animation import render_animated_video
from src.video.assembler import assemble_video, render_scene_image
from src.video.image_fetcher import fetch_for_hint
from src.video.thumbnail_generator import generate_thumbnail
from src.voice.synth import concatenate_audio, synthesize_script
from src.notify.discord import notify_success, notify_error
try:
    from src.audio.mixer import build_final_audio
except ImportError:
    build_final_audio = None  # type: ignore

logger = logging.getLogger("punpun")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def run_pipeline(
    *,
    topic: str | None = None,
    script_path: Path | None = None,
    test_mode: bool = True,
    publish_at: str | None = None,
    use_voicevox: bool = True,
    animate: bool = True,
    fps: int = 24,
    parallel: int = 3,
) -> dict:
    """1 本のパイプライン実行。
    返り値はレポート (生成物のパス、所要時間、エラー等)。
    """
    started = datetime.now()
    report: dict = {
        "started": started.isoformat(),
        "test_mode": test_mode,
        "stages": {},
        "errors": [],
    }

    today = started.strftime("%Y-%m-%d_%H%M%S")
    work_dir = OUTPUT_DIR / ("test" if test_mode else "production") / today
    work_dir.mkdir(parents=True, exist_ok=True)
    report["work_dir"] = str(work_dir)

    # --- 1. 題材選定 / 台本ロード ---------------------------------------
    try:
        if script_path:
            logger.info(f"Loading script from {script_path}")
            script: VideoScript = load_script(script_path)
            topic = script.topic
        else:
            if not topic:
                next_topic = topic_selector.pop_next()
                if not next_topic:
                    raise RuntimeError("題材キューが空です。config/topic-queue.json に追加してください。")
                topic = next_topic["topic"]
            logger.info(f"Generating script for: {topic}")
            script = generate_script(
                topic,
                save_to=work_dir / "script.json",
            )
        report["topic"] = topic
        report["title"] = script.title
        report["scenes"] = len(script.scenes)
        report["stages"]["script"] = "ok"
    except Exception as e:
        report["errors"].append({"stage": "script", "error": str(e)})
        report["stages"]["script"] = "failed"
        return report

    # --- 2. 音声合成 -----------------------------------------------------
    try:
        logger.info("Synthesizing audio...")
        synthesize_script(script, work_dir / "audio", use_voicevox=use_voicevox)
        narration = concatenate_audio(script, work_dir / "narration.wav")

        # BGM / SE ミックス (assets に BGM があれば自動で適用)
        if build_final_audio is not None:
            try:
                final_audio = build_final_audio(
                    script, narration, work_dir / "narration_mixed.m4a",
                    topic=report.get("topic", ""),
                )
                narration = final_audio
                report["bgm_mixed"] = True
                logger.info("BGM/SE mixed into narration")
            except Exception as e:
                logger.warning(f"BGM mix skipped: {e}")
                report["bgm_mixed"] = False

        report["stages"]["audio"] = "ok"
        report["narration"] = str(narration)
        report["total_duration"] = script.total_duration()
    except Exception as e:
        report["errors"].append({"stage": "audio", "error": str(e), "trace": traceback.format_exc()})
        report["stages"]["audio"] = "failed"
        return report

    # --- 3. 画像取得 -----------------------------------------------------
    try:
        logger.info("Fetching background images...")
        from PIL import Image as _PIL
        backgrounds: list = []
        scene_images: list[Path] = []
        for scene in script.scenes:
            bg_path = fetch_for_hint(scene.image_hint)
            backgrounds.append(_PIL.open(bg_path).convert("RGBA"))
            # 従来互換: 静止画も 1 枚書き出しておく (サムネ等で使う)
            scene_img = render_scene_image(
                bg_path, scene.text, work_dir / "scenes" / f"scene_{scene.index:04d}.png"
            )
            scene_images.append(scene_img)
        report["stages"]["scenes"] = "ok"
        report["scene_images"] = len(scene_images)
    except Exception as e:
        report["errors"].append({"stage": "scenes", "error": str(e), "trace": traceback.format_exc()})
        report["stages"]["scenes"] = "failed"
        return report

    # --- 4. 動画アセンブル ---------------------------------------------
    try:
        if animate:
            logger.info(f"Assembling ANIMATED video (fps={fps}, parallel={parallel})...")
            video_path = render_animated_video(
                script, backgrounds, work_dir / "video.mp4",
                work_dir=work_dir / "_anim_work",
                fps=fps,
                parallel=parallel,
            )
        else:
            logger.info("Assembling static video...")
            video_path = assemble_video(
                script, scene_images, narration, work_dir / "video.mp4"
            )

        # BGM がミックスされていれば、動画の音声トラックを差し替え
        if report.get("bgm_mixed") and narration.suffix.lower() != ".wav":
            logger.info("Replacing video audio with BGM-mixed track...")
            mixed_out = work_dir / "video_with_bgm.mp4"
            import subprocess as _sp
            _sp.run(
                ["ffmpeg", "-y",
                 "-i", str(video_path),
                 "-i", str(narration),
                 "-c:v", "copy",
                 "-c:a", "aac", "-b:a", "192k",
                 "-map", "0:v:0", "-map", "1:a:0",
                 "-shortest",
                 str(mixed_out)],
                check=True, capture_output=True,
            )
            video_path = mixed_out

        report["stages"]["video"] = "ok"
        report["video"] = str(video_path)
    except Exception as e:
        report["errors"].append({"stage": "video", "error": str(e), "trace": traceback.format_exc()})
        report["stages"]["video"] = "failed"
        return report

    # --- 5. サムネ生成 -------------------------------------------------
    try:
        logger.info("Generating thumbnail...")
        # 主役の肖像画を背景に使う (1 シーン目は OP で雑然としているので避ける)
        thumb_bg = None
        for scene in script.scenes:
            if scene.image_hint.type.value in ("portrait", "photo"):
                thumb_bg = fetch_for_hint(scene.image_hint)
                break
        thumbnail = generate_thumbnail(
            script.thumbnail_text, thumb_bg, work_dir / "thumbnail.png"
        )
        report["stages"]["thumbnail"] = "ok"
        report["thumbnail"] = str(thumbnail)
    except Exception as e:
        report["errors"].append({"stage": "thumbnail", "error": str(e)})
        report["stages"]["thumbnail"] = "failed"

    # --- 6. アップロード -----------------------------------------------
    if not test_mode:
        try:
            from src.upload.upload_video import upload_to_youtube
            video_id = upload_to_youtube(
                script, video_path,
                thumbnail_path=Path(report.get("thumbnail")) if report.get("thumbnail") else None,
                publish_at_iso=publish_at,
                test_mode=False,
            )
            report["video_id"] = video_id
            report["stages"]["upload"] = "ok"
            topic_selector.mark_posted(script.topic, video_id=video_id)
        except Exception as e:
            report["errors"].append({"stage": "upload", "error": str(e), "trace": traceback.format_exc()})
            report["stages"]["upload"] = "failed"
    else:
        report["stages"]["upload"] = "skipped (test mode)"

    finished = datetime.now()
    report["finished"] = finished.isoformat()
    report["elapsed_seconds"] = (finished - started).total_seconds()

    # レポート保存
    (work_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(f"✅ Done. {work_dir}/report.json")

    # Discord 通知
    try:
        if report["errors"]:
            err = report["errors"][0]
            notify_error(
                stage=err["stage"],
                detail=err.get("error", "unknown"),
                topic=report.get("topic"),
            )
        else:
            video_url = None
            if report.get("video_id"):
                video_url = f"https://www.youtube.com/watch?v={report['video_id']}"
            notify_success(
                message="動画パイプラインが完了しました",
                video_url=video_url,
                title=report.get("title"),
                duration_sec=report.get("total_duration"),
                scene_count=report.get("scenes"),
            )
    except Exception:
        pass

    return report


def main() -> int:
    p = argparse.ArgumentParser(description="ぷんぷんチャンネル動画生成パイプライン")
    p.add_argument("--topic", help="題材を指定 (なければキューから自動選定)")
    p.add_argument("--script", help="既存の台本 JSON から動画だけ作る")
    p.add_argument("--test", action="store_true", help="アップロードしない")
    p.add_argument("--no-voicevox", action="store_true", help="open-jtalk を使う (テスト用)")
    p.add_argument("--no-animate", action="store_true", help="静止画動画にする (高速)")
    p.add_argument("--fps", type=int, default=24, help="動画の fps (デフォ 24、速度優先なら 15)")
    p.add_argument("--parallel", type=int, default=3, help="並列レンダリングのワーカー数")
    p.add_argument("--publish-at", help="公開時刻 (ISO8601)")
    args = p.parse_args()

    report = run_pipeline(
        topic=args.topic,
        script_path=Path(args.script) if args.script else None,
        test_mode=args.test or bool(args.script),
        publish_at=args.publish_at,
        use_voicevox=not args.no_voicevox,
        animate=not args.no_animate,
        fps=args.fps,
        parallel=args.parallel,
    )
    if report["errors"]:
        for err in report["errors"]:
            print(f"❌ [{err['stage']}] {err['error']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
