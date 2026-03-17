"""
분석 도구 모음.

- analyze_swot: SWOT 분석 결과를 2×2 행렬표로 반환
"""
from typing import Annotated
from langchain_core.tools import tool


@tool
def analyze_swot(
    subject: Annotated[str, "분석 대상 (기업명, 제품, 시장 등)"],
    strengths: Annotated[list[str], "강점(S) 항목 목록 — 내부적으로 잘하고 있는 것, 경쟁 우위 요소"],
    weaknesses: Annotated[list[str], "약점(W) 항목 목록 — 내부적으로 부족한 점, 개선이 필요한 부분"],
    opportunities: Annotated[list[str], "기회(O) 항목 목록 — 외부 환경에서 유리하게 작용하는 요소"],
    threats: Annotated[list[str], "위협(T) 항목 목록 — 외부 환경에서의 위험 요소"],
) -> str:
    """
    SWOT 분석 항목을 받아 2×2 행렬표 형식으로 반환합니다.

    행(Row)    : O(기회) / T(위협)  — 외부 요인
    열(Column) : S(강점) / W(약점)  — 내부 요인

    각 셀은 해당 조합의 전략적 시사점을 포함합니다.
    """

    def _fmt(items: list[str], max_width: int) -> list[str]:
        """항목 목록을 bullet 줄 목록으로 변환."""
        lines = []
        for item in items:
            # 긴 텍스트는 max_width 단위로 줄바꿈
            words = item.split()
            line = "• "
            for word in words:
                if len(line) + len(word) + 1 > max_width:
                    lines.append(line.rstrip())
                    line = "  " + word + " "
                else:
                    line += word + " "
            lines.append(line.rstrip())
        return lines if lines else ["• (없음)"]

    def _pad(text: str, width: int) -> str:
        """텍스트를 지정 너비로 패딩 (한글 2바이트 고려)."""
        display_len = sum(2 if ord(c) > 127 else 1 for c in text)
        pad = width - display_len
        return text + " " * max(pad, 0)

    COL_W = 38   # S / W 열 너비
    ROW_W = 14   # O / T 행 레이블 너비

    s_lines = _fmt(strengths, COL_W - 2)
    w_lines = _fmt(weaknesses, COL_W - 2)
    o_lines = _fmt(opportunities, COL_W - 2)
    t_lines = _fmt(threats, COL_W - 2)

    # 헤더 정의
    header_row  = " " * ROW_W + "│ " + _pad("S  강점 (Strength)", COL_W) + "│ " + _pad("W  약점 (Weakness)", COL_W) + "│"
    header_sub  = " " * ROW_W + "│ " + _pad("내부 경쟁 우위 요소", COL_W) + "│ " + _pad("내부 개선 필요 부분", COL_W) + "│"

    sep_top     = "─" * ROW_W + "┬" + "─" * (COL_W + 2) + "┬" + "─" * (COL_W + 2) + "┐"
    sep_head    = "─" * ROW_W + "┼" + "─" * (COL_W + 2) + "┼" + "─" * (COL_W + 2) + "┤"
    sep_mid     = "─" * ROW_W + "┼" + "─" * (COL_W + 2) + "┼" + "─" * (COL_W + 2) + "┤"
    sep_bot     = "─" * ROW_W + "┴" + "─" * (COL_W + 2) + "┴" + "─" * (COL_W + 2) + "┘"

    def _build_cell_rows(row_label: str, row_sub: str, left_lines: list[str], right_lines: list[str]) -> list[str]:
        """행 레이블 + 두 열의 내용을 합쳐 행 목록을 반환."""
        n = max(len(left_lines), len(right_lines), 2)
        rows = []
        for i in range(n):
            if i == 0:
                lbl = _pad(row_label, ROW_W - 1) + " │"
            elif i == 1:
                lbl = _pad(row_sub, ROW_W - 1) + " │"
            else:
                lbl = " " * (ROW_W - 1) + " │"
            l = (" " + _pad(left_lines[i], COL_W) + "│") if i < len(left_lines) else (" " + " " * COL_W + "│")
            r = (" " + _pad(right_lines[i], COL_W) + "│") if i < len(right_lines) else (" " + " " * COL_W + "│")
            rows.append(lbl + l + r)
        return rows

    o_rows = _build_cell_rows("O  기회 (Opportunity)", "외부 유리 환경 요소", o_lines, s_lines)
    t_rows = _build_cell_rows("T  위협 (Threat)",       "외부 위험 요소",       t_lines, w_lines)

    title = f"\n{'━' * (ROW_W + (COL_W + 3) * 2)}"
    title += f"\n  SWOT 분석  |  {subject}"
    title += f"\n{'━' * (ROW_W + (COL_W + 3) * 2)}\n"

    lines = [
        title,
        sep_top,
        header_row,
        header_sub,
        sep_head,
        *o_rows,
        sep_mid,
        *t_rows,
        sep_bot,
    ]
    return "\n".join(lines)
