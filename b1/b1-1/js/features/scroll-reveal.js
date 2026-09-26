/**
 * 스크롤 등장 애니메이션.
 *
 * 다른 기능과 달리 전역 상태를 거치지 않는다. 한 번 보이고 나면 끝나는
 * 일시적인 시각 효과라 저장할 값도, 다른 곳과 공유할 값도 없기 때문이다.
 * 상태에 넣으면 스크롤할 때마다 전체 렌더가 도는 비용만 생긴다.
 *
 * 관찰 대상은 페이지에 처음부터 있는 정적 요소로 한정한다. 비동기로 그려지는
 * 프로젝트 카드까지 맡으면 projects 기능과 서로를 알아야 해서, 기능끼리
 * 독립적으로 둔다는 규칙이 깨진다.
 */
import { $$ } from '../dom.js';

/** 요소가 이만큼 보이면 등장시킨다. README에 같은 값을 기록해 둔다. */
const REVEAL_THRESHOLD = 0.2;

const REVEAL_SELECTOR = '.reveal';
const VISIBLE_CLASS = 'is-visible';

/**
 * 숨김 스타일을 켜는 스위치.
 * CSS는 이 클래스가 붙어 있을 때만 대상을 숨기므로, 스크립트가 실행되지
 * 않거나 IntersectionObserver를 못 쓰는 환경에서는 콘텐츠가 그냥 보인다.
 */
const ENABLED_CLASS = 'js-reveal';

export const initScrollReveal = () => {
  const targets = $$(REVEAL_SELECTOR);

  if (targets.length === 0 || !('IntersectionObserver' in window)) return;

  document.documentElement.classList.add(ENABLED_CLASS);

  let revealedCount = 0;

  /*
   * 마지막 요소까지 나타나면 이 기능은 할 일이 끝난다.
   * 스위치를 끄면 `.js-reveal .reveal` 규칙이 더는 걸리지 않으므로,
   * 요소마다 남아 있던 opacity·transform과 transition 선언이 함께 사라진다.
   * 지금 화면은 그대로 두면서 끝난 효과의 흔적만 걷어내는 정리다.
   */
  const finish = () => {
    observer.disconnect();
    document.documentElement.classList.remove(ENABLED_CLASS);
    targets.forEach((target) => target.classList.remove(VISIBLE_CLASS));
  };

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(({ target, isIntersecting }) => {
        if (!isIntersecting) return;

        target.classList.add(VISIBLE_CLASS);
        revealedCount += 1;

        // 한 번 보인 요소는 다시 볼 필요가 없으므로 관찰을 끊는다.
        observer.unobserve(target);
      });

      if (revealedCount === targets.length) finish();
    },
    { threshold: REVEAL_THRESHOLD },
  );

  targets.forEach((target) => observer.observe(target));
};
