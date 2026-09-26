# IAM and Least Privilege

## Security Group과 IAM의 역할 구분

두 기능은 통제 대상이 다릅니다.

| 구분 | Security Group | IAM |
|---|---|---|
| 통제 대상 | 네트워크 트래픽 | AWS API 호출 권한 |
| 적용 위치 | ENI, 인스턴스 | 사용자, 역할, 서비스 |
| 판단 기준 | 포트, 프로토콜, 출발지 | 액션, 리소스, 조건 |
| 예시 | 22번 포트를 관리자 IP에만 허용 | `ec2:TerminateInstances` 허용 여부 |

네트워크에서 차단되어도 IAM 권한이 과도하면 API로 리소스를 변경할 수 있고, 반대로 IAM이 제한되어도 포트가 열려 있으면 서비스는 노출됩니다. 두 계층을 함께 좁혀야 합니다.

## 이 프로젝트의 운영 자격 증명

작업에는 루트 계정이 아닌 별도의 IAM 사용자 `cloud-lab-operator` 를 사용했습니다.

이 사용자는 실습에 필요한 EC2와 VPC 조작 권한만 가지며, IAM 관련 액션은 부여되어 있지 않습니다. 실제로 IAM 보안 자격 증명 화면을 열면 권한 부족 메시지가 표시됩니다.

![IAM 권한 제한 확인](screenshots/iam-least-privilege.png)

CloudTrail 조회와 CloudShell 실행도 권한이 없어 사용할 수 없습니다. 필요한 작업만 허용된 상태임을 그대로 보여 주는 결과입니다.

## 역할별 정책 예시

### 조회 전용

배포 상태만 확인하는 담당자에게 부여합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOnlyInspect",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeRouteTables",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs"
      ],
      "Resource": "*"
    }
  ]
}
```

### 실습 운영자

이 프로젝트의 리소스만 다루도록 태그 조건을 겁니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ManageTaggedInstances",
      "Effect": "Allow",
      "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:RebootInstances",
        "ec2:TerminateInstances"
      ],
      "Resource": "arn:aws:ec2:ap-northeast-2:*:instance/*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Project": "b3-1"
        }
      }
    },
    {
      "Sid": "DenyOtherRegions",
      "Effect": "Deny",
      "Action": "ec2:*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": "ap-northeast-2"
        }
      }
    }
  ]
}
```

### 인스턴스 역할

서버에서 AWS API가 필요할 때는 액세스 키를 인스턴스에 두지 않고 역할을 사용합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "WriteOwnLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:ap-northeast-2:*:log-group:/b3-1/*"
    }
  ]
}
```

## 권한 최소화 절차

1. 아무 권한도 없는 상태에서 시작합니다.
2. 작업을 수행하고 실패한 API 호출을 확인합니다.
3. 실패한 액션만 정책에 추가합니다.
4. 리소스 범위를 `*` 대신 ARN이나 태그 조건으로 좁힙니다.
5. 리전 조건으로 사용 범위를 제한합니다.
6. 사용하지 않는 권한은 주기적으로 제거합니다.

## 운영 원칙

- 루트 계정은 결제와 계정 설정 외에는 사용하지 않습니다.
- 모든 사용자에게 MFA를 적용합니다.
- 장기 액세스 키 대신 역할과 임시 자격 증명을 사용합니다.
- 액세스 키가 필요하면 저장소에 포함하지 않고 별도로 관리합니다.
- 권한 변경 이력은 검토 가능한 형태로 남깁니다.
