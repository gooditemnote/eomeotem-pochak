#!/usr/bin/env python3
"""R010: exact affiliate URL + verified metadata -> static card.

Keep affiliate URL byte-for-byte unchanged; resolved URL is NEVER used for CTA.
Fail closed when source page/image/address cannot be verified. No deployment.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / 'products.js'
ASSETS = ROOT / 'assets' / 'products'
AFFILIATE_ARCHIVE = ROOT / 'affiliate-links'
PREFIX = '// 어머템포착 상품 데이터: 화면 공개용 내용만 기록합니다.\nwindow.EOMEOTEM_PRODUCTS = '
KST = ZoneInfo('Asia/Seoul')

def today_stamp():
    return dt.datetime.now(KST).date().isoformat()
ALLOWED_LINK_HOSTS = {'link.coupang.com', 'coupa.ng'}
BAD_TITLES = ('access denied', '403 forbidden', '로봇이 아닙니다', '접근이 제한', 'security check', 'captcha', 'page not found')


def check_number(number: str) -> str:
    if not re.fullmatch(r'(?:0[0-9]{2}|[1-9][0-9]{2,3})', number) or not 1 <= int(number) <= 9999:
        raise ValueError('번호는 001~9999 형식이어야 합니다.')
    return number


def check_affiliate_url(url: str) -> str:
    if not url or url != url.strip() or len(url) > 4096 or re.search(r'[\x00-\x20\x7f]', url):
        raise ValueError('제휴 URL 원문이 비어 있거나 공백/제어문자가 있습니다. 자동 수정하지 않습니다.')
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != 'https' or parsed.hostname not in ALLOWED_LINK_HOSTS
                or parsed.username or parsed.password or parsed.port not in (None, 443)
                or not parsed.path.strip('/') or parsed.fragment):
            raise ValueError('쿠팡 공식 HTTPS 제휴링크만 가능합니다.')
    except ValueError as exc:
        raise ValueError(f'제휴 URL 검증 실패: {exc}') from exc
    return url  # Absolute rule: DO NOT strip, expand, encode, normalize or rewrite.


def read_products() -> list[dict]:
    text = PRODUCTS.read_text(encoding='utf-8').strip()
    if not text.startswith(PREFIX.strip()) or not text.endswith(';'):
        raise ValueError('products.js 규격 불일치. 등록 중단.')
    data = json.loads(text[len(PREFIX.strip()):-1])
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        raise ValueError('상품 배열 구조 오류')
    ids = [x.get('id') for x in data]
    if len(ids) != len(set(ids)):
        raise ValueError('중복 상품번호 발견')
    return data


class StrictCoupangRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != 'https' or not (parsed.hostname == 'coupang.com' or parsed.hostname.endswith('.coupang.com') or parsed.hostname == 'coupa.ng'):
            raise ValueError('허용되지 않은 도메인으로 리디렉션됨. 자동 수집 중단.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_page(url: str) -> tuple[str, str]:
    opener = build_opener(StrictCoupangRedirect())
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125 Safari/537.36', 'Accept-Language': 'ko-KR,ko;q=0.9'})
    with opener.open(req, timeout=15) as resp:
        if resp.status != 200 or not urlsplit(resp.url).hostname.endswith('.coupang.com'):
            raise ValueError('쿠팡 상세페이지를 확인할 수 없습니다.')
        raw = resp.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('페이지가 너무 커서 자동 분석을 중단합니다.')
        charset = resp.headers.get_content_charset() or 'utf-8'
        return raw.decode(charset, errors='replace'), resp.url


def extract_value(obj, key):
    if isinstance(obj, dict):
        if key in obj: return obj[key]
        for v in obj.values():
            found = extract_value(v, key)
            if found: return found
    if isinstance(obj, list):
        for v in obj:
            found = extract_value(v, key)
            if found: return found
    return None


def metadata_from_html(html: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    og = {}
    for meta in soup.find_all('meta'):
        k = meta.get('property') or meta.get('name')
        if k: og[k.lower()] = meta.get('content', '')
    ld = []
    for script in soup.find_all('script', type='application/ld+json'):
        try: ld.append(json.loads(script.string or script.get_text()))
        except (ValueError, TypeError): pass
    name = str(og.get('og:title') or extract_value(ld, 'name') or (soup.title.get_text(' ', strip=True) if soup.title else '')).strip()
    name = re.sub(r'\s*[|｜]\s*쿠팡.*$', '', name).strip()
    image = og.get('og:image') or extract_value(ld, 'image')
    if isinstance(image, list): image = image[0] if image else ''
    if isinstance(image, dict): image = image.get('url', '')
    address = extract_value(ld, 'streetAddress') or ''
    if not address:
        e = soup.select_one('[itemprop="streetAddress"]')
        address = e.get('content') or e.get_text(' ', strip=True) if e else ''
    if len(name) < 4 or any(bad in name.lower() for bad in BAD_TITLES):
        raise ValueError('실제 상품명 확인 실패(접근 제한/빈 페이지).')
    return {'name': name, 'address': str(address).strip(), 'image': str(image or '').strip(),
            'ratingVisual': extract_value(ld, 'ratingValue'), 'reviewCount': extract_value(ld, 'reviewCount'),
            'ratingLabel': ''}


def image_bytes_valid(raw: bytes) -> bytes:
    if len(raw) > 8 * 1024 * 1024 or len(raw) < 1500:
        raise ValueError('이미지 크기가 비정상입니다.')
    try:
        with Image.open(io.BytesIO(raw)) as im:
            if im.format not in {'JPEG', 'PNG', 'WEBP'} or min(im.size) < 200:
                raise ValueError('대표 이미지 해상도/형식을 확인하세요.')
            im.verify()
    except (UnidentifiedImageError, OSError) as e:
        raise ValueError('실제 이미지 데이터가 아닙니다.') from e
    return raw


def verified_image_from_url(url: str) -> bytes:
    try:
        p = urlsplit(url)
        # Only exact provider-hosted imagery; arbitrary remote URLs are unsafe.
        if p.scheme != 'https' or not p.hostname or not (p.hostname == 'coupangcdn.com' or p.hostname.endswith('.coupangcdn.com')):
            raise ValueError('쿠팡 제공 공식 CDN 이미지가 아닙니다. 이미지 증빙 파일을 제공해 주세요.')
        opener = build_opener()
        with opener.open(Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=12) as resp:
            if resp.status != 200:
                raise ValueError('대표 이미지 다운로드 실패')
            return image_bytes_valid(resp.read(8 * 1024 * 1024 + 1))
    except (HTTPError, URLError) as e:
        raise ValueError(f'대표 이미지 다운로드 실패: {e}') from e


def atomic_write(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        f.write(content)
    try: os.replace(tmp, path)
    finally: tmp.unlink(missing_ok=True)


def execute(args):
    number = check_number(args.number)
    raw_url = check_affiliate_url(args.affiliate_url)
    old = read_products()
    existing = next((x for x in old if x['id'] == number), None)
    archive = AFFILIATE_ARCHIVE / f'{number}.txt'
    if existing:
        prior = existing.get('affiliateUrl')
        if archive.exists() and archive.read_text(encoding='utf-8') != prior:
            raise ValueError('기존 저장 제휴 URL과 원문 보관 파일이 일치하지 않습니다.')
        if prior and prior != raw_url and not args.replace:
            raise ValueError('다른 URL로 교체하려면 --replace를 명시하세요. 기존 링크 보호.')
        if prior == raw_url and not args.replace:
            print(f'변경 없음: {number}번 동일 원본 제휴 URL 등록됨.')
            return
    if args.metadata_file:
        meta = json.loads(Path(args.metadata_file).read_text(encoding='utf-8'))
        if meta.get('verifiedAffiliateUrl') != raw_url:
            raise ValueError('증빙 메타데이터 파일의 제휴 원문 URL 불일치')
        name = meta.get('name','')
        address = meta.get('address','')
        # Evidence must be traceable to a reviewed page; never guess from similar listings.
        if not meta.get('verificationSource'):
            raise ValueError('검증 출처가 없는 상품정보는 등록할 수 없습니다.')
        if not args.image_file:
            raise ValueError('수동 검증 등록은 실제 대표 이미지 파일이 필요합니다.')
        image = image_bytes_valid(Path(args.image_file).read_bytes())
        resolved = meta['verificationSource']
    else:
        try:
            html, resolved = fetch_page(raw_url)
            meta = metadata_from_html(html)
            name, address = meta['name'], meta['address']
            if not meta['image']:
                raise ValueError('쿠팡 상세페이지에 대표 이미지 데이터가 없습니다.')
            image = verified_image_from_url(meta['image'])
        except (URLError, HTTPError) as e:
            raise ValueError(f'쿠팡 상세페이지 접근 실패: {e}. 임의 데이터는 등록하지 않습니다.') from e
    if not isinstance(name,str) or not 4 <= len(name.strip()) <= 200:
        raise ValueError('검증된 상품명이 누락되었습니다.')
    if args.kind == 'stay' and (not isinstance(address,str) or not 5 <= len(address.strip()) <= 220):
        raise ValueError('숙소 도로명 주소가 확인되지 않아 등록을 중단합니다.')
    if args.kind != 'stay': address = ''
    if not isinstance(resolved, str) or not resolved.startswith('https://'):
        raise ValueError('상품정보 검증 출처가 유효하지 않습니다.')
    # Optional review snapshot: only store explicit verified figures from this page.
    review_fields = {}
    rating_label = meta.get('ratingLabel')
    review_count = meta.get('reviewCount')
    rating_visual = meta.get('ratingVisual')
    if rating_label is not None and rating_label != '':
        if (not isinstance(rating_label, str) or not 1 <= len(rating_label) <= 30
                or isinstance(review_count, bool)):
            raise ValueError('리뷰 평가 데이터가 유효하지 않습니다.')
        try:
            review_count = int(review_count)
        except (TypeError, ValueError):
            raise ValueError('상품평 개수는 검증된 정수여야 합니다.')
        if not 0 <= review_count <= 10_000_000:
            raise ValueError('리뷰 수 범위를 확인하세요.')
        review_fields.update(ratingLabel=rating_label, reviewCount=review_count,
                             reviewCapturedAt=meta.get('reviewCapturedAt', today_stamp()))
        if rating_visual is not None:
            try: rating_visual = float(rating_visual)
            except (ValueError,TypeError): raise ValueError('별점 표시 데이터를 확인하세요.')
            if not 0 <= rating_visual <= 5: raise ValueError('별점 표시 범위 오류')
            review_fields['ratingVisual'] = rating_visual
    ext = {'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}[Image.open(io.BytesIO(image)).format]
    image_path = ASSETS / f'{number}{ext}'
    # No silently changing the affiliate link, even for internal JSON escapes.
    today = dt.datetime.now(KST).date().isoformat()
    entry = {'id':number,'name':name.strip(),'address':address.strip(), 'kind':args.kind,
             'imageUrl':f'./assets/products/{number}{ext}', 'affiliateUrl':raw_url,
             'publishedAt':today}
    entry.update(review_fields)
    after = [dict(x) for x in old if x['id'] != number] + [entry]
    contents = (PREFIX + json.dumps(after, ensure_ascii=False, indent=2) + ';\n').encode('utf-8')
    recovered = json.loads(contents.decode('utf-8').strip()[len(PREFIX.strip()):-1])
    assert next(i for i in recovered if i['id'] == number)['affiliateUrl'] == raw_url
    assert all(next(y for y in recovered if y['id'] == x['id']) == x for x in old if x['id'] != number)
    print(f'검증: {number}, {name}, 주소={address or "해당 없음"}, 이미지={len(image)} bytes')
    print(f'제휴 URL SHA256: {hashlib.sha256(raw_url.encode()).hexdigest()}')
    if args.dry_run:
        print('DRY RUN: 파일 변경 없음')
        return
    backup = ROOT.parent / f'{ROOT.name}_private_backups' / dt.datetime.now(KST).strftime('%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True)
    paths = [PRODUCTS, archive, image_path]
    previous = {p:(p.read_bytes() if p.exists() else None) for p in paths}
    for p, content in previous.items():
        if content is not None: (backup / p.name).write_bytes(content)
    try:
        atomic_write(image_path, image)
        atomic_write(archive, raw_url.encode('utf-8'))
        atomic_write(PRODUCTS, contents)
        assert archive.read_bytes() == raw_url.encode('utf-8')
        assert next(x for x in read_products() if x['id'] == number)['affiliateUrl'] == raw_url
        assert image_bytes_valid(image_path.read_bytes()) == image
    except Exception:
        for p, content in previous.items():
            if content is None: p.unlink(missing_ok=True)
            else: atomic_write(p, content)
        raise
    print(f'등록 완료: {number}; 원본 제휴 URL 보존 PASS; 백업 {backup}')
    print('정적 사이트 배포는 별도로 진행해야 합니다.')


def main():
    p = argparse.ArgumentParser(description='어머템포착 R010, 상품번호 + 쿠팡 제휴 URL -> 검증된 상품 카드 등록')
    p.add_argument('--number', required=True)
    p.add_argument('--affiliate-url', required=True, help='사용자 제공 URL을 1문자도 변경하지 마세요.')
    p.add_argument('--kind', choices=['stay','general'], default='stay')
    p.add_argument('--metadata-file', help='직접 검증한 JSON. 반드시 verifiedAffiliateUrl/verificationSource/name/address 포함')
    p.add_argument('--image-file', help='실제 상품 대표 이미지 증빙 파일. 수동 검증시에만 사용')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--replace', action='store_true', help='같은 번호의 기존 상품 교체를 명시적으로 허용')
    args = p.parse_args()
    execute(args)

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, KeyError, AssertionError, json.JSONDecodeError) as e:
        print(f'등록 보류: {e}',file=sys.stderr)
        sys.exit(2)
