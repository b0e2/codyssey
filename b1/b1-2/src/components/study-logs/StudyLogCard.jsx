import { memo } from 'react'
import { Link } from 'react-router-dom'
import StatusBadge from '../ui/StatusBadge.jsx'
import TagBadge from '../ui/TagBadge.jsx'
import { getTagInitial, getTagTone, formatStudyDate } from '../../lib/studyLogFormatters.js'

const VISIBLE_TAGS = 2

// 목록 한 행. 왼쪽 시각 영역은 이미지 업로드 대신
// 대표 태그의 색과 이니셜로 채운다.
//
// 카드 전체를 링크로 감싸지 않는다. 안에 수정·삭제 버튼이 있어
// 링크 안에 버튼이 중첩되기 때문이다. 제목만 링크로 둔다.
//
// memo 로 감싼 이유: 목록 화면에서 검색어를 한 글자 칠 때마다 화면이
// 다시 그려지는데, 그때 카드 내용은 바뀌지 않는다. 카드가 여러 장이므로
// 건너뛸 값이 있다. 넘기는 콜백도 useCallback 으로 고정해야 효과가 있다.
function StudyLogCard({ log, compact = false, isDeleting = false, onEdit, onDelete }) {
  const [leadTag] = log.tags ?? []
  const visibleTags = (log.tags ?? []).slice(0, VISIBLE_TAGS)
  const restCount = (log.tags ?? []).length - visibleTags.length

  return (
    <article className="log-row">
      <span className={`log-row__thumb log-row__thumb--${getTagTone(leadTag)}`} aria-hidden="true">
        {getTagInitial(leadTag)}
      </span>

      <div className="log-row__body">
        <Link to={`/logs/${log.id}`} className="log-row__title">
          {log.title}
        </Link>
        {compact ? null : <p className="log-row__summary">{log.content}</p>}
      </div>

      <div className="log-row__tags">
        {visibleTags.map((tag) => (
          <TagBadge key={tag} tag={tag} size="sm" />
        ))}
        {restCount > 0 ? <span className="log-row__more">+{restCount}</span> : null}
      </div>

      <time className="log-row__date" dateTime={log.study_date}>
        {formatStudyDate(log.study_date)}
      </time>

      <StatusBadge isCompleted={log.is_completed} size="sm" />

      {onEdit || onDelete ? (
        <div className="log-row__actions">
          {onEdit ? (
            <button type="button" className="button button--secondary button--sm" onClick={() => onEdit(log)}>
              수정
            </button>
          ) : null}
          {onDelete ? (
            <button
              type="button"
              className="button button--danger button--sm"
              disabled={isDeleting}
              onClick={() => onDelete(log)}
            >
              {isDeleting ? '삭제 중' : '삭제'}
            </button>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}

export default memo(StudyLogCard)
