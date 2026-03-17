"""SWOT 서브그래프 전용 상태 정의."""
from typing import Annotated
from operator import add
from typing_extensions import TypedDict


class SWOTState(TypedDict):
    subject: str                           # 분석 대상 (기업명, 시장, 제품 등)
    raw_info: Annotated[list[str], add]    # gather_info 에서 누적된 원시 정보
    criteria: dict[str, str]              # 평가 기준 (strength / weakness / opportunity / threat)
    strengths: list[str]                   # S — 내부 강점
    weaknesses: list[str]                  # W — 내부 약점
    opportunities: list[str]              # O — 외부 기회
    threats: list[str]                     # T — 외부 위협
    swot_matrix: str                       # 최종 포맷된 2×2 행렬
