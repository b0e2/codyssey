import { useState } from 'react'
import TagBadge from '../ui/TagBadge.jsx'
import { normalizeTag, normalizeTags } from '../../lib/studyLogValidation.js'

// 엔터나 쉼표로 태그를 확정한다.
// 정규화와 중복 판정은 검증 계층의 순수 함수에 맡기고
// 여기서는 입력 상호작용만 다룬다.
export default function TagInput({ tags = [], maxTags = 5, error, suggestions = [], onChange, id = 'tags' }) {
  const [draft, setDraft] = useState('')
  const isFull = tags.length >= maxTags

  function commit(raw) {
    const tag = normalizeTag(raw)
    if (!tag || isFull) return

    const next = normalizeTags([...tags, tag])
    // 이미 있는 태그면 개수가 늘지 않는다. 그때는 입력만 비운다.
    if (next.length !== tags.length) onChange(next)
    setDraft('')
  }

  function handleKeyDown(event) {
    // 한글처럼 글자를 조합하는 입력기는 조합을 확정할 때도 Enter 를 보낸다.
    // 그 Enter 는 글자를 끝내는 것이지 태그를 끝내는 것이 아니다.
    // 걸러내지 않으면 '사탕' 을 칠 때 확정 전 값과 남은 글자가 각각 태그가 된다.
    if (event.nativeEvent.isComposing) return

    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault()
      commit(draft)
      return
    }
    // 입력이 비어 있을 때 지우면 마지막 태그를 뺀다.
    if (event.key === 'Backspace' && !draft && tags.length > 0) {
      onChange(tags.slice(0, -1))
    }
  }

  const available = suggestions.filter(
    (tag) => !tags.some((selected) => selected.toLowerCase() === tag.toLowerCase()),
  )

  return (
    <div className="tag-input-wrap">
      <div className={error ? 'tag-input tag-input--invalid' : 'tag-input'}>
        {tags.map((tag) => (
          <span key={tag} className="tag-input__chip">
            #{tag}
            <button
              type="button"
              className="tag-input__remove"
              aria-label={`${tag} 태그 삭제`}
              onClick={() => onChange(tags.filter((item) => item !== tag))}
            >
              ×
            </button>
          </span>
        ))}

        <input
          id={id}
          type="text"
          className="tag-input__field"
          value={draft}
          disabled={isFull}
          placeholder={isFull ? `태그는 ${maxTags}개까지 넣을 수 있어요` : '태그를 입력하고 엔터'}
          aria-invalid={error ? true : undefined}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => commit(draft)}
        />
      </div>

      {available.length > 0 && !isFull ? (
        <div className="tag-input__suggestions">
          <span className="tag-input__suggestions-label">이미 쓴 태그</span>
          {available.slice(0, 8).map((tag) => (
            <TagBadge key={tag} tag={tag} size="sm" onClick={() => commit(tag)} />
          ))}
        </div>
      ) : null}
    </div>
  )
}
