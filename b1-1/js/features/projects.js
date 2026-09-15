/**
 * GitHub 프로젝트 기능.
 *
 * 요청을 시작하고, 그 결과를 상태로 옮기고, 상태에 맞는 화면을 그린다.
 * 데이터를 가져오는 일은 github-api.js가 맡고, 이 파일은 그것을
 * 언제 부르고 결과를 어떤 상태로 옮길지만 정한다.
 *
 *   loadProjects → status: 'loading' → 목록 요청 → ready / empty / error → renderProjects
 *
 * 사용자에게 보여 주는 상태는 loading·ready·error·empty 네 가지이고 한 번에
 * 하나만 그린다. idle은 부팅 전 내부 상태라 화면을 갖지 않는다.
 *
 * 목록이 네트워크에서 왔는지 저장해 둔 캐시에서 왔는지는 github-api.js가 정하고,
 * 이 파일은 그 결과를 상태로 옮겨 안내 문구를 고르는 데만 쓴다.
 */
import { getState, setState } from '../store.js';
import { $, $$, escapeHtml } from '../dom.js';
import {
  FALLBACK_LANGUAGE,
  loadRepositories,
  normalizeRepository,
  selectPortfolioRepositories,
  sortByRecentPush,
} from '../github-api.js';

const GITHUB_USERNAME = 'b0e2';
const ALL_LANGUAGES = 'all';
const LIVE_DATA = 'live';

/** 로딩 중 카드 자리를 대신할 스켈레톤 장수. */
const SKELETON_COUNT = 3;

const ERROR_MESSAGES = {
  403: '시간당 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.',
  404: `GitHub 사용자 ${GITHUB_USERNAME}의 저장소를 찾을 수 없습니다.`,
  default: '프로젝트를 불러올 수 없습니다.',
};

/**
 * 상태별로 컨테이너에 갈아 끼울 라이브 리전 속성.
 * 마크업에 고정으로 박아 두면 ready에서도 빈 라이브 리전이 남고, 안쪽 상태
 * 마크업에 또 role을 주면 리전이 중첩돼 같은 안내가 두 번 읽힌다.
 * 오류만 assertive로 즉시 끊어 읽고, 나머지는 하던 낭독을 방해하지 않는다.
 */
const LIVE_REGIONS = {
  loading: { role: 'status', live: 'polite' },
  empty: { role: 'status', live: 'polite' },
  error: { role: 'alert', live: 'assertive' },
};

/**
 * 언어 칩 순서는 언어의 성격으로 정한다. 이름 순으로 세우면 Dockerfile이
 * Dart 앞에 오는 식으로 주력 언어가 셸·문서에 밀린다.
 */
const SHELL_AND_BUILD_LANGUAGES = new Set([
  'Shell',
  'Dockerfile',
  'Makefile',
  'CMake',
  'Batchfile',
  'PowerShell',
]);

const DOCUMENT_LANGUAGES = new Set([
  'Markdown',
  'HTML',
  'CSS',
  'SCSS',
  'Less',
  'TeX',
]);

/** 최근 push일 표기. 카드마다 새로 만들지 않도록 포매터를 한 번만 만든다. */
const PUSHED_AT_FORMAT = new Intl.DateTimeFormat('ko-KR', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
});

/** 캐시를 받아 둔 시각. 같은 날 안의 이야기라 시:분이면 충분하다. */
const CACHED_AT_FORMAT = new Intl.DateTimeFormat('ko-KR', {
  hour: '2-digit',
  minute: '2-digit',
});

let filtersElement = null;
let statusElement = null;
let gridElement = null;
let demoElement = null;
let demoNoticeElement = null;
let projectsSection = null;

/** 필터 버튼은 언어 목록이 달라졌을 때만 다시 만든다. 매번 새로 그리면 포커스가 날아간다. */
let renderedLanguageKey = '';

const setProjects = (changes) =>
  setState(({ projects }) => ({ projects: { ...projects, ...changes } }));

const resolveErrorMessage = ({ status }) => ERROR_MESSAGES[status] ?? ERROR_MESSAGES.default;

/** 선택한 언어에 해당하는 항목만 남긴다. 원본 목록은 그대로 두고 볼 것만 골라 낸다. */
const selectByLanguage = (items, language) =>
  language === ALL_LANGUAGES ? items : items.filter((item) => item.language === language);

const rankLanguage = (language) => {
  if (language === FALLBACK_LANGUAGE) return 3;
  if (DOCUMENT_LANGUAGES.has(language)) return 2;
  if (SHELL_AND_BUILD_LANGUAGES.has(language)) return 1;

  return 0;
};

/**
 * 화면에 있는 언어만 칩으로 만든다. 목록을 고정해 두면 없는 언어가 남거나
 * 새 언어가 빠지므로, 보정을 마친 응답에서 그때그때 뽑는다.
 * sort는 순위가 같으면 순서를 유지하므로, 같은 묶음 안에서는 최근 push 순이 남는다.
 */
const collectLanguages = (items) =>
  [...new Set(items.map(({ language }) => language))].sort(
    (a, b) => rankLanguage(a) - rankLanguage(b),
  );

/**
 * 목록 한 번을 채우는 전 과정.
 * 시작할 때 loading으로 바꾸고, 끝나면 결과에 따라 세 갈래로 나뉜다.
 *
 * 유효한 캐시가 있으면 loadRepositories가 요청 없이 바로 돌려주므로 loading이
 * 눈에 보이기 전에 끝난다. 그래도 loading을 거쳐 가는 흐름은 그대로 둔다.
 * 캐시가 없을 때와 상태 전환이 갈라지면 추적할 경로만 늘기 때문이다.
 *
 * forceRefresh는 "다시 시도"에서만 켠다. 캐시를 건너뛰고 반드시 요청을 보낸다.
 */
const loadProjects = async ({ forceRefresh = false } = {}) => {
  setProjects({ status: 'loading', errorMessage: '' });

  try {
    const { repositories, fromCache, savedAt, isStale } = await loadRepositories(GITHUB_USERNAME, {
      forceRefresh,
    });
    const items = sortByRecentPush(
      selectPortfolioRepositories(repositories).map(normalizeRepository),
    );

    setProjects({
      status: items.length > 0 ? 'ready' : 'empty',
      items,
      usedCache: fromCache,
      cachedAt: savedAt,
      cacheIsStale: isStale,
    });
  } catch (error) {
    setProjects({
      status: 'error',
      items: [],
      errorMessage: resolveErrorMessage(error),
      usedCache: false,
      cachedAt: null,
      cacheIsStale: false,
    });
  }
};

/**
 * 상태 화면 안의 버튼 두 개를 위임으로 받는다.
 * 다시 시도는 데모를 보고 있을 때 실데이터로 돌아오기만 한다. 이미 들고 있는
 * 목록을 그대로 쓰면 되므로 데모를 구경했다는 이유로 요청이 늘지 않는다.
 */
const handleStatusClick = (event) => {
  if (event.target.closest('#projects-filter-reset')) {
    setProjects({ language: ALL_LANGUAGES });

    return;
  }

  if (!event.target.closest('#projects-retry')) return;

  if (getState().projects.demo !== LIVE_DATA) {
    setProjects({ demo: LIVE_DATA });

    return;
  }

  // 다시 시도를 눌렀다면 저장해 둔 목록이 아니라 새 응답을 보고 싶다는 뜻이다.
  loadProjects({ forceRefresh: true });
};

/**
 * 안내 줄의 새로고침. 캐시로 그려진 화면에서 강제로 새 요청을 보내는 유일한 경로다.
 * 성공하면 안내가 사라지면서 버튼도 없어지므로 포커스가 갈 곳을 직접 정해 준다.
 */
const handleNoticeClick = async (event) => {
  if (!event.target.closest('#projects-refresh')) return;

  await loadProjects({ forceRefresh: true });

  const refreshButton = $('#projects-refresh');

  if (refreshButton) {
    refreshButton.focus();

    return;
  }

  projectsSection.focus({ preventScroll: true });
};

const handleFilterClick = (event) => {
  const button = event.target.closest('.filter-btn');

  if (!button) return;

  setProjects({ language: button.dataset.language });
};

/** 버튼은 상태마다 다시 그리지 않으므로 컨테이너에서 한 번만 위임해 받는다. */
const handleDemoClick = (event) => {
  const button = event.target.closest('.state-demo__btn');

  if (!button) return;

  setProjects({ demo: button.dataset.demo });
};

export const initProjects = () => {
  filtersElement = $('#project-filters');
  statusElement = $('#projects-status');
  gridElement = $('#projects-grid');
  demoElement = $('#state-demo');
  demoNoticeElement = $('#projects-demo-notice');
  projectsSection = $('#projects');

  // 재시도 버튼과 필터 버튼은 렌더될 때마다 새로 생기므로, 컨테이너에서 위임해 받는다.
  statusElement.addEventListener('click', handleStatusClick);
  filtersElement.addEventListener('click', handleFilterClick);
  demoElement.addEventListener('click', handleDemoClick);
  demoNoticeElement.addEventListener('click', handleNoticeClick);

  loadProjects();
};

const createBadgeMarkup = (isFork) =>
  `<span class="badge ${isFork ? 'badge--fork' : 'badge--origin'}">${
    isFork ? 'FORK' : 'ORIGIN'
  }</span>`;

const createCardMarkup = ({ name, description, language, stars, url, isFork, pushedAt }) => `
  <article class="project-card">
    <div class="project-card__head">
      <h3 class="project-card__title">
        <a class="project-card__link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">
          ${escapeHtml(name)}<span class="project-card__mark" aria-hidden="true">↗</span><span class="sr-only">GitHub에서 열기</span>
        </a>
      </h3>
      ${createBadgeMarkup(isFork)}
    </div>
    <p class="project-card__description">${escapeHtml(description)}</p>
    <p class="project-card__meta">
      <span class="project-card__language">${escapeHtml(language)}</span>
      <span class="project-card__stars"><span aria-hidden="true">★</span> ${stars}<span class="sr-only">개의 스타</span></span>
      <span class="project-card__pushed">최근 푸시 <time datetime="${pushedAt.toISOString()}">${PUSHED_AT_FORMAT.format(pushedAt)}</time></span>
    </p>
  </article>
`;

/*
 * 스켈레톤은 카드가 놓일 자리에 그대로 들어간다. 로딩 문구만 띄우고 자리를
 * 비워 두면 카드가 도착하는 순간 아래 내용이 한 번 밀린다.
 * 읽을 내용이 없는 장식이므로 접근성 트리에서는 감추고, 불러오는 중이라는
 * 사실은 상태 컨테이너의 문구가 대신 알린다.
 */
const createSkeletonMarkup = () =>
  Array.from({ length: SKELETON_COUNT })
    .map(
      () => `
  <div class="skeleton-card" aria-hidden="true">
    <span class="skeleton skeleton--title"></span>
    <span class="skeleton skeleton--text"></span>
    <span class="skeleton skeleton--text skeleton--short"></span>
    <span class="skeleton skeleton--meta"></span>
  </div>
`,
    )
    .join('');

const createStateMarkup = (screen, { errorMessage, isFilteredEmpty }) => {
  if (screen === 'loading') {
    return `<div class="state state--loading">
      <span class="spinner" aria-hidden="true"></span>
      <p class="state__message">저장소를 불러오는 중입니다.</p>
    </div>`;
  }

  if (screen === 'error') {
    return `<div class="state state--error">
      <p class="state__badge">ERROR</p>
      <p class="state__message">${escapeHtml(errorMessage)}</p>
      <button class="btn btn--ghost" id="projects-retry" type="button">다시 시도</button>
    </div>`;
  }

  // 필터 때문에 비었을 때만 되돌릴 곳이 있다. 원본이 0건이면 초기화해도 같은 화면이다.
  if (isFilteredEmpty) {
    return `<div class="state">
      <p class="state__message">선택한 언어에 해당하는 프로젝트가 없습니다.</p>
      <button class="btn btn--ghost" id="projects-filter-reset" type="button">필터 초기화</button>
    </div>`;
  }

  return `<div class="state"><p class="state__message">표시할 프로젝트가 없습니다.</p></div>`;
};

const renderFilters = (hasFilters, items, language) => {
  filtersElement.hidden = !hasFilters;

  if (!hasFilters) {
    filtersElement.innerHTML = '';
    renderedLanguageKey = '';

    return;
  }

  const languages = [ALL_LANGUAGES, ...collectLanguages(items)];
  const languageKey = languages.join('|');

  if (languageKey !== renderedLanguageKey) {
    filtersElement.innerHTML = languages
      .map(
        (value) =>
          `<button class="filter-btn" type="button" data-language="${escapeHtml(value)}">${
            value === ALL_LANGUAGES ? '전체' : escapeHtml(value)
          }</button>`,
      )
      .join('');
    renderedLanguageKey = languageKey;
  }

  $$('.filter-btn', filtersElement).forEach((button) => {
    const isActive = button.dataset.language === language;

    button.classList.toggle('is-active', isActive);
    button.setAttribute('aria-pressed', String(isActive));
  });
};

/** 상태 컨테이너 자체가 라이브 리전이 된다. 내용보다 속성을 먼저 맞춘다. */
const renderLiveRegion = (screen) => {
  const region = LIVE_REGIONS[screen];

  if (!region) {
    statusElement.removeAttribute('role');
    statusElement.removeAttribute('aria-live');

    return;
  }

  statusElement.setAttribute('role', region.role);
  statusElement.setAttribute('aria-live', region.live);
};

/** 지금 보고 있는 상태만 밝게 띄운다. 필터 칩과 같은 aria-pressed 방식이다. */
const renderDemoControl = (demo) => {
  $$('.state-demo__btn', demoElement).forEach((button) => {
    const isActive = button.dataset.demo === demo;

    button.classList.toggle('is-active', isActive);
    button.setAttribute('aria-pressed', String(isActive));
  });
};

/*
 * 카드 영역 위의 안내 한 줄. 데모 안내와 캐시 안내가 같은 자리를 나눠 쓴다.
 * 데모를 보고 있을 때는 지금 화면이 실제 응답이 아니라는 사실이 먼저이므로 그쪽을 띄운다.
 * 데모 중에는 요청을 만들지 않는 것이 규칙이라 새로고침 버튼도 붙이지 않는다.
 *
 * 캐시 안내는 두 가지로 나뉜다. 유효 기간 안의 캐시는 지금 무엇을 보고 있는지만 조용히
 * 알리고, 요청이 실패해 꺼내 쓴 캐시에만 최신이 아닐 수 있다는 경고를 붙인다.
 * 반복 방문마다 경고가 뜨면 정상 동작인데도 화면이 시끄러워진다.
 */
const resolveNotice = (demo, usedCache, cachedAt, cacheIsStale) => {
  if (demo !== LIVE_DATA) {
    return {
      variant: 'demo',
      message: 'STATE DEMO — 화면 확인용 예시입니다. 실제 응답이 아니며 요청을 보내지 않습니다.',
      refreshable: false,
    };
  }

  if (!usedCache || !cachedAt) return null;

  const savedAt = CACHED_AT_FORMAT.format(cachedAt);

  return cacheIsStale
    ? {
        variant: 'stale',
        message: `새 목록을 받지 못해 ${savedAt}에 저장해 둔 목록을 보여 줍니다. 최신이 아닐 수 있습니다.`,
        refreshable: true,
      }
    : { variant: 'cached', message: `${savedAt}에 저장해 둔 목록입니다.`, refreshable: true };
};

/*
 * 내용이 그대로면 다시 그리지 않는다. 필터를 누를 때마다 innerHTML을 새로 넣으면
 * 안내 안의 새로고침 버튼이 매번 교체되어 거기 있던 포커스가 사라진다.
 */
let renderedNoticeKey = '';

const renderNotice = (demo, usedCache, cachedAt, cacheIsStale) => {
  const notice = resolveNotice(demo, usedCache, cachedAt, cacheIsStale);
  const key = notice ? `${notice.variant}|${notice.message}` : '';

  if (key === renderedNoticeKey) return;

  renderedNoticeKey = key;
  demoNoticeElement.hidden = notice === null;
  demoNoticeElement.classList.toggle('projects__demo-notice--stale', notice?.variant === 'stale');
  demoNoticeElement.innerHTML = notice
    ? `<span class="projects__notice-text">${notice.message}</span>${
        notice.refreshable
          ? '<button class="projects__notice-refresh" id="projects-refresh" type="button">새로고침</button>'
          : ''
      }`
    : '';
};

/** 상태를 받아 화면에만 반영한다. */
export const renderProjects = ({ projects }) => {
  const { status, items, language, errorMessage, demo, usedCache, cachedAt, cacheIsStale } =
    projects;

  /*
   * 데모를 고르면 불러온 데이터는 그대로 둔 채 그릴 상태만 바꿔치기한다.
   * items를 비우지 않으므로 실데이터로 돌아올 때 다시 요청할 필요가 없다.
   */
  const dataStatus = demo === LIVE_DATA ? status : demo;
  const visibleItems = dataStatus === 'ready' ? selectByLanguage(items, language) : [];

  /*
   * 필터 결과가 0건인 것도 사용자에게는 빈 화면이다. 응답이 0건인 경우와 같은
   * 화면을 쓰되, 되돌릴 필터가 있을 때만 초기화 버튼을 붙인다.
   */
  const isFilteredEmpty = dataStatus === 'ready' && visibleItems.length === 0;
  const screen = isFilteredEmpty ? 'empty' : dataStatus;

  // 칩은 실제 목록이 있을 때만 둔다. 필터 때문에 비었을 때도 남아야 되돌릴 수 있다.
  renderFilters(dataStatus === 'ready' && items.length > 0, items, language);
  renderDemoControl(demo);
  renderNotice(demo, usedCache, cachedAt, cacheIsStale);

  /*
   * 카드 자리는 언제나 한 가지만 차지한다. ready면 카드, loading이면 스켈레톤,
   * 그 밖에는 비운다. 덕분에 스켈레톤과 실제 카드가 겹쳐 보이는 순간이 없다.
   */
  if (screen === 'ready') {
    gridElement.innerHTML = visibleItems.map(createCardMarkup).join('');
  } else if (screen === 'loading') {
    gridElement.innerHTML = createSkeletonMarkup();
  } else {
    gridElement.innerHTML = '';
  }

  renderLiveRegion(screen);

  statusElement.innerHTML =
    screen === 'ready' || screen === 'idle'
      ? ''
      : createStateMarkup(screen, {
          errorMessage: demo === LIVE_DATA ? errorMessage : ERROR_MESSAGES.default,
          isFilteredEmpty: isFilteredEmpty && language !== ALL_LANGUAGES,
        });
};
