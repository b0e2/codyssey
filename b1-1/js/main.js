/**
 * 애플리케이션 진입점.
 *
 * 기능 모듈을 초기화하고 렌더러를 구독시키는 조립 지점이다.
 * 어떤 규칙도 여기서 갖지 않는다. 각 기능이 자기 상태와 렌더를 소유하고,
 * 이 파일은 그것들을 순서대로 불러 줄 뿐이다.
 */
import { getState, subscribe } from './store.js';
import { initTheme, renderTheme } from './features/theme.js';
import { initNavigation, renderNavigation } from './features/navigation.js';
import { initScrollReveal } from './features/scroll-reveal.js';
import { initTyping } from './features/typing.js';
import { initProjects, renderProjects } from './features/projects.js';
import { initContactForm, renderContactForm } from './features/contact-form.js';

/**
 * 상태가 바뀔 때마다 각 기능의 렌더러에게 현재 상태를 넘긴다.
 * 무엇을 어떻게 그릴지는 각 렌더러가 스스로 판단한다.
 */
const renderApp = (state) => {
  renderTheme(state);
  renderNavigation(state);
  renderProjects(state);
  renderContactForm(state);
};

const initializeApp = () => {
  initTheme();
  initNavigation();
  initScrollReveal();
  initTyping();
  initProjects();
  initContactForm();

  subscribe(renderApp);
  renderApp(getState());
};

document.addEventListener('DOMContentLoaded', initializeApp);
