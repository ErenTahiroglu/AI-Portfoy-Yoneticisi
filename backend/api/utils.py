from typing import List

def process_tickers_with_weights(raw_tickers: List[str]):
    parsed = []
    weights_map = {}
    for rt in raw_tickers:
        parts = rt.split(":")
        ticker = parts[0].strip().upper()
        if not ticker: continue
        weight = 1.0
        if len(parts) > 1:
            try:
                weight = float(parts[1])
            except ValueError:
                pass
        parsed.append(ticker)
        weights_map[ticker] = weight
    return parsed, weights_map

def tr_lower(text: str) -> str:
    """Türkçe karakter duyarlı küçük harfe çevirme."""
    return text.replace('İ', 'i').replace('I', 'ı').lower()

def tr_upper(text: str) -> str:
    """Türkçe karakter duyarlı büyük harfe çevirme."""
    return text.replace('i', 'İ').replace('ı', 'I').upper()
