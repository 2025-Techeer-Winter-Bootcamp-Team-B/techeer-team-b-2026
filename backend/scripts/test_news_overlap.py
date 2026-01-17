"""
뉴스 지역별 중복/고유 비율 테스트 스크립트

서울/강남, 경기/성남, 경북/경주 세 지역에서 크롤링한 뉴스의
공통 뉴스와 다른 뉴스의 비율을 분석합니다.
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

# Windows에서 UTF-8 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트를 Python 경로에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.news import news_service
from app.utils.news import filter_news_by_keywords


def print_section(title: str, width: int = 70):
    """섹션 구분선 출력"""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def get_news_urls(news_list: List[Dict]) -> Set[str]:
    """뉴스 리스트에서 URL 집합 추출"""
    return {news.get("url", "") for news in news_list if news.get("url")}


def analyze_overlap(regions: Dict[str, List[Dict]]):
    """지역별 뉴스 중복/고유 비율 분석"""
    print_section("뉴스 중복/고유 비율 분석")
    
    # 각 지역의 URL 집합
    region_urls = {}
    for region_name, news_list in regions.items():
        region_urls[region_name] = get_news_urls(news_list)
        print(f"\n[{region_name}]")
        print(f"  총 뉴스 수: {len(news_list)}개")
        print(f"  고유 URL 수: {len(region_urls[region_name])}개")
    
    # 모든 지역의 URL 집합
    all_urls = set()
    for urls in region_urls.values():
        all_urls.update(urls)
    
    print(f"\n[전체 통계]")
    print(f"  전체 고유 뉴스 수: {len(all_urls)}개")
    
    # 지역별 고유 뉴스 (다른 지역과 겹치지 않는 뉴스)
    unique_news = {}
    for region_name, urls in region_urls.items():
        other_urls = set()
        for other_region, other_urls_set in region_urls.items():
            if other_region != region_name:
                other_urls.update(other_urls_set)
        unique_news[region_name] = urls - other_urls
        print(f"\n[{region_name} 고유 뉴스]")
        print(f"  개수: {len(unique_news[region_name])}개")
        if len(region_urls[region_name]) > 0:
            unique_percent = (len(unique_news[region_name]) / len(region_urls[region_name])) * 100
            print(f"  비율: {unique_percent:.1f}%")
    
    # 두 지역 간 공통 뉴스
    print(f"\n[지역 간 공통 뉴스]")
    region_names = list(region_urls.keys())
    for i, region1 in enumerate(region_names):
        for region2 in region_names[i+1:]:
            common = region_urls[region1] & region_urls[region2]
            print(f"\n[{region1} ∩ {region2}]")
            print(f"  공통 뉴스 수: {len(common)}개")
            if len(region_urls[region1]) > 0:
                percent1 = (len(common) / len(region_urls[region1])) * 100
                print(f"  {region1} 대비: {percent1:.1f}%")
            if len(region_urls[region2]) > 0:
                percent2 = (len(common) / len(region_urls[region2])) * 100
                print(f"  {region2} 대비: {percent2:.1f}%")
    
    # 세 지역 모두 공통인 뉴스
    if len(region_names) >= 3:
        all_common = region_urls[region_names[0]]
        for region_name in region_names[1:]:
            all_common &= region_urls[region_name]
        
        print(f"\n[세 지역 모두 공통 뉴스]")
        print(f"  개수: {len(all_common)}개")
        for region_name in region_names:
            if len(region_urls[region_name]) > 0:
                percent = (len(all_common) / len(region_urls[region_name])) * 100
                print(f"  {region_name} 대비: {percent:.1f}%")
    
    # 공통 뉴스 상세 정보
    if len(all_common) > 0:
        print(f"\n[세 지역 모두 공통 뉴스 상세]")
        # 원본 뉴스 리스트에서 공통 뉴스 찾기
        common_news_list = []
        for region_name, news_list in regions.items():
            for news in news_list:
                if news.get("url") in all_common:
                    if news not in common_news_list:
                        common_news_list.append(news)
        
        for i, news in enumerate(common_news_list[:5], 1):  # 최대 5개만 표시
            title = news.get("title", "N/A")
            print(f"  [{i}] {title[:60]}...")
        if len(common_news_list) > 5:
            print(f"  ... 외 {len(common_news_list) - 5}개")
    
    # 지역별 고유 뉴스 상세 정보
    print(f"\n[지역별 고유 뉴스 상세]")
    for region_name, news_list in regions.items():
        unique_urls = unique_news[region_name]
        if len(unique_urls) > 0:
            print(f"\n[{region_name} 고유 뉴스]")
            unique_news_list = [news for news in news_list if news.get("url") in unique_urls]
            for i, news in enumerate(unique_news_list[:3], 1):  # 최대 3개만 표시
                title = news.get("title", "N/A")
                print(f"  [{i}] {title[:60]}...")
            if len(unique_news_list) > 3:
                print(f"  ... 외 {len(unique_news_list) - 3}개")
    
    # 통계 요약
    print_section("통계 요약")
    
    # 실제 뉴스 개수 계산 (각 지역의 뉴스 리스트 길이)
    total_news_count = sum(len(news_list) for news_list in regions.values())
    total_unique_count = len(all_urls)
    
    # 중복 계산: 전체 뉴스 수 - 고유 뉴스 수
    overlap_count = total_news_count - total_unique_count
    
    print(f"\n[전체 통계]")
    print(f"  전체 뉴스 수 (중복 포함): {total_news_count}개")
    print(f"  전체 고유 뉴스 수: {total_unique_count}개")
    print(f"  중복 뉴스 수: {overlap_count}개")
    
    if total_news_count > 0:
        overlap_percent = (overlap_count / total_news_count) * 100
        unique_percent = (total_unique_count / total_news_count) * 100
        print(f"\n  중복 비율: {overlap_percent:.1f}%")
        print(f"  고유 비율: {unique_percent:.1f}%")
    else:
        overlap_percent = 0.0
        unique_percent = 0.0
    
    return {
        "total_news": total_news_count,
        "unique_news": total_unique_count,
        "overlap_count": overlap_count,
        "overlap_percent": overlap_percent,
        "unique_percent": unique_percent,
        "all_common": len(all_common) if len(region_names) >= 3 else 0,
        "region_unique": {name: len(urls) for name, urls in unique_news.items()}
    }


async def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 70)
    print("  지역별 뉴스 중복/고유 비율 테스트")
    print("=" * 70)
    print("\n테스트 지역:")
    print("  1. 서울/강남: ['서울시', '강남구']")
    print("  2. 경기/성남: ['경기도', '성남시']")
    print("  3. 경북/경주: ['경상북도', '경주시']")
    
    # 뉴스 크롤링
    print_section("1단계: 뉴스 크롤링")
    print("\n뉴스를 크롤링 중...")
    print("   실행: news_service.crawl_only(limit_per_source=30)")
    
    try:
        crawled_news = await news_service.crawl_only(limit_per_source=30)
        print(f"   [OK] 크롤링 완료: {len(crawled_news)}개 뉴스 수집")
    except Exception as e:
        print(f"   [FAIL] 크롤링 실패: {e}")
        return
    
    if not crawled_news:
        print("   [FAIL] 크롤링된 뉴스가 없습니다.")
        return
    
    # 지역별 키워드 정의
    regions = {
        "서울/강남": ["서울시", "강남구"],
        "경기/성남": ["경기도", "성남시"],
        "경북/경주": ["경상북도", "경주시"]
    }
    
    # 지역별 필터링
    print_section("2단계: 지역별 뉴스 필터링")
    
    filtered_regions = {}
    for region_name, keywords in regions.items():
        print(f"\n[{region_name}] 키워드: {keywords}")
        try:
            filtered_news = filter_news_by_keywords(
                news_list=crawled_news.copy(),
                keywords=keywords
            )
            filtered_regions[region_name] = filtered_news
            print(f"  [OK] 필터링 완료: {len(filtered_news)}개 뉴스")
            
            # 상위 3개 미리보기
            if filtered_news:
                print(f"  [상위 결과]")
                for i, news in enumerate(filtered_news[:3], 1):
                    title = news.get("title", "N/A")
                    score = news.get("relevance_score", 0.0)
                    print(f"    [{i}] ({score:.1f}점) {title[:50]}...")
        except Exception as e:
            print(f"  [FAIL] 필터링 실패: {e}")
            filtered_regions[region_name] = []
    
    # 중복/고유 비율 분석
    if filtered_regions:
        stats = analyze_overlap(filtered_regions)
        
        # 최종 결과
        print_section("최종 결과")
        print(f"\n[전체 통계]")
        print(f"  전체 뉴스 수: {stats['total_news']}개")
        print(f"  전체 고유 뉴스 수: {stats['unique_news']}개")
        print(f"  중복 뉴스 수: {stats['overlap_count']}개")
        print(f"  중복 비율: {stats['overlap_percent']:.1f}%")
        print(f"  고유 비율: {stats['unique_percent']:.1f}%")
        print(f"  세 지역 모두 공통 뉴스: {stats['all_common']}개")
        
        print(f"\n[지역별 고유 뉴스]")
        for region_name, count in stats['region_unique'].items():
            print(f"  {region_name}: {count}개")
        
        print("\n" + "=" * 70)
        print("  테스트 완료!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
