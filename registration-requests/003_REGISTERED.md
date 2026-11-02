# 003 상품 등록 증빙 — 호텔 탑스텐 정동진

- 상태: **정적 사이트 ZIP 반영 완료, 실제 배포 전** (2026-11-02)
- 번호: `003`
- 쿠팡 상품: **[본사직영] 호텔 탑스텐 정동진** (실제 상세페이지 상품 이름에 이벤트성 가격 문구가 추가될 수 있으므로 카드에서는 숙소명 중심으로 표기)
- 종류: `stay`, 버튼 표기 `예약`
- 방문지 주소: **강원특별자치도 강릉시 옥계면 헌화로 455-34**
- 위치 안내: 바다 전망 객실은 객실별로 별도 선택해야 함
- 평가: **매우 좋음**, **★★★★☆** (쿠팡 `productReview.ratingAverage = 4.0` 기준 별표 표시), 상품평 **117개**, 2026-11-02 화면 확인 시점 기준. 별점 숫자를 카드에 직접 표기하지 않음.
- 대표 이미지: 동일 상품의 쿠팡 `product.imageGroups[0].images[0].smallThumbnailPath`로 확인된 실제 **첫 번째 갤러리 이미지**. `https://thumbnail.coupangcdn.com/thumbnails/remote/400x200q60crop200x200/image/travelSeller/hotel/A01437486/87dc8b35-b148-415c-b564-c7a06d985b91.png`
- 이미지 방식: 제공 CDN의 URL을 그대로 로드. 이 소스는 원격에 있으므로 쿠팡 CDN에서 접근을 제한하거나 URL이 바뀌면 이미지가 표시되지 않을 수 있음. 사이트의 이미지 실패 대체 안내는 기존대로 적용됨. 로컬 저장본 없음.
- 원문 제휴 링크: `https://link.coupang.com/a/ilicdLAy1Q`
- 원본 보관: `affiliate-links/003.txt` (줄바꿈 없이 원문만 저장)
- 링크 SHA-256 (UTF-8): `3394866a111893bbc095776ea6b00ed40a9d81fa1f475a274411d70253b1fc8b`
- 링크 리디렉션 검증: 단축 URL 접속 결과 `https://trip.coupang.com/tp/products/30000011263729` 상품으로 연결되며 `vendorItemId=70000227543392`, `itemId=20002141545227`을 포함한 같은 호텔의 페이지 확인. **이 도착 URL은 상품 카드 버튼에 저장하지 않음.**
- 가격·특가 안내는 변동 가능해 상품 카드에 표시하지 않음.
- 기존 `001`, `002` 상품 데이터와 제휴 URL은 수정하지 않음.
- 표시: 기존 `verifiedProductCard`와 `travel-card` 공통 CSS를 사용하므로 상품명·주소·리뷰·예약 버튼 스타일은 001·002와 같음. `index.html` 자체를 수정하지 않음.
- 실제 이미지를 상업적으로 사용할 권리는 별도 이용 조건 확인이 필요.

## 확인 경로

쿠팡 트래블 상품 상세페이지 `https://trip.coupang.com/tp/products/30000011263729`의 `travel-detail-product-data` 안 `product.productName`, `product.location.address`, `product.productReview`, `product.imageGroups[0].images[0]` 확인. 사용자 제공 단축 링크로 접근해 이 상품에 도달하는 것도 확인.
