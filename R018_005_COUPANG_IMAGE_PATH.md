# R018 — 005 서울랜드 쿠팡 이미지 경로 적용 (2026-11-04)

- 사용자 제공 주소는 `https://image.coupangcdn.com/image/resized_image/t…00186371/1ebcc0a0-8b20-4b8d-8f42-c0efe1ca0234.jpg`처럼 중간 경로가 생략된 형태였습니다.
- 크롬에서 확인된 서울랜드 상품(30000001063207) 갤러리 **첫 사진 파일명**은 `1ebcc0a0-8b20-4b8d-8f42-c0efe1ca0234.jpg`입니다.
- **경로 추정 복원**: 기존 쿠팡 트래블 ticket 갤러리 URL 패턴(`travelSeller/common/A...`)을 사용하여 다음 URL을 조립했습니다.
  `https://image.coupangcdn.com/image/resized_image/thumbnails/remote/1180x2360q60crop1180x630/image/travelSeller/common/A00186371/1ebcc0a0-8b20-4b8d-8f42-c0efe1ca0234.jpg`
- 주의: 파일명을 실제 쿠팡 페이지와 대조했지만, **생략된 전체 경로 및 해당 CDN URL의 HTTP/이미지 응답을 검증하지 못했습니다.** 따라서 쿠팡 공식 이미지 적용은 원격 접속 시 성공 여부를 확인해야 합니다.
- 원격 이미지에 에러가 나면 이전 CC0 대체사진으로 돌아가며, 그마저 실패하면 `실제 사진 준비 중`을 표시합니다. 대체사진은 쿠팡 이미지와 동일하지 않습니다.
- 상품 ID·주소·명칭·리뷰·001~005 모든 제휴 URL은 변경하지 않았습니다.
- GitHub Pages 배포는 수행하지 않았습니다.
