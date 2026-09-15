/**
 * 문의 폼 기능.
 *
 * 입력값과 오류를 모두 상태에 두고, 화면은 그 상태를 비추기만 한다.
 * 오류 메시지를 DOM에서 되읽지 않으므로 "지금 이 폼이 제출 가능한가"의
 * 답이 항상 상태 한 곳에 있다.
 *
 *   input/blur/submit → 검증 → setState → (구독) → renderContactForm → DOM
 *
 * 피드백 시점은 두 단계다. 처음 쓰는 동안에는 아무 말도 하지 않다가,
 * 필드를 한 번 떠난(blur) 뒤부터 그 필드만 글자마다 다시 봐 준다.
 * 다 쓰지도 않은 입력에 "이름을 입력해 주세요"를 들이밀지 않기 위해서다.
 *
 * 검증을 통과하면 Formspree로 실제 전송한다. 요청이 떠 있는 동안과 실패한 뒤가
 * 서로 다른 화면이어야 하므로, 제출 이후의 진행을 status 한 값으로 관리한다.
 *
 *   submit → sending → (성공) sent   → 성공 패널
 *                    → (실패) failed → 입력값을 남긴 채 사유 안내
 */
import { getState, setState } from '../store.js';
import { $ } from '../dom.js';

const FIELDS = ['name', 'email', 'message'];

/**
 * 폼 전송을 받아 주는 Formspree 엔드포인트.
 * 서버 없이 정적 호스팅만으로 메일을 받기 위한 경로이고, 공개돼도 되는 값이다.
 */
const FORM_ENDPOINT = 'https://formspree.io/f/xeaqlyoq';

/**
 * @ 앞뒤가 있고, 점 뒤 최상위 도메인이 두 글자 이상인지까지 본다.
 * 더 엄격하게 굴면 정상적인 주소까지 막게 되므로 여기서 멈춘다.
 */
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i;

/** 메시지 최소 길이. 공백은 세지 않으므로 스페이스로 채워 넘길 수 없다. */
const MESSAGE_MIN_LENGTH = 10;

const REQUIRED_MESSAGES = {
  name: '이름을 입력해 주세요.',
  email: '이메일을 입력해 주세요.',
  message: '메시지를 입력해 주세요.',
};

const EMAIL_FORMAT_MESSAGE = '이메일 형식이 올바르지 않습니다. 예: you@example.com';
const MESSAGE_LENGTH_MESSAGE = `메시지를 공백 제외 ${MESSAGE_MIN_LENGTH}자 이상 적어 주세요.`;

const EMPTY_VALUES = { name: '', email: '', message: '' };
const EMPTY_ERRORS = { name: '', email: '', message: '' };
const UNTOUCHED = { name: false, email: false, message: false };

/**
 * 전송 실패 안내. 사용자가 할 수 있는 일이 달라지므로 사유를 나눈다.
 * 422는 Formspree가 값을 거절한 경우이고, 429는 이 폼의 한도를 넘긴 경우다.
 */
const SEND_ERROR_MESSAGES = {
  422: '입력값을 다시 확인해 주세요.',
  429: '잠시 뒤에 다시 보내 주세요. 짧은 시간에 너무 많이 전송되었습니다.',
  default: '메시지를 보내지 못했습니다. 잠시 후 다시 시도해 주세요.',
};

const MESSAGE_COUNT_ID = 'contact-message-count';

const SENDING_LABEL = '보내는 중…';
const SUBMIT_LABEL = '보내기';

let formElement = null;
let successElement = null;
let alertElement = null;
let messageCountElement = null;
let successNameElement = null;
let successEmailElement = null;
let submitButton = null;

const inputs = {};
const errorElements = {};

const setForm = (changes) => setState(({ form }) => ({ form: { ...form, ...changes } }));

/** 공백을 뺀 실제 글자 수. 길이 판정과 화면 안내가 같은 기준을 쓴다. */
const countWithoutSpaces = (value) => value.replace(/\s/g, '').length;

/** 값 하나를 검증해 오류 문구를 돌려준다. 문제가 없으면 빈 문자열이다. */
export const validateField = (field, value) => {
  const trimmed = value.trim();

  if (!trimmed) return REQUIRED_MESSAGES[field];
  if (field === 'email' && !EMAIL_PATTERN.test(trimmed)) return EMAIL_FORMAT_MESSAGE;
  if (field === 'message' && countWithoutSpaces(value) < MESSAGE_MIN_LENGTH) {
    return MESSAGE_LENGTH_MESSAGE;
  }

  return '';
};

/** 전체 값을 검증해 필드별 오류 문구를 모은다. */
export const validateForm = (values) =>
  Object.fromEntries(FIELDS.map((field) => [field, validateField(field, values[field])]));

/**
 * 입력하는 동안에는 값만 옮기고, 이미 blur를 거친 필드만 다시 검증한다.
 * submitAlert는 건드리지 않는다. 제출 요약이 글자마다 바뀌면
 * role="alert"가 타이핑 도중 하던 낭독을 끊는다.
 */
const handleFieldInput = ({ target: { name, value } }) => {
  const { values, errors, touched } = getState().form;
  const nextValues = { ...values, [name]: value };

  setForm({
    values: nextValues,
    errors: { ...errors, [name]: touched[name] ? validateField(name, value) : '' },
  });
};

/** 필드를 떠나는 순간부터 그 필드는 검증 대상이 된다. */
const handleFieldBlur = ({ target: { name, value } }) => {
  const { errors, touched } = getState().form;

  if (touched[name] && errors[name] === validateField(name, value)) return;

  setForm({
    touched: { ...touched, [name]: true },
    errors: { ...errors, [name]: validateField(name, value) },
  });
};

const resolveSendError = ({ status }) => SEND_ERROR_MESSAGES[status] ?? SEND_ERROR_MESSAGES.default;

/**
 * 검증을 통과한 값을 Formspree로 보낸다.
 * 실패하면 응답 코드를 담은 Error를 던져서, 부르는 쪽이 안내를 고를 수 있게 한다.
 * 네트워크 자체가 끊겼을 때는 fetch가 status 없는 오류를 던지므로 기본 문구로 떨어진다.
 */
const sendMessage = async (values) => {
  const response = await fetch(FORM_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(values),
  });

  if (!response.ok) {
    const error = new Error(`폼 전송 응답 오류 (${response.status})`);

    error.status = response.status;
    throw error;
  }
};

const handleSubmit = async (event) => {
  // 기본 동작은 페이지를 새로 불러오는 것이라 상태가 모두 사라진다.
  event.preventDefault();

  const { values, status } = getState().form;

  // 요청이 떠 있는 동안 다시 눌러도 같은 메시지를 두 번 보내지 않는다.
  if (status === 'sending') return;

  const errors = validateForm(values);
  const invalidFields = FIELDS.filter((field) => errors[field]);

  if (invalidFields.length > 0) {
    /*
     * 제출을 눌렀다면 아직 손대지 않은 필드도 검토 대상이다.
     * 전부 touched로 만들어야 이후 입력에서도 계속 재검증이 돈다.
     */
    setForm({
      touched: { name: true, email: true, message: true },
      errors,
      submitAlert: `확인이 필요한 항목이 ${invalidFields.length}개 있습니다.`,
      status: 'idle',
    });

    // 요약은 개수만 알린다. 무엇이 틀렸는지는 이동한 필드의 안내가 설명한다.
    inputs[invalidFields[0]].focus();

    return;
  }

  setForm({ errors: { ...EMPTY_ERRORS }, submitAlert: '', status: 'sending' });

  try {
    await sendMessage(values);

    setForm({ status: 'sent', submitAlert: '' });

    // 방금까지 포커스가 있던 제출 버튼이 숨겨지므로, 갈 곳을 직접 정해 준다.
    successElement.focus();
  } catch (error) {
    /*
     * 값은 그대로 남긴다. 보내지 못한 것은 네트워크 사정이지 입력의 잘못이 아니므로,
     * 사용자가 같은 내용을 다시 쓰게 만들 이유가 없다. 포커스도 제출 버튼에 그대로 둔다.
     */
    setForm({ status: 'failed', submitAlert: resolveSendError(error) });
  }
};

/** 성공 패널에서 되돌아오면 폼은 처음 상태여야 한다. */
const handleReset = () => {
  setForm({
    values: { ...EMPTY_VALUES },
    touched: { ...UNTOUCHED },
    errors: { ...EMPTY_ERRORS },
    submitAlert: '',
    status: 'idle',
  });

  inputs.name.focus();
};

export const initContactForm = () => {
  formElement = $('#contact-form');
  successElement = $('#contact-success');
  alertElement = $('#contact-alert');
  messageCountElement = $(`#${MESSAGE_COUNT_ID}`);
  successNameElement = $('#contact-success-name');
  successEmailElement = $('#contact-success-email');
  submitButton = $('#contact-submit');

  FIELDS.forEach((field) => {
    inputs[field] = $(`#contact-${field}`);
    errorElements[field] = $(`#contact-${field}-error`);

    inputs[field].addEventListener('input', handleFieldInput);
    inputs[field].addEventListener('blur', handleFieldBlur);
  });

  formElement.addEventListener('submit', handleSubmit);
  $('#contact-reset').addEventListener('click', handleReset);
};

/**
 * 입력을 설명하는 요소만 aria-describedby로 잇는다.
 * 빈 문단까지 걸어 두면 읽을 것이 없는데도 설명이 있다고 알리게 된다.
 */
const describedBy = (field, hasError) => {
  const ids = field === 'message' ? [MESSAGE_COUNT_ID] : [];

  if (hasError) ids.push(`contact-${field}-error`);

  return ids.join(' ');
};

/** 상태를 받아 화면에만 반영한다. 여기서 상태를 바꾸지 않는다. */
export const renderContactForm = ({ form: { values, errors, submitAlert, status } }) => {
  const isSending = status === 'sending';
  const isSent = status === 'sent';

  FIELDS.forEach((field) => {
    const input = inputs[field];
    const message = errors[field];

    // 값이 같은데도 다시 대입하면 입력 중 커서가 끝으로 튄다.
    if (input.value !== values[field]) {
      input.value = values[field];
    }

    errorElements[field].textContent = message;
    input.setAttribute('aria-invalid', String(Boolean(message)));

    const ids = describedBy(field, Boolean(message));

    if (ids) {
      input.setAttribute('aria-describedby', ids);
    } else {
      input.removeAttribute('aria-describedby');
    }
  });

  messageCountElement.textContent = `공백 제외 ${countWithoutSpaces(values.message)}자 / 최소 ${MESSAGE_MIN_LENGTH}자`;

  // 같은 문구를 다시 넣어도 라이브 리전은 새 알림으로 읽는다. 달라졌을 때만 쓴다.
  if (alertElement.textContent !== submitAlert) {
    alertElement.textContent = submitAlert;
  }

  /*
   * 전송 중에는 버튼을 잠가 같은 메시지가 두 번 나가지 않게 하고,
   * 글자로도 진행을 알린다. 핸들러에서도 한 번 더 막지만, 눌리는 버튼을
   * 그대로 두면 아무 일도 일어나지 않는 것처럼 보인다.
   */
  submitButton.disabled = isSending;
  submitButton.textContent = isSending ? SENDING_LABEL : SUBMIT_LABEL;

  /*
   * 폼과 성공 패널은 둘 다 DOM에 남아 있고 보이는 쪽만 바뀐다.
   * 값을 지우지 않으므로 성공 패널이 방금 보낸 이름과 이메일을 그대로 쓸 수 있다.
   */
  formElement.hidden = isSent;
  successElement.hidden = !isSent;

  if (isSent) {
    successNameElement.textContent = values.name;
    successEmailElement.textContent = values.email;
  }
};
