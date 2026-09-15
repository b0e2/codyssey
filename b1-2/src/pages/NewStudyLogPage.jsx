import { useNavigate } from 'react-router-dom'
import StudyLogForm from '../components/study-logs/StudyLogForm.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import { useCreateStudyLog } from '../hooks/useStudyLog.js'
import { useStudyLogForm } from '../hooks/useStudyLogForm.js'
import { useStudyLogs } from '../hooks/useStudyLogs.js'
import { STUDY_LOG_INITIAL_VALUES } from '../lib/studyLogValidation.js'

export default function NewStudyLogPage() {
  const navigate = useNavigate()
  const { createLog, isCreating } = useCreateStudyLog()
  // 이미 쓴 태그를 제안하려고 목록을 읽는다.
  // 제안이 없어도 등록은 되므로 이 조회의 로딩·에러는 폼을 막지 않는다.
  const { logs } = useStudyLogs()

  const tagSuggestions = [...new Set(logs.flatMap((log) => log.tags ?? []))]

  const form = useStudyLogForm({
    initialValues: STUDY_LOG_INITIAL_VALUES,
    onSubmit: async (values) => {
      const created = await createLog(values)
      navigate(`/logs/${created.id}`)
    },
  })

  return (
    <>
      <PageHeader
        title="새 TIL 작성"
        description="오늘 배운 것을 기록해보세요. 완료로 표시하려면 회고를 함께 남겨주세요."
      />
      <StudyLogForm
        {...form}
        isSubmitting={form.isSubmitting || isCreating}
        submitLabel="TIL 저장"
        tagSuggestions={tagSuggestions}
        onSubmit={form.handleSubmit}
        onChange={form.handleChange}
        onBlur={form.handleBlur}
        onTagsChange={form.handleTagsChange}
        onCancel={() => navigate('/logs')}
      />
    </>
  )
}
