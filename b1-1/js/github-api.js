/**
 * GitHub API 계층.
 *
 * 요청, 오류, 정규화, 그리고 캐시까지 "데이터를 얻는 방법"을 맡는다.
 * 전역 상태를 읽지도 바꾸지도 않는다. 상태를 언제 어떻게 바꿀지는 부르는 쪽이 정한다.
 *
 * 캐시가 여기 있는 이유는 그것이 화면의 상태가 아니라 데이터를 얻는 경로이기 때문이다.
 * 부르는 쪽 입장에서는 "저장소 목록을 달라"는 요청 하나이고, 그 답이 네트워크에서 왔는지
 * 브라우저 저장소에서 왔는지는 같은 질문에 대한 두 경로일 뿐이다. features/projects.js가
 * 캐시를 직접 다루면 상태를 옮기는 일과 데이터를 구하는 일이 한 파일에서 섞인다.
 * 저장하는 값도 화면용으로 가공하기 전의 원본 응답이라, 이 계층 밖으로 새어 나가지 않는다.
 *
 * 화면에 맞춘 판단은 여기 두지 않는다. 날짜를 어떤 형식으로 보여 줄지,
 * 언어 칩을 어떤 순서로 세울지, 배지에 무슨 글자를 쓸지는 features/projects.js가 정한다.
 */
const API_ORIGIN = 'https://api.github.com';

const REQUEST_HEADERS = { Accept: 'application/vnd.github+json' };

const FALLBACK_DESCRIPTION = '아직 설명이 없는 저장소입니다.';

/**
 * 캐시를 믿는 시간. 무인증 GitHub API는 시간당 60회뿐이라 새로고침 몇 번이면 바닥난다.
 * 10분은 반복 방문의 요청을 거의 없애면서도, 저장소를 갱신한 뒤 화면에 반영되기까지
 * 오래 기다리지 않는 절충값이다. README에 같은 값을 기록해 둔다.
 */
const CACHE_TTL = 10 * 60 * 1000;

/** 계정이 바뀌면 옛 계정의 목록을 읽지 않도록 키에 사용자명을 넣는다. */
const cacheKey = (username) => `portfolio-repos:${username}`;

/**
 * 언어 판정이 비어 있는 저장소가 모이는 자리.
 * 화면과 필터 칩이 같은 문자열을 써야 하므로 밖에서도 참조할 수 있게 내보낸다.
 */
export const FALLBACK_LANGUAGE = '기타';

/**
 * GitHub의 언어 판정은 저장소 파일 구성에서 자동으로 나오기 때문에 실제와
 * 어긋날 수 있다. 아래 두 fork는 Flutter 프로젝트인데 판정 결과가 비어 있어
 * 화면에서 언어를 잃는다. 확인된 저장소만 이름으로 바로잡고, 그 밖의 빈 값은
 * 추측하지 않고 기타로 모은다. 규칙을 넓히면 API가 판정을 고쳤을 때
 * 이 표가 조용히 틀린 값을 덮어쓰게 된다.
 */
const LANGUAGE_OVERRIDES = {
  'sallae-mallae-app': 'Dart',
  'ai-debate-front': 'Dart',
};

/*
 * 저장소 접근은 세 군데에서 따로 막힐 수 있다. 브라우저 설정이 localStorage를
 * 아예 차단하거나, 저장 용량이 넘치거나, 남아 있던 값이 깨져 있거나.
 * 셋을 각각 감싸 두면 어느 쪽이 실패해도 캐시만 건너뛰고 요청 흐름은 그대로 돈다.
 */
const readStoredCache = (username) => {
  try {
    return localStorage.getItem(cacheKey(username));
  } catch {
    return null;
  }
};

const writeStoredCache = (username, value) => {
  try {
    localStorage.setItem(cacheKey(username), value);
  } catch {
    // 캐시는 최적화라서, 저장에 실패해도 이번에 받아 온 목록은 그대로 쓴다.
  }
};

/**
 * 저장된 값은 사용자가 직접 고칠 수 있는 자리에 있으므로 그대로 믿지 않는다.
 * 화면을 그리는 데 실제로 필요한 필드만 확인해, 깨진 값이 렌더까지 흘러가지 않게 한다.
 */
const isUsableRepository = (repository) =>
  repository !== null
  && typeof repository === 'object'
  && typeof repository.name === 'string'
  && !Number.isNaN(Date.parse(repository.pushed_at));

const parseCache = (raw) => {
  if (!raw) return null;

  try {
    const { savedAt, repositories } = JSON.parse(raw);

    if (typeof savedAt !== 'number' || !Array.isArray(repositories)) return null;
    if (!repositories.every(isUsableRepository)) return null;

    return { savedAt, repositories };
  } catch {
    return null;
  }
};

const readCache = (username) => parseCache(readStoredCache(username));

/**
 * 저장소 목록을 가져온다.
 * 실패하면 응답 코드를 담은 Error를 던져서, 부르는 쪽이 상황별로 안내를 고를 수 있게 한다.
 */
export const fetchRepositories = async (username) => {
  const endpoint = `${API_ORIGIN}/users/${encodeURIComponent(username)}/repos?sort=updated&per_page=60`;
  const response = await fetch(endpoint, { headers: REQUEST_HEADERS });

  if (!response.ok) {
    const error = new Error(`GitHub API 응답 오류 (${response.status})`);

    error.status = response.status;
    throw error;
  }

  return response.json();
};

/**
 * 저장소 목록을 얻는 하나의 입구. 부르는 쪽은 데이터가 어디서 왔는지 신경 쓰지 않는다.
 *
 *   유효한 캐시가 있으면      → 요청하지 않고 그대로 돌려준다
 *   없거나 만료됐으면         → 요청하고, 성공하면 캐시를 갱신한다
 *   요청이 실패했는데 캐시가 있으면 → 만료됐더라도 그것으로 대신한다
 *   요청도 실패하고 캐시도 없으면  → 예외를 그대로 올려보낸다
 *
 * 세 번째 갈래가 이 변경의 핵심이다. 한도를 다 쓴 방문자에게 오류 화면만 보여 주는 것보다,
 * 조금 지난 목록이라도 보여 주고 최신이 아닐 수 있다고 알리는 편이 낫다.
 *
 * 돌려주는 값의 isStale이 두 캐시 경로를 갈라 준다. 유효 기간 안의 캐시(false)와
 * 요청이 실패해 어쩔 수 없이 꺼내 쓴 캐시(true)는 사용자에게 알릴 내용이 다르다.
 *
 * forceRefresh는 "새로고침"용이다. 캐시를 읽지 않고 반드시 요청을 보내되,
 * 그 요청마저 실패하면 남아 있는 캐시로 되돌아간다.
 */
export const loadRepositories = async (username, { forceRefresh = false } = {}) => {
  const cached = forceRefresh ? null : readCache(username);

  if (cached && Date.now() - cached.savedAt < CACHE_TTL) {
    return {
      repositories: cached.repositories,
      fromCache: true,
      savedAt: cached.savedAt,
      isStale: false,
    };
  }

  try {
    const repositories = await fetchRepositories(username);

    writeStoredCache(username, JSON.stringify({ savedAt: Date.now(), repositories }));

    return { repositories, fromCache: false, savedAt: null, isStale: false };
  } catch (error) {
    // forceRefresh였다면 위에서 읽지 않았으므로 여기서 한 번 더 확인한다.
    const fallback = cached ?? readCache(username);

    if (!fallback) throw error;

    return {
      repositories: fallback.repositories,
      fromCache: true,
      savedAt: fallback.savedAt,
      isStale: true,
    };
  }
};

/** 응답에서 화면에 쓸 값만 뽑고, 비어 있을 수 있는 필드는 대체 텍스트로 채운다. */
export const normalizeRepository = ({
  id,
  name,
  description,
  language,
  fork,
  stargazers_count: stars,
  html_url: url,
  pushed_at: pushedAt,
}) => ({
  id,
  name,
  description: description?.trim() || FALLBACK_DESCRIPTION,
  language: LANGUAGE_OVERRIDES[name] || language || FALLBACK_LANGUAGE,
  isFork: Boolean(fork),
  stars,
  url,
  // 표시 형식은 화면이 정하므로 여기서는 비교 가능한 Date로만 넘긴다.
  pushedAt: new Date(pushedAt),
});

/**
 * fork도 포트폴리오에 싣고 배지로 구분한다. 남의 코드에서 출발한 작업도
 * 무엇을 했는지 보여 주는 기록이기 때문이다.
 * 다만 archived는 읽기 전용으로 멈춘 저장소라 최근 활동 순 목록에 섞지 않는다.
 */
export const selectPortfolioRepositories = (repositories) =>
  repositories.filter(({ archived }) => !archived);

/**
 * 최근에 밀어 넣은 저장소가 위로 온다.
 * 목록의 기준은 `updated_at`이 아니라 `pushed_at`이다. `updated_at`은 설명이나
 * 별표처럼 코드와 무관한 변경으로도 갱신되므로 "최근 작업한 순서"와 어긋난다.
 * 원본을 건드리지 않도록 복사한 뒤 정렬한다.
 */
export const sortByRecentPush = (repositories) =>
  [...repositories].sort((a, b) => b.pushedAt - a.pushedAt);
