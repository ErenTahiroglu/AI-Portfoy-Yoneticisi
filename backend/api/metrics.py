from prometheus_client import Counter, Histogram

# 1. Gölge (Shadow) Karar Sapması Sayacı
# Etiketler: old_decision (Eski Motorun Kararı), new_decision (Yeni Grafın Kararı), ticker
SHADOW_DIVERGENCE_TOTAL = Counter(
    "shadow_divergence_total",
    "Total number of diverging investment decisions between original AI and LangGraph",
    ["old_decision", "new_decision", "ticker"]
)

# 2. Şema Doğrulama (Validation) Hatası Sayacı
SUMMARIZER_VALIDATION_ERROR_TOTAL = Counter(
    "summarizer_validation_error_total",
    "Total number of Pydantic validation errors inside SummarizerNode before fallback",
    ["agent_node"]
)

# 3. Global Çöküş / Timeout Kalkanı Sayacı
GLOBAL_TIMEOUT_SHIELD_TOTAL = Counter(
    "global_timeout_shield_total",
    "Total number of times the Graph hit the global 30s timeout and defaulted to HOLD"
)

# 4. Agent API Gecikme (Latency) Ölçümü
AI_NODE_LATENCY_SECONDS = Histogram(
    "ai_node_latency_seconds",
    "Time spent making LLM / Fetch calls inside individual LangGraph nodes",
    ["node_name"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0]
)
