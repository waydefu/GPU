# 擷取後的變更（sha256sums.txt 保留擷取當下的原樣）

- `trace-tids.txt` → `trace-tids-RUNNER-GUESS-WRONG.txt`（檔首加註）。runner 以 logcat 的
  `gles-renderer: Initialized EGL` tid 當 renderer，那其實是 X 的 dix 執行緒；X3 的 thread-group leader 是 Android Looper。
- `decompose.txt/.json`（用錯的 tid）→ `decompose-WRONG-TIDS.*`；新的 `decompose.*` 由 opstream_decompose.py
  從追蹤紀錄判定 tid（fork commit efa9d4b），DETECT 行記錄依據。
- 擷取本身（atrace.z、opstream.out、stable-*.json 等）未變動。
