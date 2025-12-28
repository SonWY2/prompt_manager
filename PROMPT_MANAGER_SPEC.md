# Prompt Manager 기능 명세서

## 1. 개요 (Product Overview)
Prompt Manager는 LLM(Large Language Model) 프롬프트 엔지니어링을 효율적으로 수행하기 위한 **통합 관리 도구**입니다. 사용자는 다양한 태스크별로 프롬프트를 관리하고, 버전 제어를 통해 프롬프트를 고도화하며, 템플릿 변수를 사용하여 동적인 테스트를 수행할 수 있습니다. 또한, 여러 LLM 모델(OpenAI, Anthropic 등)을 연동하여 즉시 실행하고 결과를 비교 분석할 수 있습니다.

**핵심 가치:**
- **구조화된 관리:** 흩어진 프롬프트를 태스크와 버전 단위로 체계적으로 관리.
- **반복 실험 최적화:** 변수 치환과 버전 관리를 통해 신속한 A/B 테스트 지원.
- **통합 실행 환경:** 별도의 코딩 없이 UI에서 직접 LLM API를 호출하고 결과 확인.

---

## 2. 핵심 개념 정의 (Key Concepts)

| 용어 | 정의 | 관계 |
| :--- | :--- | :--- |
| **Task** | 특정 목적을 가진 프롬프트 프로젝트 단위 (예: "이메일 요약", "코드 생성"). | 하나의 Task는 여러 Version을 가짐. Task 레벨 변수 보유 가능. |
| **Version** | Task 내에서 수정/개선된 프롬프트의 스냅샷. | 고유한 Prompt Content, System Prompt, Description 보유. |
| **Variable** | 프롬프트 내에서 동적으로 치환되는 값. `{{variable_name}}` 형식. | Task 레벨에서 전역 값 설정 가능하며, 실행 시점에 입력값으로 주입됨. |
| **Result** | 특정 Version으로 LLM을 실행한 결과. | 실행 시점의 Input Data, Output, 모델 정보, Timestamp를 포함. |
| **LLM Endpoint** | 실제 LLM API 연결 정보 (Base URL, API Key, Model). | 사용자는 여러 Endpoint를 등록하고 활성화하여 사용 가능. |

---

## 3. 상세 기능 요건 (Feature Specifications)

### 3.1 태스크 관리 (Task Management)
사용자는 작업의 단위인 Task를 생성하고 관리할 수 있어야 합니다.

*   **생성:**
    *   사용자는 고유한 이름을 가진 새 Task를 생성할 수 있다.
    *   초기 생성 시 Task는 빈 상태이며, 즉시 첫 번째 버전을 생성할 준비가 되어야 한다.
*   **조회 및 탐색:**
    *   좌측 사이드바에서 모든 Task 목록을 확인할 수 있다.
    *   Task는 최근 수정순으로 정렬된다.
    *   특정 Task를 클릭하면 해당 Task의 최신 작업 상태(마지막 선택 버전 등)로 진입한다.
*   **수정 및 삭제:**
    *   Task의 이름을 수정할 수 있다.
    *   Task를 삭제하면 하위의 모든 Version과 Result 데이터도 영구적으로 삭제되어야 한다 (Cascade Delete).
*   **상태 관리:**
    *   '즐겨찾기' 기능을 통해 중요 Task를 상단에 고정하거나 별도로 필터링할 수 있다.

### 3.2 프롬프트 편집 및 버전 관리 (Prompt Engineering & Versioning)
프롬프트를 작성하고, 수정하고, 이력을 관리하는 핵심 기능입니다.

*   **3단 구성 에디터:**
    *   **Description:** 해당 프롬프트 버전의 목적이나 특징을 기록하는 메타데이터 필드.
    *   **System Prompt:** LLM에게 역할을 부여하는 시스템 지시문 (예: "You are a helpful assistant").
    *   **User Prompt (Main):** 실제 작업을 지시하는 메인 프롬프트. `{{variable}}` 구문을 사용하여 템플릿 변수를 삽입할 수 있다.
*   **버전 제어 (Versioning):**
    *   **새 버전 생성:** 현재 작업 중인 내용을 기반으로 새로운 버전을 생성한다 (스냅샷 저장).
    *   **버전 타임라인:** 상단 타임라인 UI를 통해 이전 버전으로 자유롭게 이동하여 내용을 확인할 수 있다.
    *   **복제 (Copy):** 특정 버전을 복제하여 새로운 버전의 시작점으로 삼을 수 있다.
*   **자동 저장 (Auto-save):**
    *   에디터의 내용은 사용자가 입력을 멈추거나 포커스를 잃을 때 자동으로 서버에 저장되어야 한다.
    *   저장 상태(Saving, Saved, Error)를 시각적으로 표시해야 한다.
*   **변수 하이라이팅:**
    *   에디터 내에서 `{{variable}}` 패턴은 시각적으로 강조(Highlight)되어야 한다.

### 3.3 템플릿 변수 관리 (Template Variable Management)
동적 프롬프트를 위한 변수 추출 및 값 관리 기능입니다.

*   **자동 추출:**
    *   에디터(System/User Prompt)에 입력된 `{{...}}` 패턴을 실시간으로 분석하여 변수 목록을 추출한다.
    *   변수명은 영문자, 숫자, 언더스코어, 하이픈만 허용한다.
*   **값 할당 (Value Assignment):**
    *   **Task Variables:** Task 단위로 변수값을 저장하여, 동일한 Task 내의 모든 Version에서 공통으로 사용할 수 있다.
    *   사용자는 각 변수에 대해 테스트용 값(Value)을 입력할 수 있다.
    *   사용되지 않는 변수(프롬프트에서 제거된 변수)는 삭제 가능하도록 표시한다.
*   **프리뷰 (Preview):**
    *   변수값이 치환된 최종 프롬프트 형태를 미리보기 모드에서 확인할 수 있다.

### 3.4 LLM 실행 및 결과 (LLM Execution & Results)
작성한 프롬프트를 실제 LLM 모델에 전송하고 응답을 확인합니다.

*   **LLM Endpoint 설정:**
    *   사용자는 사용할 LLM 모델의 연결 정보(이름, Base URL, API Key, Default Model)를 'Settings' 또는 별도 관리 메뉴에서 등록한다.
    *   OpenAI 호환 API (OpenAI, Anthropic, Ollama, vLLM 등) 형식을 지원해야 한다.
    *   특정 Endpoint를 'Active' 상태로 설정하여 실행 시 사용한다.
*   **실행 (Run Prompt):**
    *   실행 버튼 클릭 시, 현재 선택된 Version의 프롬프트 내용과 입력된 변수값을 결합(Rendering)한다.
    *   결합된 최종 프롬프트를 Active Endpoint로 전송한다.
    *   실행 중에는 로딩 상태를 표시하고 중복 실행을 방지한다.
*   **결과 표시:**
    *   LLM의 응답(Response)을 화면에 출력한다.
    *   **메트릭:** 소모된 토큰 수(Input/Output)와 추정 비용(Cost)을 계산하여 표시한다.
    *   **이력 저장:** 모든 실행 결과는 자동으로 'History' 탭에 저장된다.

### 3.5 실행 이력 및 분석 (History & Analysis)
과거의 실행 결과를 조회하고 비교합니다.

*   **이력 목록:**
    *   해당 Version에서 실행했던 모든 결과 목록을 최신순으로 보여준다.
    *   각 이력 아이템은 실행 시각, 사용 모델, 응답 요약을 포함한다.
*   **상세 조회:**
    *   이력 아이템 선택 시, 당시의 **Request Message**(치환된 전체 프롬프트), **Response**, **Metrics**, **Input Variables**를 상세히 보여준다.
*   **비교 (Comparison) - (Future/Optional):**
    *   서로 다른 두 버전의 실행 결과를 나란히(Side-by-side) 놓고 비교할 수 있는 뷰를 제공한다.

---

## 4. 사용자 흐름 (User Flow)

1.  **시작:** 사용자는 '새 태스크 만들기'를 통해 프로젝트(예: "마케팅 문구 작성")를 시작한다.
2.  **작성:**
    *   System Prompt에 "너는 전문 마케터야"라고 입력한다.
    *   User Prompt에 "제품 {{product_name}}에 대한 {{target_audience}} 타겟의 광고 문구를 작성해줘"라고 입력한다.
3.  **변수 설정:** Variables 탭으로 이동하여 `product_name`에 "AI 커피메이커", `target_audience`에 "30대 직장인"을 입력한다.
4.  **실행:** 'Run Prompt' 버튼을 누른다.
5.  **확인:** 우측 패널에서 LLM이 생성한 광고 문구를 확인한다. 결과가 마음에 들지 않는다.
6.  **수정 및 버전업:**
    *   'New Version' 버튼을 누르거나 에디터 내용을 수정하여 v2를 만든다.
    *   프롬프트에 "단, 이모지를 많이 사용해서 친근하게 작성해줘"라는 제약 조건을 추가한다.
7.  **재실행 및 비교:** 다시 실행하고, History 탭에서 v1의 결과와 v2의 결과를 비교하여 더 나은 버전을 선택한다.

---

## 5. 시스템 요구사항 (System Requirements Summary)

*   **Frontend:** React 기반 SPA. 상태 관리는 전역 스토어(예: Zustand)를 사용하여 Task/Version/Result 간의 데이터 동기화를 보장해야 함.
*   **Backend:** 경량 REST API 서버. JSON 파일 기반 DB(또는 SQLite)를 사용하여 별도 설치 없이 구동 가능해야 함.
*   **API Integration:** 외부 LLM API 호출 시 타임아웃 처리 및 에러 핸들링이 필수적임.
*   **Data Structure:** Task -> Version -> Result 의 1:N:M 계층 구조를 엄격히 유지해야 함.
