/**
 * Hero 타이핑 효과.
 *
 * features/scroll-reveal.js와 같은 이유로 전역 상태를 거치지 않는다.
 * 타이핑은 저장할 필요도, 다른 기능과 공유할 필요도 없는 일시적인 시각 효과다.
 * 문구 한 글자마다 setState를 부르면 70ms마다 전체 렌더가 도는데, 그렇게 얻는
 * 것은 아무것도 없다. 이 모듈이 자기 타이머와 진행 위치를 직접 들고 있다.
 *
 * 대신 수명주기는 분명히 나눠 둔다.
 *   시작 — 모션 축소 설정이 아니고 탭이 보이는 동안
 *   정지 — 탭이 가려지면 진행 위치를 그대로 둔 채 타이머만 멈춘다
 *   완성 — 모션 축소 설정에서는 정지한 뒤 완성 문구를 즉시 보여 준다
 */
import { $ } from '../dom.js';

/** 확정 문구 3개. 각각 두 줄이며 줄바꿈은 CSS의 pre-line이 그대로 살린다. */
const PHRASES = [
  'Android부터 Flutter까지\n모바일 서비스를 개발했습니다.',
  '화면 구현을 넘어\n데이터의 흐름을 봅니다.',
  'AI와 백엔드로\n역량을 확장하고 있습니다.',
];

/**
 * 스크립트가 없거나 모션 축소 설정일 때 화면에 남는 완성 문구.
 * index.html의 초기 텍스트, 그리고 같은 h1 안의 sr-only 문구와 같은 문장이어야 한다.
 */
const COMPLETED_INDEX = PHRASES.length - 1;

/** 한 글자 입력·삭제 간격과 완성 후 대기 시간. README에 같은 값을 기록해 둔다. */
const PHASE_DELAY = {
  typing: 70,
  holding: 1600,
  erasing: 34,
};

const REDUCED_MOTION_QUERY = '(prefers-reduced-motion: reduce)';

let textElement = null;
let timerId = 0;

/*
 * 진행 위치는 세 값으로 충분하다. 지금 어떤 문구의(phraseIndex) 몇 글자까지
 * 보이고 있으며(visibleCount) 다음에 무엇을 할지(phase)다. 초기값은 마크업에
 * 이미 그려져 있는 완성 상태와 같다. 그래야 스크립트가 붙는 순간 화면이
 * 첫 글자로 튀지 않고, 대기 → 삭제 → 다음 문구로 자연스럽게 이어진다.
 */
let phraseIndex = COMPLETED_INDEX;
let visibleCount = PHRASES[COMPLETED_INDEX].length;
let phase = 'holding';

const render = () => {
  textElement.textContent = PHRASES[phraseIndex].slice(0, visibleCount);
};

/** 한 단계 진행하고 다음 단계를 예약한다. 다음 지연은 새로 정해진 phase가 결정한다. */
const step = () => {
  if (phase === 'holding') {
    phase = 'erasing';
  } else if (phase === 'typing') {
    visibleCount += 1;

    if (visibleCount === PHRASES[phraseIndex].length) phase = 'holding';
  } else {
    visibleCount -= 1;

    if (visibleCount === 0) {
      phase = 'typing';
      phraseIndex = (phraseIndex + 1) % PHRASES.length;
    }
  }

  render();
  timerId = window.setTimeout(step, PHASE_DELAY[phase]);
};

const start = () => {
  if (timerId) return;

  timerId = window.setTimeout(step, PHASE_DELAY[phase]);
};

/** 타이머만 끊고 진행 위치는 남긴다. 다시 시작하면 멈춘 자리에서 이어진다. */
const stop = () => {
  window.clearTimeout(timerId);
  timerId = 0;
};

/** 모션 축소 설정용. 애니메이션을 멈추되 문구는 완성된 상태로 되돌려 놓는다. */
const stopAtCompletedPhrase = () => {
  stop();

  phraseIndex = COMPLETED_INDEX;
  visibleCount = PHRASES[COMPLETED_INDEX].length;
  phase = 'holding';
  render();
};

export const initTyping = () => {
  textElement = $('.hero__typing-text');

  if (!textElement) return;

  const reducedMotion = window.matchMedia(REDUCED_MOTION_QUERY);

  /*
   * 시작·정지 조건을 한곳에서 판단한다. 조건이 늘어나도 켜고 끄는 지점이
   * 흩어지지 않고, 설정이 도중에 바뀌어도 같은 함수를 다시 부르면 된다.
   */
  const syncRunningState = () => {
    if (reducedMotion.matches) {
      stopAtCompletedPhrase();

      return;
    }

    if (document.hidden) {
      stop();

      return;
    }

    start();
  };

  reducedMotion.addEventListener('change', syncRunningState);
  document.addEventListener('visibilitychange', syncRunningState);

  syncRunningState();
};
