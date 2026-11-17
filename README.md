# ☕ Smart Coffee Inventory Management System

Python, Pandas, SQLite, Streamlit을 활용한 스마트 커피 재고 관리 시스템

## 1. 프로젝트 소개

커피 매장 판매 데이터를 분석하고, 상품별 재고 현황과 예상 수요를 바탕으로 품절 위험을 파악하며 발주를 지원하는 데이터 기반 재고 관리 프로젝트입니다.

매출 데이터 분석에서 시작하여 재고 예측, SQLite 데이터베이스 구축, 입고·출고 관리, Streamlit 대시보드 구현까지 확장했습니다.

## 2. 개발 환경

| 구분 | 사용 기술 |
|---|---|
| Language | Python |
| Data Analysis | Pandas, NumPy |
| Database | SQLite |
| Dashboard | Streamlit, Plotly |
| Development | VS Code |
| Version Control | Git, GitHub |

## 3. 주요 기능

### 판매 데이터 분석
- 매장별·상품별 판매 데이터 분석
- 상품 수요 분석
- 분석 결과 CSV 저장

### 재고 관리
- 상품별 현재 재고 확인
- 예상 수요 기반 품절 위험 분석
- 재고 부족 상품에 대한 발주 추천

### 입고·출고 처리
- 상품별 입고 수량 입력
- 상품별 출고 수량 입력
- SQLite 재고 수량 반영
- 재고 변동 이력 저장

### BI 대시보드
- 재고 현황 시각화
- 품절 위험 상품 확인
- 발주 추천 정보 확인
- 데이터 조회 및 관리

## 4. 프로젝트 개발 과정

| 일차 | 개발 내용 |
|---|---|
| 1일차 | 프로젝트 환경 설정 |
| 2일차 | 데이터 구조 확인 |
| 3일차 | 판매 데이터 전처리 |
| 4일차 | 상품별 수요 분석 |
| 5일차 | 재고 및 품절 위험 예측 |
| 6일차 | 발주 추천 로직 구현 |
| 7일차 | SQLite 데이터베이스 구축 |
| 8일차 | Streamlit 대시보드 구현 |
| 9일차 | 입고·출고 및 재고 변동 이력 기능 |
| 10일차 | 최종 테스트 및 GitHub 정리 |

## 5. 프로젝트 폴더 구조

```text
Coffee-Shop-Sales-Data-Inventory-Project/
├── Coffee-Shop-Sales-Data-Analytics-Project-main/
├── data/
├── database/
├── output/
├── python/
├── sql/
├── app.py
├── app_backup.py
├── inventory_manager.py
├── requirements.txt
├── test_day10.py
├── README.md
└── .gitignore
```

`app.py`는 최종 실행 코드이며, `app_backup.py`는 개발 과정의 이전 버전입니다.

## 6. 실행 방법

### 프로젝트 다운로드

```bash
git clone https://github.com/bottle1144/smart-coffee-inventory-system.git
cd smart-coffee-inventory-system
```

### 가상환경 생성

```bash
python -m venv venv
venv\Scripts\activate
```

### 라이브러리 설치

```bash
python -m pip install -r requirements.txt
```

### 데이터베이스 준비

SQLite 데이터베이스 파일은 GitHub에 포함하지 않았습니다.

실행 전에 프로젝트의 `python/database.py`를 통해 초기 데이터베이스를 생성해야 합니다. 필요한 데이터 파일과 실행 순서는 실제 코드에 맞춰 확인해야 합니다.

### 대시보드 실행

```bash
python -m streamlit run app.py
```

실행 후 브라우저에서 일반적으로 다음 주소로 접속할 수 있습니다.

`http://localhost:8501`

## 7. 최종 테스트

프로젝트 개발 환경에서 최종 테스트를 진행했습니다.

- 데이터베이스 파일 확인
- SQLite 무결성 검사
- 주요 테이블 및 컬럼 확인
- 재고 관리 관련 기능 점검

최종 테스트 결과: **ALL CHECKS PASSED**

## 8. 향후 개선 방향

- 판매량 예측 모델 고도화
- 매장별 재고 비교 기능 확장
- 품절 위험 알림 기능
- 발주 자동화 기능
- 클라우드 환경 배포

## 9. 원본 데이터 및 참고 자료

원본 커피 매출 분석 자료는 프로젝트 내 `Coffee-Shop-Sales-Data-Analytics-Project-main/` 폴더에 포함되어 있습니다.

원본 데이터 및 코드의 출처와 라이선스는 확인 후 명시합니다.