# M1 video I/O: guarantees and limitations

`FrameStream` is a read-only OpenCV stream interface. Processing is blocked until external consent is affirmed unless an input is explicitly flagged as *synthetic*. It never saves image arrays. `tools/probe_video.py` prints **only** decoded-frame counts and gap counts. Since validated face-redaction has not been built, public image/video export is forbidden.

## Timestamp policy
- Offline frames use backend presentation timestamps (PTS, milliseconds) when present. When timestamps are missing, reported FPS or a supplied FPS fallback is used, and the frame is tagged `fps_fallback`.
- Variable frame rate is preserved only where the backend exposes PTS; otherwise timing is **estimated**, not guaranteed.
- Nonmonotonic source timestamps emit a `timestamp_regression` gap. Timing is conservatively repaired from FPS, or processing stops if no timebase is available.
- Large PTS differences relative to nominal FPS emit a `timestamp_jump` warning and estimated missing count. Legitimate VFR intervals can trigger it: do not label these as confirmed dropped frames.
- Live mode uses a relative monotonic process clock, because RTSP presentation timestamps can reset after reconnection.

## Streaming, interruption, and media
- Read frames one at a time; do not load the entire clip into memory.
- Offline read failures with remaining declared frames emit a decode-error gap and stop after bounded retries. Missing/incorrect frame-count metadata may make corruption indistinguishable from ordinary EOF.
- Live read failures emit disconnect gaps and reconnect with bounded exponential backoff, limited by a total reconnect budget. OpenCV backend socket stalls/timeouts are not guaranteed to be interruptible.
- Optional proportional resize and mirroring; orientation metadata auto-apply is requested via OpenCV but must be verified per phone/codec/backend. Audio tracks are ignored.

## Usage
`python tools/probe_video.py private_clip.mp4 --consent-confirmed --max-frames 100` handles a consented mock-shelf clip. Pass `--synthetic` only for generated media. A command-line flag is *not* proof of informed consent.

`python bench/bench_video.py --frames 30` synthesizes a tiny MJPG clip in temporary storage, then writes measured CPU decoder throughput and `crt.environment.environment_snapshot()` with Git SHA to ignored `results/video_smoke.json`. This does not measure CV detection or cashierless-cart accuracy.

## Not yet covered / partially supported
Backend-independent exact PTS, reliable EOF/corruption distinction with bad metadata, hard RTSP socket timeouts, verified rotated-phone playback, autofocus hunting, camera calibration drift, memory-leak checks over hours, full codec validation, and safe rendered outputs. These are explicitly not complete in M1.
