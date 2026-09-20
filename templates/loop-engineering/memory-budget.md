# Memory Budget Specification — AI 優化 Workspace

本規範定義 AI Agent 上下文 Token 預算分配與檢索上限，確保高成本效益並防止記憶膨脹。

---

## 📊 Token Budget Allocation (預算分配)

- **Max Context Window**: 200,000 tokens
- **Core System & Rules Reserve**: 25,000 tokens (System Prompt, Karpathy Guidelines, Invariants)
- **L1 Working Memory Allocation**: 45,000 tokens (`STATE.md`, active session turn, git status)
- **L2 Episodic Memory Allocation**: 30,000 tokens (recent `SNAPSHOT.jsonl`, handoff records)
- **L3 Semantic Retrieval Cap**: 100,000 tokens (Supabase RAG / Long-term documentation)

---

## ⚡ Compression & Eviction Policies (壓縮與驅逐策略)

1. **Context Headroom Warning**: 當整體 Context 消耗達 140,000 tokens (70%) 時，啟動警告。
2. **Auto-Compaction Trigger**: 當快照數量超過 200 條時，觸發 SelfCompact 熱蒸餾（歸檔前 150 條為結構化單一摘要）。
3. **Retrieval Hard Cap**: 單次語意查詢檢索返回結果上限為 5 篇（Token 上限 10k），避免雜訊污染工作記憶。
