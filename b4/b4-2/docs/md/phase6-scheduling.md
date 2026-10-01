# Phase 6. 스케줄링 분석

기록: [phase6-scheduling.log](../log/phase6-scheduling.log) · 리포트: [#13](https://github.com/b0e2/b4-2/issues/13)

## 목표

- 정상 실행 시 Scheduler 작업 로그의 실행 순서, 교체 시점 확인
- Round-Robin, FCFS, Priority 중 적용된 방식 판단

## 진행

```bash
for n in 1 2 3; do nohup $AGENT_HOME/agent-leak-app-arm64 > /dev/null 2>&1 & sleep 4; pkill -x agent-leak-app-; sleep 2; done
grep -E 'Scheduler|\[Thread-' $AGENT_LOG_DIR/agent_app.log | head -19
grep -oE '\[Thread-.\]' $AGENT_LOG_DIR/agent_app.log | uniq -c
grep -E 'Task Started|Task Completed' $AGENT_LOG_DIR/agent_app.log
grep -cE 'Preempted|Resumed' $AGENT_LOG_DIR/agent_app.log
```

## 확인

![Scheduling](../images/scheduling.png)

| 작업 | 등록 순서 | 시작 | 완료 | 대기 | 반환 |
| --- | --- | --- | --- | --- | --- |
| Thread-B | 2 | ,078 | ,290 | 1ms | 213ms |
| Thread-C | 3 | ,346 | ,563 | 269ms | 486ms |
| Thread-A | 1 | ,619 | ,832 | 542ms | 755ms |

- 3회 모두 B → C → A, 작업마다 5줄 연속
- `Preempted`, `Resumed` 0건

## 결과

| 방식 | 판단 | 근거 |
| --- | --- | --- |
| Round-Robin | 아님 | 작업 중간 교체 없음 |
| FCFS | 아님 | 등록 순서 A, B, C와 실행 순서가 다름 |
| Priority (비선점) | 해당 | 매번 같은 순서 B > C > A, 시작한 작업은 완료까지 실행 |

우선순위가 낮은 작업의 대기가 길어지므로, 작업 중요도가 분명한 배치 처리에는 맞고 고른 응답 시간이 필요한 웹 서버에는 선점형 방식이 맞습니다.
