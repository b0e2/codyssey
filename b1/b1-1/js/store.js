/**
 * 애플리케이션의 단일 상태 저장소.
 *
 * 화면에 보이는 모든 것의 근거를 한 객체에 모아 둔다. 상태를 DOM에서
 * 읽어 오거나 여기저기 흩어진 전역 변수로 관리하면, 지금 화면이 왜
 * 이렇게 그려졌는지 추적할 수 없고 값이 서로 어긋나기 시작한다.
 *
 * 흐름은 항상 한 방향이다.
 *   이벤트 → setState → 구독자에게 통지 → render → DOM
 */
let state = {
  // 'light' | 'dark'
  theme: 'light',

  navigation: {
    menuOpen: false,
    isScrolled: false,
    showTopButton: false,
  },

  projects: {
    // 'idle' | 'loading' | 'ready' | 'error' | 'empty'
    // idle은 부팅 전 내부 상태이며 사용자에게 보여 주는 상태로 세지 않는다.
    status: 'idle',
    items: [],
    language: 'all',
    errorMessage: '',

    /*
     * 화면 확인용 상태 데모 선택값. 'live'면 위의 status를 그대로 쓰고,
     * 그 밖의 값이면 그 상태의 화면을 대신 그린다. 불러온 items를 지우지 않으므로
     * 실데이터로 돌아올 때 다시 요청할 필요가 없다.
     * 저장하지 않는 값이라 새로고침하면 'live'로 돌아온다.
     */
    // 'live' | 'loading' | 'error' | 'empty'
    demo: 'live',

    /*
     * 지금 화면의 목록이 브라우저에 저장해 둔 응답에서 왔는지와, 그 응답을 받아 둔 시각.
     * 안내 문구를 고르는 데만 쓴다. 상태 이름은 여전히 loading·ready·error·empty 넷이다.
     */
    usedCache: false,
    cachedAt: null,

    /*
     * 유효 기간 안의 캐시인지, 요청이 실패해 어쩔 수 없이 꺼내 쓴 캐시인지.
     * 전자는 조용히 알리고 후자에만 최신이 아닐 수 있다는 경고를 붙인다.
     */
    cacheIsStale: false,
  },

  form: {
    values: { name: '', email: '', message: '' },

    /*
     * blur로 한 번 떠난 필드만 true가 된다. 첫 입력 도중에 오류를 들이밀지
     * 않으려면 "아직 다 안 썼는지"와 "틀렸는지"를 구분해야 한다.
     */
    touched: { name: false, email: false, message: false },

    // 지금 화면에 보이는 오류. touched가 아닌 필드는 값이 비어 있어도 빈 문자열이다.
    errors: { name: '', email: '', message: '' },

    /*
     * 제출을 눌렀을 때 한 번만 알리는 요약 문구.
     * 검증 실패의 개수 안내와 전송 실패의 사유가 같은 자리를 나눠 쓴다.
     * 필드별 오류는 aria-describedby가 맡으므로 여기에는 흘리지 않는다.
     */
    submitAlert: '',

    /*
     * 제출 이후의 진행 상태. 검증은 이 값과 무관하게 언제나 돈다.
     *   idle    입력 중이거나 아직 보내지 않았다
     *   sending 전송 요청이 떠 있다. 버튼을 잠가 중복 제출을 막는다
     *   sent    전송에 성공했다. 입력 폼 자리를 성공 패널이 대신한다
     *   failed  전송에 실패했다. 입력값을 남겨 그대로 다시 시도할 수 있다
     */
    // 'idle' | 'sending' | 'sent' | 'failed'
    status: 'idle',
  },
};

const listeners = new Set();

/** 현재 상태를 읽는다. 반환값을 직접 수정하지 말고 setState를 쓴다. */
export const getState = () => state;

/**
 * 상태를 바꾸고 구독자에게 알린다.
 * 이전 상태를 받아 바뀔 부분만 돌려주는 함수를 넘기거나, 객체를 바로 넘긴다.
 *
 *   setState({ theme: 'dark' })
 *   setState(({ theme }) => ({ theme: theme === 'dark' ? 'light' : 'dark' }))
 *
 * 기존 객체를 고치지 않고 새 객체로 교체하므로, 변경 전후를 비교할 수 있다.
 */
export const setState = (updater) => {
  const changes = typeof updater === 'function' ? updater(state) : updater;

  state = { ...state, ...changes };
  listeners.forEach((listener) => listener(state));
};

/**
 * 상태가 바뀔 때마다 호출될 함수를 등록하고, 해제 함수를 돌려준다.
 * 구독자는 '무엇이 바뀌었는지'가 아니라 '지금 상태가 무엇인지'만 받는다.
 */
export const subscribe = (listener) => {
  listeners.add(listener);

  return () => listeners.delete(listener);
};
