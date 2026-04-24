/**
 * Remotion エントリーポイント。
 * `npx remotion studio` or `npx remotion render` で使用される。
 */
import {registerRoot} from "remotion";
import {RemotionRoot} from "./Root";

registerRoot(RemotionRoot);
