/**
 * 내비게이션 기능.
 *
 * 햄버거 메뉴와 앵커 이동을 담당한다. 등장 애니메이션은 성격이 다른
 * 일시 효과라 features/scroll-reveal.js가 따로 맡는다.
 *
 *   click → 핸들러 → setState → (구독) → renderNavigation → DOM
 */
import { getState, setState } from '../store.js';
import { $, $$ } from '../dom.js';

/** 768px부터는 메뉴가 헤더 안으로 들어오므로 햄버거 상태를 유지할 이유가 없다. */
const DESKTOP_QUERY = '(min-width: 768px)';

/** 헤더 배경이 바뀌는 스크롤 위치. README에 같은 값을 기록해 둔다. */
const HEADER_THRESHOLD = 60;

/** 맨 위로 버튼이 나타나는 스크롤 위치. 이 값을 넘어야 보인다. README에 같은 값을 기록해 둔다. */
const TOP_BUTTON_THRESHOLD = 320;

/**
 * 모션을 줄이도록 설정한 사용자에게는 부드러운 이동 대신 즉시 이동시킨다.
 * CSS의 scroll-behavior는 스크립트가 지정한 behavior에 덮이므로, 이동을 만드는
 * 쪽에서 직접 확인해야 한다. 같은 확인이 typing에도 필요하지만 대응 방식이
 * 서로 달라(여기는 이동 방식, 저기는 실행 여부) 각 기능이 따로 판단한다.
 */
const REDUCED_MOTION_QUERY = '(prefers-reduced-motion: reduce)';

const resolveScrollBehavior = () =>
  window.matchMedia(REDUCED_MOTION_QUERY).matches ? 'auto' : 'smooth';

let header = null;
let menu = null;
let menuToggle = null;
let topButton = null;
let scrollFrameRequested = false;

/** navigation 조각만 바꾼다. 나머지 상태는 그대로 둔다. */
const setNavigation = (changes) =>
  setState(({ navigation }) => ({ navigation: { ...navigation, ...changes } }));

const closeMenu = () => {
  if (!getState().navigation.menuOpen) return;

  setNavigation({ menuOpen: false });
};

const handleMenuToggleClick = () => {
  const { menuOpen } = getState().navigation;

  setNavigation({ menuOpen: !menuOpen });
};

/**
 * 앵커 링크의 기본 점프를 막고 부드럽게 이동시킨다.
 * 이동 뒤 대상 섹션으로 포커스를 옮겨 키보드 사용자도 같은 위치에서 이어갈 수 있게 한다.
 */
const handleAnchorClick = (event) => {
  const targetId = event.currentTarget.getAttribute('href').slice(1);
  const target = document.getElementById(targetId);

  if (!target) return;

  event.preventDefault();
  closeMenu();

  target.scrollIntoView({ behavior: resolveScrollBehavior() });
  target.focus({ preventScroll: true });
};

const handleTopButtonClick = () => {
  window.scrollTo({ top: 0, behavior: resolveScrollBehavior() });
};

/**
 * 열린 메뉴는 Escape로도 닫는다. 메뉴를 연 뒤 링크를 고르지 않고 빠져나오려는
 * 키보드 사용자에게 햄버거로 되돌아가는 것 말고 다른 출구를 준다.
 * 닫은 뒤 포커스를 햄버거로 돌려 주지 않으면 사라진 요소에 포커스가 남는다.
 */
const handleKeydown = (event) => {
  if (event.key !== 'Escape') return;
  if (!getState().navigation.menuOpen) return;

  closeMenu();
  menuToggle.focus();
};

/**
 * 스크롤 위치를 임계값 기준의 boolean 두 개로 줄인 뒤,
 * 실제로 달라졌을 때만 상태를 바꾼다. 스크롤 한 번에 수십 번 호출되는
 * 핸들러에서 매번 setState를 부르면 화면이 바뀌지 않는데도 렌더가 반복된다.
 */
const syncScrollState = () => {
  const offset = window.scrollY;
  const isScrolled = offset >= HEADER_THRESHOLD;
  const showTopButton = offset > TOP_BUTTON_THRESHOLD;
  const { navigation } = getState();

  if (navigation.isScrolled === isScrolled && navigation.showTopButton === showTopButton) return;

  setNavigation({ isScrolled, showTopButton });
};

/**
 * scroll 이벤트는 브라우저가 매우 잦게 발생시키므로,
 * 다음 화면을 그리기 직전에 한 번만 처리하도록 묶는다.
 */
const handleScroll = () => {
  if (scrollFrameRequested) return;

  scrollFrameRequested = true;
  requestAnimationFrame(() => {
    scrollFrameRequested = false;
    syncScrollState();
  });
};

/** 데스크톱 폭으로 넓어지면 열려 있던 모바일 메뉴 상태를 정리한다. */
const handleDesktopChange = (event) => {
  if (event.matches) closeMenu();
};

export const initNavigation = () => {
  header = $('#site-header');
  menu = $('#nav-menu');
  menuToggle = $('#nav-toggle');
  topButton = $('#top-button');

  menuToggle.addEventListener('click', handleMenuToggleClick);
  topButton.addEventListener('click', handleTopButtonClick);

  $$('a[href^="#"]:not(.skip-link)').forEach((anchor) => {
    anchor.addEventListener('click', handleAnchorClick);
  });

  document.addEventListener('keydown', handleKeydown);
  window.matchMedia(DESKTOP_QUERY).addEventListener('change', handleDesktopChange);
  window.addEventListener('scroll', handleScroll, { passive: true });

  // 새로고침으로 스크롤 위치가 복원된 경우를 대비해 초기 상태를 맞춘다.
  syncScrollState();
};

/** 상태를 받아 화면에만 반영한다. */
export const renderNavigation = ({ navigation: { menuOpen, isScrolled, showTopButton } }) => {
  menu.classList.toggle('active', menuOpen);
  menuToggle.setAttribute('aria-expanded', String(menuOpen));
  menuToggle.setAttribute('aria-label', menuOpen ? '메뉴 닫기' : '메뉴 열기');

  header.classList.toggle('is-scrolled', isScrolled);
  topButton.classList.toggle('is-visible', showTopButton);
};
