# 이에이승 소개
![Untitled](https://user-images.githubusercontent.com/62296495/196046510-d9ec3dc7-0f15-4f6a-b75a-81593c6bc8d7.png)
<img width="926" alt="Untitled (1)" src="https://user-images.githubusercontent.com/62296495/196046514-98309931-8a43-4b07-acc9-944cd279c15d.png">

이에이승 서비스는 사투리 사용자가 면접 중 사투리를 인식하고 표준어로 번역해 사용자가 사투리를 교정할 수 있도록 돕는 서비스 입니다. 

## Flask-server
이에이승 프로젝트의 Flask-server Repository입니다.

[이에이승 Organization](https://github.com/epowe)

## 주요 기능

- 면접 영상 분석 및 피드백 제공
- 사투리 인식 기능
- TTS를 사용한 목소리 비교 기능

## 팀 구성

- 프론트 개발 2명
- 서버 개발 2명
- AI 모델 개발 1명

## 기술 스택

`Flask`, `MySQL` , `AWS`, `Docker`

## 프로젝트 기여

1. **AWS 인프라 구축**
    - MSA 구조의 아키텍처 설계
          <img width="1193" alt="Untitled (2)" src="https://user-images.githubusercontent.com/62296495/196046561-764d48a5-8193-42c6-b4e8-a6c840c5bf11.png">
            
2. **AI 영상 분석 Flask 서버 구현**
    - AI 분석 데이터 CRUD 구현
    - Naver Clova TTS API 적용
    - AWS S3, MySQL을 사용해 영상, 음성 데이터 관리
    - Github Actions, Docker를 사용한 CI/CD 자동화

