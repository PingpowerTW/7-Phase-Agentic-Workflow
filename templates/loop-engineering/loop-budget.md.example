# Loop Budget — AI 優化 Workspace

## Daily limits

| Loop / Task Type | Max runs/day | Max tokens/day | Max sub-agent spawns/run |
|---|---|---|---|
| Daily Triage (L1) | 2 | 150k | 0 (Report-only) |
| Feature / Refactor Loop (L2) | 10 | 600k | 3 (Maker + Verifier + Auditor) |
| Snapshot & State Sync | 20 | 100k | 0 |

## On budget exceed

1. 暫停高頻自治作業與主動重構迴圈。
2. 切換為 L1 Report-only 模式，不再觸發代碼生成與修改。
3. 提示人類使用者並在 `STATE.md` 記錄預算告警。

## Kill switch

- 旗標狀態: `loop-pause-all: false`
- 當遭遇異常連續失敗或不可預期修改時，將旗標設為 `true` 並立即中斷所有背景 Agent 任務。

## Estimate spend

```bash
node loop-engineering/tools/loop-cost/dist/cli.js --pattern daily-triage --level L1
```
