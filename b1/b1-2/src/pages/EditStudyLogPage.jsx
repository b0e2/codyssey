import { useNavigate, useParams } from 'react-router-dom'
import StudyLogForm from '../components/study-logs/StudyLogForm.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorState from '../components/ui/ErrorState.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import { useStudyLog } from '../hooks/useStudyLog.js'
import { useStudyLogForm } from '../hooks/useStudyLogForm.js'
import { useStudyLogs } from '../hooks/useStudyLogs.js'

// 폼은 불러온 값이 준비된 뒤에만 마운트한다.
// 빈 폼을 먼저 띄우고 값이 도착하면 채우는 방식이면
// 사용자가 이미 친 입력을 나중에 온 값이 덮는다.
export default function EditStudyLogPage() {
  const { id } = useParams()
  const { log, isLoading, error, isNotFound, refetch, updateLog } = useStudyLog(id)

  if (isLoading) return <LoadingState message="TIL을 불러오는 중입니다." />
  if (error) {
    return <ErrorState message="TIL을 불러오지 못했습니다." onRetry={refetch} />
  }
  if (isNotFound) return <NotFound />

  return <EditForm log={log} updateLog={updateLog} />
}

function NotFound() {
  const navigate = useNavigate()
  return (
    <EmptyState
      title="기록을 찾을 수 없습니다."
      description="이미 삭제되었거나 주소가 잘못되었을 수 있어요."
      actionLabel="학습 목록으로"
      onAction={() => navigate('/logs')}
    />
  )
}

function EditForm({ log, updateLog }) {
  const navigate = useNavigate()
  const { logs } = useStudyLogs()
  const tagSuggestions = [...new Set(logs.flatMap((item) => item.tags ?? []))]

  const form = useStudyLogForm({
    initialValues: {
      title: log.title,
      tags: log.tags ?? [],
      study_date: log.study_date,
      duration_minutes: String(log.duration_minutes),
      understanding: log.understanding,
      content: log.content,
      reflection: log.reflection ?? '',
      resource_url: log.resource_url ?? '',
      is_completed: log.is_completed,
    },
    onSubmit: async (values) => {
      const updated = await updateLog(values)
      if (!updated) throw new Error('저장하지 못했습니다. 잠시 후 다시 시도해 주세요.')
      navigate(`/logs/${log.id}`)
    },
  })

  return (
    <>
      <PageHeader title="TIL 수정" description="기록을 고치고 저장하면 상세로 돌아갑니다." />
      <StudyLogForm
        {...form}
        submitLabel="변경사항 저장"
        tagSuggestions={tagSuggestions}
        onSubmit={form.handleSubmit}
        onChange={form.handleChange}
        onBlur={form.handleBlur}
        onTagsChange={form.handleTagsChange}
        onCancel={() => navigate(`/logs/${log.id}`)}
      />
    </>
  )
}
