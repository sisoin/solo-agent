# 배터리 기업 전략 분석 에이전트

LLM 기반 멀티에이전트 시스템으로 CATL과 LG에너지솔루션의 배터리 시장 전략을 자동 분석하고 PDF 보고서를 생성합니다.

## Overview

- **Objective** : 글로벌 배터리 양대 기업(CATL·LG에너지솔루션)의 포트폴리오, 기술 경쟁력, SWOT, 전략 비교를 자동화된 멀티에이전트 파이프라인으로 분석
- **Method** : RAG(기업 내부 문서) + 실시간 웹서치를 결합해 정보를 수집하고, LangGraph Supervisor 패턴으로 에이전트를 조율하여 구조화된 PDF 보고서 생성
- **Tools** : Tavily Search, Google News, yfinance, PDFPlumber, WeasyPrint, Qdrant

## Features

- PDF·웹 문서 기반 RAG 검색 (기업 IR 자료, 기술 문서 등)
- 실시간 웹서치(Tavily)와 RAG를 균형 있게 활용하는 정보 수집 전략
- LG에너지솔루션·CATL 회사별 분석을 LangGraph Send API로 병렬 실행
- 확증 편향 방지 전략 : 긍정(수주·성장) 검색 후 부정(실적 부진·리스크) 정보를 별도 검색하도록 프롬프트 설계, Supervisor·보고서 생성 에이전트 모두 균형 분석 원칙 적용
- 참고문헌 URL 유효성 검사 (HTTP HEAD 요청으로 404·오류 링크 자동 제거)
- `LLM.with_structured_output`으로 보고서 섹션을 스키마 기반 구조화 생성
- WeasyPrint를 통한 HTML → PDF 자동 변환

## Tech Stack

| Category   | Details                                        |
|------------|------------------------------------------------|
| Framework  | LangGraph, LangChain, langgraph-supervisor     |
| LLM        | GPT-4o-mini via OpenAI API                     |
| Retrieval  | Qdrant (Vector DB)                             |
| Embedding  | BAAI/bge-m3 (1024 dim, HuggingFace)            |
| Web Search | Tavily Search, Google News                     |
| Report     | WeasyPrint (HTML → PDF)                        |

## Agents

- **retrieve_node** : 배터리 시장 공통 배경 문서를 RAG로 선검색하여 하위 에이전트에 전달
- **company_analysis_agent** (Supervisor) : LG에너지솔루션·CATL 각각에 대해 하위 3개 에이전트를 순차 조율
  - **market_analysis_agent** : 시장 규모·점유율·원자재 가격·최신 뉴스 웹서치 수집
  - **tech_analysis_agent** : 배터리 셀 기술·공정·차세대 기술 역량 분석
  - **swot_analysis_agent** : SWOT 서브그래프를 실행하여 2×2 행렬 생성
- **company_comparison_agent** : 두 기업 분석 결과를 종합하여 비교 보고서 작성
- **report_generation_agent** : 구조화 출력으로 보고서 섹션 생성 → HTML 렌더링 → PDF 저장

## Architecture

<img width="811" height="491" alt="아키텍처" src="https://github.com/user-attachments/assets/c34e22cb-bf00-4fa0-8421-6b3990335830" />

## Directory Structure

```
├── data/
│   └── tech_docs/             # 기업별 PDF 문서 (LG에너지솔루션, CATL)
├── battery_market_agent/
│   ├── agents/                # Agent 및 LangGraph 그래프 모듈
│   │   └── swot/              # SWOT 분석 서브그래프
│   ├── rag/                   # RAG 파이프라인 (ingest, retriever)
│   ├── state/                 # LangGraph State 정의
│   ├── tools/                 # 도구 모음 (검색, 시장 데이터, 분석)
│   └── config/                # 환경 설정 (Settings)
├── docs/                      # 생성된 PDF 보고서
├── run.sh                     # 실행 스크립트
└── README.md
```

## 특이사항

- **분량 보정 Loop 제거** : 각 서브 에이전트의 결과물이 기준 분량에 미달할 경우 최대 5회 재시도하는 Loop를 구현하였으나, GPT-4o-mini 모델이 장문 텍스트 생성에 특화되어 있지 않아 Loop를 모두 소진하고도 분량을 충족하지 못하는 문제가 반복적으로 발생하였다. 이에 분량 보정 Loop를 제거하고 단일 호출로 최대한의 출력을 유도하는 방향으로 변경하였다.
- **Retrieval 결과 State 전파 문제** : `retrieve_node`에서 수집한 RAG 검색 결과가 이후 모든 State에 그대로 전달되어 토큰을 불필요하게 과다 소비하는 문제가 발생하였다. 이로 인해 분당 요청 토큰(TPM) 한도를 초과하여 API 오류가 발생하였으며, RAG 결과를 필요한 에이전트에만 한정적으로 전달하도록 State 설계를 수정하여 해결하였다.

## Contributors

- 배민준 : Agent 설계, 프롬프트 엔지니어링, RAG 파이프라인, 보고서 생성
