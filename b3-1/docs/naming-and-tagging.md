# Naming and Tagging

리소스를 식별하고 정리하기 쉽도록 이름과 태그 규칙을 정했습니다.

## 네이밍 규칙

```text
<프로젝트>-<역할>[-<구분>]
```

| 리소스 | 이름 | 설명 |
|---|---|---|
| VPC | `b3-1-vpc` | 프로젝트 전용 네트워크 |
| 퍼블릭 서브넷 | `b3-1-subnet-public1-ap-northeast-2a` | 가용 영역 구분 포함 |
| 인터넷 게이트웨이 | `b3-1-igw` | 외부 통신 경로 |
| 라우팅 테이블 | `b3-1-rtb-public1-ap-northeast-2a` | 퍼블릭 경로 |
| 보안 그룹 | `b3-1-web-sg` | 웹 서버 접근 제어 |
| 인스턴스 | `b3-1-web-server` | 웹 서비스 호스트 |
| 키 페어 | `b3-1-key` | SSH 접속용 |
| 컨테이너 이미지 | `b3-1-web:1.4` | 버전 태그 유지 |

소문자와 하이픈만 사용하고, 프로젝트 이름을 접두사로 고정해 다른 실습 리소스와 구분합니다.

## 태그 표준

| 키 | 값 예시 | 용도 |
|---|---|---|
| `Name` | `b3-1-web-server` | 콘솔 표시 이름 |
| `Project` | `b3-1` | 프로젝트 단위 조회와 정리 |
| `Env` | `lab` | 환경 구분 |
| `Owner` | `jeongbeen` | 담당자 식별 |
| `ManagedBy` | `console`, `create-infra-script` | 생성 방식 구분 |

실제 적용 결과입니다.

![리소스 태그](screenshots/resource-tags.png)

## 태그를 사용하는 이유

### 리소스 조회

```bash
aws ec2 describe-instances \
  --filters Name=tag:Project,Values=b3-1 \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' \
  --output table
```

### 일괄 정리

`scripts/teardown-infra.sh` 는 `Project=b3-1` 태그를 기준으로 삭제 대상을 찾습니다. 태그가 없으면 리소스를 개별로 찾아야 하고 삭제 누락으로 과금이 이어질 수 있습니다.

### 권한 제한

IAM 정책에서 태그 조건으로 조작 범위를 제한할 수 있습니다.

```json
{
  "Condition": {
    "StringEquals": {
      "aws:ResourceTag/Project": "b3-1"
    }
  }
}
```

### 비용 구분

`Project` 태그를 비용 할당 태그로 활성화하면 Cost Explorer에서 프로젝트별 비용을 분리해 볼 수 있습니다.

## 적용 시점

리소스를 만들 때 함께 태그를 지정합니다. 생성 후에 태그를 붙이면 누락이 생기기 쉽습니다.

```bash
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[
    {Key=Name,Value=b3-1-vpc},
    {Key=Project,Value=b3-1},
    {Key=Env,Value=lab},
    {Key=Owner,Value=jeongbeen},
    {Key=ManagedBy,Value=create-infra-script}]'
```
