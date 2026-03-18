"""
에이전트에 바인딩되는 배터리 시장 분석 도구 모음.

각 함수는 @tool (LangChain)로 데코레이팅되어
에이전트의 도구 목록에 직접 전달됩니다.
"""
from langchain_core.tools import tool
import yfinance as yf

# 원자재 이름 → yfinance 티커 매핑
# 선물 계약 또는 대표 ETF 활용
_MATERIAL_TICKERS: dict[str, tuple[str, str]] = {
    # 한국어 키워드 → (티커, 설명)
    "리튬":   ("LIT",   "Global X Lithium & Battery Tech ETF (LIT)"),
    "lithium": ("LIT",  "Global X Lithium & Battery Tech ETF (LIT)"),
    "코발트": ("SBSW",  "Sibanye-Stillwater 코발트 생산주 (SBSW)"),
    "cobalt":  ("SBSW", "Sibanye-Stillwater 코발트 생산주 (SBSW)"),
    "니켈":   ("VALE", "Vale S.A. 니켈 생산주 (VALE)"),
    "nickel":  ("VALE", "Vale S.A. 니켈 생산주 (VALE)"),
    "구리":   ("HG=F",  "COMEX 구리 선물 (HG=F)"),
    "copper":  ("HG=F", "COMEX 구리 선물 (HG=F)"),
    "망간":   ("MNO",   "Consolidation Manganese Corp (MNO.AX 대용)"),
    "manganese": ("MNO", "Consolidation Manganese Corp"),
}

_PERIOD_MAP: dict[str, str] = {
    "1d": "5d", "7d": "1mo", "1m": "1mo", "3m": "3mo",
    "6m": "6mo", "1y": "1y", "2y": "2y", "5y": "5y",
}


@tool
def fetch_price_trends(material: str, period: str = "1y") -> str:
    """
    배터리 원자재(리튬·코발트·니켈 등)의 가격 추이를 조회합니다.

    Args:
        material: 원자재 이름 (예: '리튬', '코발트', '니켈', 'lithium')
        period: 조회 기간 (예: '1m', '3m', '6m', '1y', '2y')

    Returns:
        최근 가격 통계 및 추이 요약 텍스트
    """
    key = material.strip().lower()
    ticker_info = _MATERIAL_TICKERS.get(key)

    # 키워드 부분 매칭 fallback
    if ticker_info is None:
        for k, v in _MATERIAL_TICKERS.items():
            if k in key or key in k:
                ticker_info = v
                break

    if ticker_info is None:
        return (
            f"'{material}'에 대한 티커 매핑이 없습니다. "
            f"지원 원자재: {', '.join(_MATERIAL_TICKERS.keys())}"
        )

    ticker_symbol, label = ticker_info
    yf_period = _PERIOD_MAP.get(period, "1y")

    try:
        data = yf.Ticker(ticker_symbol).history(period=yf_period)
    except Exception as e:
        return f"[{label}] 데이터 조회 실패: {e}"

    if data.empty:
        return f"[{label}] {yf_period} 기간 데이터가 없습니다."

    close = data["Close"]
    latest      = close.iloc[-1]
    oldest      = close.iloc[0]
    high        = close.max()
    low         = close.min()
    pct_change  = (latest - oldest) / oldest * 100
    latest_date = data.index[-1].strftime("%Y-%m-%d")

    # 월별 종가 샘플 (최대 12포인트)
    monthly = close.resample("ME").last().tail(12)
    trend_lines = [f"  {d.strftime('%Y-%m')}: {v:.2f}" for d, v in monthly.items()]

    return (
        f"[{label}]\n"
        f"기간: {yf_period} | 기준일: {latest_date}\n"
        f"최신가: {latest:.2f} | 기간 시작가: {oldest:.2f}\n"
        f"기간 고점: {high:.2f} | 기간 저점: {low:.2f}\n"
        f"기간 수익률: {pct_change:+.1f}%\n\n"
        f"월별 종가 추이:\n" + "\n".join(trend_lines)
    )


