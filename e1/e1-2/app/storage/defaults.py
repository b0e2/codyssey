"""데이터 파일이 없거나 손상됐을 때 사용할 기본 퀴즈 데이터."""

from app.constants import CATEGORY_BACKEND, CATEGORY_PYTHON
from app.models.quiz import Quiz


def default_quizzes() -> list[Quiz]:
    """기본 퀴즈 목록을 새로 만들어 반환한다."""
    return [Quiz.from_dict(data) for data in DEFAULT_QUIZ_DATA]


DEFAULT_QUIZ_DATA = [
    {
        "question": "리스트와 튜플의 가장 큰 차이는?",
        "choices": [
            "리스트는 숫자만, 튜플은 문자열만 담는다",
            "리스트는 순서가 없고, 튜플은 순서가 있다",
            "리스트는 만든 뒤 내용을 바꿀 수 있고, 튜플은 바꿀 수 없다",
            "차이가 없고 이름만 다르다",
        ],
        "answer": 3,
        "hint": "하나는 만든 뒤에 내용을 바꿀 수 없다.",
        "category": CATEGORY_PYTHON,
    },
    {
        "question": "다음 중 딕셔너리를 만드는 표현으로 올바른 것은?",
        "choices": [
            "{1, 2, 3}",
            "[1: 'a', 2: 'b']",
            "{'a': 1, 'b': 2}",
            "('a', 1, 'b', 2)",
        ],
        "answer": 3,
        "hint": "중괄호 안에 키와 값을 콜론으로 짝지어 쓴다.",
        "category": CATEGORY_PYTHON,
    },
    {
        "question": "for 문에서 특정 조건일 때 반복 전체를 즉시 멈추는 키워드는?",
        "choices": ["continue", "break", "pass", "return"],
        "answer": 2,
        "hint": "continue는 다음 반복으로 넘어갈 뿐 멈추지 않는다.",
        "category": CATEGORY_PYTHON,
    },
    {
        "question": "클래스 메서드의 첫 번째 매개변수 self가 가리키는 것은?",
        "choices": [
            "클래스 자신",
            "메서드를 호출한 인스턴스",
            "부모 클래스",
            "아무 의미 없는 이름",
        ],
        "answer": 2,
        "hint": "인스턴스를 통해 메서드를 부를 때 자동으로 전달된다.",
        "category": CATEGORY_PYTHON,
    },
    {
        "question": "예외가 발생하든 안 하든 항상 실행되는 블록은?",
        "choices": ["try", "except", "else", "finally"],
        "answer": 4,
        "hint": "보통 파일을 닫는 등 뒷정리에 쓴다.",
        "category": CATEGORY_PYTHON,
    },
    {
        "question": "파일을 열 때 with open(...) 구문을 쓰는 주된 이유는?",
        "choices": [
            "파일을 더 빠르게 읽으려고",
            "블록을 벗어나면 파일이 자동으로 닫히도록",
            "파일 내용을 자동으로 정렬하려고",
            "여러 파일을 한 번에 열려고",
        ],
        "answer": 2,
        "hint": "close()를 깜빡해도 안전하다.",
        "category": CATEGORY_PYTHON,
    },
    {
        "question": "요청한 자원을 정상적으로 처리했음을 뜻하는 HTTP 상태 코드는?",
        "choices": ["200", "301", "404", "500"],
        "answer": 1,
        "hint": "성공 계열은 2로 시작한다.",
        "category": CATEGORY_BACKEND,
    },
    {
        "question": "서버에 새로운 자원을 생성할 때 주로 쓰는 HTTP 메서드는?",
        "choices": ["GET", "POST", "DELETE", "HEAD"],
        "answer": 2,
        "hint": "조회는 GET, 생성은 다른 메서드다.",
        "category": CATEGORY_BACKEND,
    },
    {
        "question": "존재하지 않는 페이지에 접근했을 때 흔히 보는 상태 코드는?",
        "choices": ["200", "302", "404", "503"],
        "answer": 3,
        "hint": "'Not Found'라는 문구와 함께 나온다.",
        "category": CATEGORY_BACKEND,
    },
    {
        "question": "REST에서 자원을 식별하는 데 사용하는 것은?",
        "choices": ["URI", "쿠키", "포트 번호", "세션 ID"],
        "answer": 1,
        "hint": "주소창에 보이는 경로를 떠올려 보자.",
        "category": CATEGORY_BACKEND,
    },
    {
        "question": "JSON에 대한 설명으로 올바른 것은?",
        "choices": [
            "파이썬에서만 쓸 수 있는 형식이다",
            "키와 값으로 데이터를 표현하는 텍스트 형식이다",
            "이미지를 저장하는 이진 형식이다",
            "데이터베이스 전용 언어다",
        ],
        "answer": 2,
        "hint": "이름은 JavaScript Object Notation의 약자다.",
        "category": CATEGORY_BACKEND,
    },
    {
        "question": "관계형 데이터베이스에서 각 행을 유일하게 구분하는 값은?",
        "choices": ["외래 키", "기본 키", "인덱스", "뷰"],
        "answer": 2,
        "hint": "Primary Key라고 부른다.",
        "category": CATEGORY_BACKEND,
    },
]
