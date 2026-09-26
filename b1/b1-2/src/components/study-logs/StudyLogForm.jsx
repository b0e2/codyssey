import Button from '../ui/Button.jsx'
import FormField from '../ui/FormField.jsx'
import { TextField } from '../ui/FormField.jsx'
import TagInput from './TagInput.jsx'
import {
  DURATION_MINUTES_MAX,
  DURATION_MINUTES_MIN,
  TAGS_MAX,
} from '../../lib/studyLogValidation.js'
import { formatUnderstanding } from '../../lib/studyLogFormatters.js'

const UNDERSTANDING_OPTIONS = [1, 2, 3, 4, 5].map((level) => ({
  value: level,
  label: `${level} · ${formatUnderstanding(level)}`,
}))

// 값과 오류를 모두 바깥에서 받는다. Supabase 를 모르고 스스로 저장하지 않으므로
// 등록과 수정이 같은 컴포넌트를 그대로 쓴다.
export default function StudyLogForm({
  values,
  errors,
  touched = {},
  isSubmitting,
  submitError,
  submitLabel = '저장',
  today,
  tagSuggestions = [],
  onChange,
  onBlur,
  onTagsChange,
  onSubmit,
  onCancel,
}) {
  // 아직 건드리지 않은 필드의 오류는 제출 전까지 보여주지 않는다.
  const shown = (name) => (touched[name] ? errors[name] : undefined)
  const common = (name) => ({ name, value: values[name], error: shown(name), onChange, onBlur })

  return (
    <form className="form" onSubmit={onSubmit} noValidate>
      {submitError ? (
        <p className="form__alert" role="alert">
          {submitError}
        </p>
      ) : null}

      <section className="form__card">
        <h2 className="form__card-title">무엇을 배웠나요</h2>

        <TextField
          {...common('title')}
          label="제목"
          required
          maxLength={80}
          count={`${values.title.length}/80`}
          placeholder="오늘 배운 것을 한 줄로 적어주세요"
        />

        <FormField
          id="tags"
          label="태그"
          required
          error={shown('tags')}
          hint={`엔터나 쉼표로 확정합니다. 최대 ${TAGS_MAX}개.`}
        >
          <TagInput
            tags={values.tags}
            maxTags={TAGS_MAX}
            error={shown('tags')}
            suggestions={tagSuggestions}
            onChange={onTagsChange}
          />
        </FormField>

        <TextField {...common('study_date')} label="학습한 날짜" required type="date" max={today} />
      </section>

      <section className="form__card">
        <h2 className="form__card-title">배운 내용</h2>

        <TextField
          {...common('content')}
          as="textarea"
          label="학습 내용"
          required
          rows={8}
          maxLength={3000}
          count={`${values.content.length}/3000`}
          placeholder="무엇을 어떻게 이해했는지 적어주세요"
        />

        <TextField
          {...common('resource_url')}
          label="참고 링크"
          type="url"
          hint="선택 항목입니다."
          placeholder="https://"
        />
      </section>

      <section className="form__card">
        <h2 className="form__card-title">학습 상태</h2>

        <div className="form__row">
          <TextField
            {...common('duration_minutes')}
            label="학습 시간(분)"
            required
            type="number"
            min={DURATION_MINUTES_MIN}
            max={DURATION_MINUTES_MAX}
            step={5}
            placeholder="60"
          />
          <TextField
            {...common('understanding')}
            as="select"
            label="이해도"
            required
            options={UNDERSTANDING_OPTIONS}
          />
        </div>

        <label className="checkbox">
          <input type="checkbox" name="is_completed" checked={values.is_completed} onChange={onChange} />
          학습을 마쳤어요
        </label>

        {/* 완료로 표시할 때만 회고를 필수로 받는다.
            기록과 회고를 함께 남기는 것이 이 서비스의 목적이다. */}
        <TextField
          {...common('reflection')}
          as="textarea"
          label="회고"
          required={values.is_completed}
          rows={4}
          maxLength={2000}
          count={`${values.reflection.length}/2000`}
          hint={values.is_completed ? '완료로 표시하려면 10자 이상 적어주세요.' : '선택 항목입니다.'}
          placeholder="어려웠던 점이나 다음에 해볼 것을 적어주세요"
        />
      </section>

      <div className="form__actions">
        {onCancel ? (
          <Button variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            취소
          </Button>
        ) : null}
        <Button type="submit" variant="primary" isLoading={isSubmitting} loadingLabel="저장 중">
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}
