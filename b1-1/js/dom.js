/**
 * DOM을 다룰 때 반복되는 부분만 줄여 주는 얇은 헬퍼.
 * 특정 기능에 대해 아무것도 알지 못하며, 상태도 건드리지 않는다.
 */

/** 조건에 맞는 첫 요소를 찾는다. */
export const $ = (selector, scope = document) => scope.querySelector(selector);

/** 조건에 맞는 모든 요소를 배열로 찾는다. NodeList와 달리 배열 메서드를 바로 쓸 수 있다. */
export const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

const ESCAPE_MAP = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

/**
 * 외부에서 받은 문자열을 HTML에 넣기 전에 escape한다.
 * 템플릿 리터럴로 만든 마크업을 innerHTML로 넣을 때, 값에 섞인 태그가
 * 그대로 실행되지 않도록 막는다.
 */
export const escapeHtml = (value = '') =>
  String(value).replace(/[&<>"']/g, (character) => ESCAPE_MAP[character]);
