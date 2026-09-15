/**
 * 다크 모드 기능.
 *
 * 이 파일 하나에 테마의 초기값 결정, 이벤트 연결, 상태 변경, 화면 반영이
 * 모두 들어 있다. 기능을 고칠 때 이 파일만 열면 되고, 아래로 읽어 내려가면
 * 이벤트에서 화면까지의 흐름이 그대로 이어진다.
 *
 *   click → handleToggleClick → setState → (구독) → renderTheme → DOM
 */
import { getState, setState } from '../store.js';
import { $ } from '../dom.js';

const STORAGE_KEY = 'portfolio-theme';
const THEMES = ['light', 'dark'];

let toggleButton = null;

/** localStorage는 브라우저 설정에 따라 막힐 수 있으므로 실패를 감수한다. */
const readStoredTheme = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);

    return THEMES.includes(stored) ? stored : null;
  } catch {
    return null;
  }
};

const writeStoredTheme = (theme) => {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // 저장에 실패해도 이번 방문 동안의 테마 전환은 그대로 동작한다.
  }
};

/*
 * 운영체제의 밝은/어두운 모드. 첫 값을 읽을 때와 도중에 바뀌는 것을 지켜볼 때
 * 같은 객체를 쓰므로 한 번만 만들어 둔다.
 */
const systemScheme = window.matchMedia('(prefers-color-scheme: dark)');

/**
 * 저장값은 "마지막으로 정해진 테마"다. 토글로 고른 값이든 운영체제를 따라간
 * 값이든 같은 자리에 남으므로, 다시 열었을 때 마지막 화면을 그대로 이어간다.
 * 저장값이 없는 첫 방문에만 운영체제 설정을 읽는다.
 */
const resolveInitialTheme = () => readStoredTheme() ?? (systemScheme.matches ? 'dark' : 'light');

const applyTheme = (theme) => {
  setState({ theme });
  writeStoredTheme(theme);
};

const handleToggleClick = () => {
  const { theme } = getState();

  applyTheme(theme === 'dark' ? 'light' : 'dark');
};

/**
 * 페이지를 연 채로 운영체제 설정이 바뀌면 화면도 따라간다.
 *
 * 저장값이 있어도 따라간다. 규칙은 하나다 — 마지막에 들어온 신호가 지금 테마다.
 * 운영체제를 바꾸는 것도 사용자가 직접 한 행동이므로, 예전에 누른 토글보다
 * 더 최근의 의사로 본다. 저장된 선택을 우선하면 토글을 한 번 누른 뒤로는
 * 시스템을 따라갈 길이 없어지고, UI에는 그 상태를 풀 방법도 없다.
 *
 * 따라간 값도 저장한다. 저장하지 않으면 새로고침에서 옛 선택으로 되돌아가
 * 아무것도 누르지 않았는데 화면이 저절로 바뀐 것처럼 보인다.
 */
const handleSystemSchemeChange = ({ matches }) => {
  applyTheme(matches ? 'dark' : 'light');
};

export const initTheme = () => {
  toggleButton = $('#theme-toggle');

  setState({ theme: resolveInitialTheme() });
  toggleButton.addEventListener('click', handleToggleClick);
  systemScheme.addEventListener('change', handleSystemSchemeChange);
};

/** 상태를 받아 화면에만 반영한다. 여기서 상태를 바꾸지 않는다. */
export const renderTheme = ({ theme }) => {
  const isDark = theme === 'dark';

  document.documentElement.dataset.theme = theme;
  toggleButton.setAttribute('aria-pressed', String(isDark));
  toggleButton.setAttribute('aria-label', isDark ? '라이트 모드로 전환' : '다크 모드로 전환');
};
