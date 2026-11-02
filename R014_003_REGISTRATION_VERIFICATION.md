# R014 — 어머템포착 003 상품 등록 검증

**작성일: 2026-11-02**  
**범위: 제공 ZIP에서 003 신규 카드만 추가, 기존 001·002 및 사이트 디자인 보존**

## 반영 내용

- 003: 호텔 탑스텐 정동진, 강릉시 옥계면 헌화로 455-34.
- 공식 갤러리 첫 번째 이미지: 공식 쿠팡 CDN 경로를 검증 후 사용(원격 URL로 연결, 로컬 저장 미완료).
- 평가: 매우 좋음 / 별 4개와 빈 별 1개 / 117개 상품평, 2026-11-02 기준.
- 쿠팡 파트너스 원문 `https://link.coupang.com/a/ilicdLAy1Q`를 `products.js` 및 `affiliate-links/003.txt`에 문자 그대로 저장.
- 기존 `index.html`, `card-preview.html`, `favicon.svg`, CSS, 검색·정렬·페이지네이션 코드와 하단 광고 iframe 미변경.

## 검증 요약

- PASS: 실제 003 제휴 링크가 `trip.coupang.com/tp/products/30000011263729`로 연결됨.
- PASS: 실제 쿠팡 상세에서 숙소명·도로명주소·상품평·갤러리 첫 사진 확인.
- PASS: 003 `ratingLabel`, `ratingVisual`, `reviewCount`, `reviewCapturedAt`가 공통 상품카드의 리뷰 표시 조건과 일치.
- PASS: 기존 001·002 `products.js` 객체(모든 필드) 변경 없음.
- PASS: 기존 001·002·신규 003 `affiliate-links/NNN.txt` 및 `products.js` URL 원문 일치.
- PASS: 모든 상품 링크는 `stay` 유형이므로 003 `예약` 버튼으로 연결.
- PASS: JS 문법 검사 및 상품번호 검색 규칙 로직 정적 확인. `3`, `003` 매칭 가능.
- 제한: 실행 환경에서 Chromium의 로컬 파일 및 localhost 열기가 관리자 설정으로 차단되어 실제 PC·모바일 화면에 대한 브라우저 렌더링 자동 검증은 못함.
- 제한: 003 대표 이미지의 원격 쿠팡 CDN 접근은 확인했으나, GitHub Pages 배포 후의 이미지 지속 노출까지 보장할 수 없음.
- 미실시: GitHub Pages 업로드 및 공개 사이트 확인.

## 추적·권리

- 제휴 원본을 리디렉션한 최종 상품 URL·추적 파라미터로 치환하지 않음.
- 실제 사진을 2차 광고에 사용할 권리는 제공처 및 제휴 정책에 따라 별도 확인 필요.
