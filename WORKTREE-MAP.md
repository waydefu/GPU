# Worktree / 遠端地圖 — 2026-09-17

程式碼不在 `waydefu/GPU`。資格 source 在 fork `waydefu/termux-x11`。
`termux/termux-x11` origin：**禁止 PR / merge / push / force**。

## 遠端

| 角色 | URL |
|---|---|
| 本 docs 倉庫 | https://github.com/waydefu/GPU |
| 資格 fork | https://github.com/waydefu/termux-x11 |
| 上游 origin（只讀） | https://github.com/termux/termux-x11 |
| 目前裝置 APK CI | https://github.com/waydefu/termux-x11/actions/runs/35103216566 |

## 工作站工作樹（2026-09-17）

| 路徑 | HEAD | 分支 | 角色 | 紀律 |
|---|---|---|---|---|
| `src/f8-ahb-gatea-case-loop` | `fdfb1ce44b429897eda17c43bf33fbd37afe67f3` | `fix/gatea-r7-fatal-propagation-20260916` | **已安裝** R7-04 修復 | 不要為 R7-05 改 source |
| `src/f8-ahb-gatea-r6-retire` | `0f1e54699d0b11a781f2c044fbc77505f8a53bd8` | `fix/gatea-r6-present-retirement-20260915` | 凍結 R6 PASS | **不准改** |
| `src/f8-ahb-gatea-r7` | `a7528bd` | `qualification/gatea-r7-20260916` | R7 support artifact | 歷史；未安裝 |
| `src/f8-ahb-gatea-exa-timeout` | `0d72332c0e591b2137262d06d7dcab704be49383` | timeout 修復 | RCA-1 | 歷史 B-2 FAIL 凍結 |
| `src/f8-ahb-gatea-a1` | `88e3f176d5be313b7dee058da9021cfe8d09e7de` | 凍結 control | 不准改 | |
| `src/f8-ahb-gatea-xpump` | `d9b7f60` | 歷史 xpump | 不要當現行裝置 | |

fork 上 `fdfb1ce` 已 push。origin 分支 **ABSENT**（沒有往 termux/termux-x11 推）。

## 從空機拉現行候選

```bash
mkdir -p /root/projects/GPU加速/src
git clone https://github.com/waydefu/termux-x11.git \
  /root/projects/GPU加速/src/f8-ahb-gatea-case-loop
git -C /root/projects/GPU加速/src/f8-ahb-gatea-case-loop \
  checkout fdfb1ce44b429897eda17c43bf33fbd37afe67f3
git -C /root/projects/GPU加速/src/f8-ahb-gatea-case-loop status --short
# 必須乾淨
```

凍結 R6（只要讀歷史）：

```bash
git clone https://github.com/waydefu/termux-x11.git \
  /root/projects/GPU加速/src/f8-ahb-gatea-r6-retire
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6-retire \
  checkout 0f1e54699d0b11a781f2c044fbc77505f8a53bd8
# 之後不要在這個 worktree 寫入
```

xserver submodule 在部分 worktree 未展開。`verify_r7_support.py` 需要 `xserver/present/present_vblank.c`；修補驗證可用 `core-src/` 與 case-loop `lorie/` + 歷史 patch。不要為了跑 verifier 去改契約。

## Serena

既有專案名：`gpu-f8-ahb`。不要為交接新建。不要殺別人的 clangd/Serena。
