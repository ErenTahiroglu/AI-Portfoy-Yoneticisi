from src.core.analysis_engine import AnalysisEngine

# Singleton instance of analysis engine
engine = AnalysisEngine()

def get_engine() -> AnalysisEngine:
    """Dependency Injection provider for AnalysisEngine."""
    return engine
