#!/bin/bash
# weasyprint가 Homebrew의 libgobject를 찾을 수 있도록 DYLD_LIBRARY_PATH 설정
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
uv run python -m battery_market_agent.main "$@"
