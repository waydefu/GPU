# opstream-g-01 — INVALID（凍結，不重判）

- 判定：`renderer_thread_not_found`（runner 在 Activity 的執行緒清單找 `LorieRendererTh`）。
- 工具錯誤，不是產品結果：renderer 執行緒在 **X3 程序內**（`gles-renderer: Initialized EGL` 來自 X3 pid 16848 的 tid 17284），
  且 `pthread_setname_np("LorieRendererThread")` 因超過 15 字元失敗，comm 仍是 `main`。
- 第二個工具錯誤：exit trap `cleanup; b_cleanup; mg_stop` 在非零結束碼下於 `cleanup` 中斷（harness-lib 的 cleanup 回傳原結束碼、set -e），
  X3 16848 與 mem-guard 在 INVALID 後持續執行約 10 分鐘，直到手動以精確 pid SIGTERM（見 cleanup.txt）。
  同一 trap 寫法存在於 run-oplat.sh 等衍生 runner。
- 事後 `am force-stop` 未送出：ADB（192.168.1.100:42927）在此期間斷線（Connection refused）。
- Stable `:1` 未受影響：run 前後 pid 皆為 20457。
- 未擷取 atrace；fixture 未執行。修正後的 runner 用於 opstream-g-02。
