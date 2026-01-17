"""
뉴스 키워드 필터링 테스트 스크립트

키워드별로 뉴스가 잘 필터링되는지 테스트합니다.
지역별로 뉴스가 잘 검색되는지 확인합니다.
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

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


def print_test_case(case_num: int, description: str, keywords: List[str]):
    """테스트 케이스 출력"""
    print(f"\n[테스트 케이스 {case_num}] {description}")
    print(f"   키워드: {keywords}")
    print("-" * 70)


def analyze_news_results(news_list: List[Dict], keywords: List[str]) -> Dict[str, Any]:
    """뉴스 결과 분석"""
    if not news_list:
        return {
            "total": 0,
            "matched_in_title": 0,
            "matched_in_content": 0,
            "no_match": 0,
            "avg_score": 0.0
        }
    
    matched_in_title = 0
    matched_in_content = 0
    no_match = 0
    total_score = 0.0
    
    normalized_keywords = [kw.strip().lower() for kw in keywords if kw and kw.strip()]
    
    for news in news_list:
        title = (news.get("title", "") or "").lower()
        content = (news.get("content", "") or "").lower()
        score = news.get("relevance_score", 0.0)
        total_score += score
        
        has_title_match = False
        has_content_match = False
        
        for keyword in normalized_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in title:
                has_title_match = True
            if keyword_lower in content:
                has_content_match = True
        
        if has_title_match:
            matched_in_title += 1
        elif has_content_match:
            matched_in_content += 1
        else:
            no_match += 1
    
    return {
        "total": len(news_list),
        "matched_in_title": matched_in_title,
        "matched_in_content": matched_in_content,
        "no_match": no_match,
        "avg_score": total_score / len(news_list) if news_list else 0.0
    }


def print_news_preview(news_list: List[Dict], max_items: int = 3):
    """뉴스 미리보기 출력"""
    if not news_list:
        print("   [결과 없음]")
        return
    
    print(f"   [검색 결과: {len(news_list)}개]")
    for i, news in enumerate(news_list[:max_items], 1):
        title = news.get("title", "N/A")
        score = news.get("relevance_score", 0.0)
        matched = news.get("matched_keywords", [])
        
        print(f"   [{i}] 점수: {score:.1f}")
        print(f"       제목: {title[:60]}...")
        if matched:
            print(f"       매칭 키워드: {', '.join(matched)}")
        print()
    
    if len(news_list) > max_items:
        print(f"   ... 외 {len(news_list) - max_items}개")


async def test_keyword_filtering():
    """키워드 필터링 테스트"""
    print_section("키워드 필터링 테스트")
    
    # 먼저 뉴스를 크롤링
    print("\n[1단계] 뉴스 크롤링 중...")
    print("   실행: news_service.crawl_only(limit_per_source=30)")
    
    try:
        crawled_news = await news_service.crawl_only(limit_per_source=30)
        print(f"   [OK] 크롤링 완료: {len(crawled_news)}개 뉴스 수집")
    except Exception as e:
        print(f"   [FAIL] 크롤링 실패: {e}")
        return False
    
    if not crawled_news:
        print("   [FAIL] 크롤링된 뉴스가 없습니다.")
        return False
    
    # 테스트 케이스 정의
    test_cases = [
        {
            "description": "서울시 단일 키워드",
            "keywords": ["서울시"]
        },
        {
            "description": "부산시 단일 키워드",
            "keywords": ["부산시"]
        },
        {
            "description": "강남구 단일 키워드",
            "keywords": ["강남구"]
        },
        {
            "description": "서울시 + 강남구 복합 키워드",
            "keywords": ["서울시", "강남구"]
        },
        {
            "description": "서울시 + 강남구 + 역삼동 복합 키워드",
            "keywords": ["서울시", "강남구", "역삼동"]
        },
        {
            "description": "부산시 + 해운대구 복합 키워드",
            "keywords": ["부산시", "해운대구"]
        },
        {
            "description": "경기도 단일 키워드",
            "keywords": ["경기도"]
        },
        {
            "description": "인천시 단일 키워드",
            "keywords": ["인천시"]
        },
    ]
    
    print("\n[2단계] 키워드별 필터링 테스트")
    print(f"   총 {len(test_cases)}개 테스트 케이스 실행\n")
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print_test_case(i, test_case["description"], test_case["keywords"])
        
        try:
            # 키워드 필터링 실행
            filtered_news = filter_news_by_keywords(
                news_list=crawled_news.copy(),
                keywords=test_case["keywords"]
            )
            
            # 결과 분석
            analysis = analyze_news_results(filtered_news, test_case["keywords"])
            
            # 결과 출력
            print(f"   [결과 분석]")
            print(f"   - 총 뉴스 수: {analysis['total']}개")
            print(f"   - 제목에 매칭: {analysis['matched_in_title']}개")
            print(f"   - 본문에만 매칭: {analysis['matched_in_content']}개")
            print(f"   - 매칭 없음: {analysis['no_match']}개")
            print(f"   - 평균 점수: {analysis['avg_score']:.1f}")
            
            # 뉴스 미리보기
            print_news_preview(filtered_news, max_items=3)
            
            # 성공 여부 판단
            success = analysis['total'] > 0 and analysis['matched_in_title'] + analysis['matched_in_content'] > 0
            
            results.append({
                "case": test_case["description"],
                "keywords": test_case["keywords"],
                "success": success,
                "total": analysis['total'],
                "matched": analysis['matched_in_title'] + analysis['matched_in_content']
            })
            
            if success:
                print(f"   [OK] 테스트 통과")
            else:
                print(f"   [WARN] 매칭된 뉴스가 없거나 적습니다")
            
        except Exception as e:
            print(f"   [FAIL] 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "case": test_case["description"],
                "keywords": test_case["keywords"],
                "success": False,
                "error": str(e)
            })
    
    # 최종 결과 요약
    print_section("테스트 결과 요약")
    
    passed = sum(1 for r in results if r.get("success", False))
    total = len(results)
    
    print(f"\n총 {total}개 테스트 케이스 중 {passed}개 통과")
    print("\n상세 결과:")
    for result in results:
        status = "[OK]" if result.get("success", False) else "[FAIL]"
        case = result["case"]
        if result.get("success", False):
            total_news = result.get("total", 0)
            matched = result.get("matched", 0)
            print(f"  {status} {case}: {total_news}개 뉴스, {matched}개 매칭")
        else:
            error = result.get("error", "알 수 없는 오류")
            print(f"  {status} {case}: {error}")
    
    return passed == total


async def test_regional_keywords():
    """지역별 키워드 테스트"""
    print_section("지역별 키워드 검색 테스트")
    
    # 주요 지역별 테스트
    regional_keywords = {
        "서울": ["서울시", "서울"],
        "부산": ["부산시", "부산"],
        "대구": ["대구시", "대구"],
        "인천": ["인천시", "인천"],
        "광주": ["광주시", "광주"],
        "대전": ["대전시", "대전"],
        "울산": ["울산시", "울산"],
        "경기": ["경기도", "경기"],
        "강원": ["강원도", "강원"],
        "충북": ["충청북도", "충북"],
        "충남": ["충청남도", "충남"],
        "전북": ["전라북도", "전북"],
        "전남": ["전라남도", "전남"],
        "경북": ["경상북도", "경북"],
        "경남": ["경상남도", "경남"],
        "제주": ["제주도", "제주"],
    }
    
    print("\n[1단계] 뉴스 크롤링 중...")
    try:
        crawled_news = await news_service.crawl_only(limit_per_source=30)
        print(f"   [OK] 크롤링 완료: {len(crawled_news)}개 뉴스 수집")
    except Exception as e:
        print(f"   [FAIL] 크롤링 실패: {e}")
        return False
    
    print(f"\n[2단계] 지역별 키워드 검색 테스트")
    print(f"   총 {len(regional_keywords)}개 지역 테스트\n")
    
    results = []
    
    for region, keywords in regional_keywords.items():
        print(f"[{region}] 키워드: {keywords}")
        print("-" * 70)
        
        try:
            # 각 키워드로 필터링
            filtered_news = filter_news_by_keywords(
                news_list=crawled_news.copy(),
                keywords=keywords
            )
            
            analysis = analyze_news_results(filtered_news, keywords)
            
            print(f"   결과: {analysis['total']}개 뉴스")
            print(f"   - 제목 매칭: {analysis['matched_in_title']}개")
            print(f"   - 본문 매칭: {analysis['matched_in_content']}개")
            print(f"   - 평균 점수: {analysis['avg_score']:.1f}")
            
            # 상위 2개만 미리보기
            if filtered_news:
                print(f"   [상위 결과]")
                for i, news in enumerate(filtered_news[:2], 1):
                    title = news.get("title", "N/A")
                    score = news.get("relevance_score", 0.0)
                    print(f"      [{i}] ({score:.1f}점) {title[:50]}...")
            
            success = analysis['total'] > 0
            results.append({
                "region": region,
                "keywords": keywords,
                "success": success,
                "total": analysis['total']
            })
            
            if success:
                print(f"   [OK] 검색 성공\n")
            else:
                print(f"   [WARN] 검색 결과 없음\n")
                
        except Exception as e:
            print(f"   [FAIL] 테스트 실패: {e}\n")
            results.append({
                "region": region,
                "keywords": keywords,
                "success": False,
                "error": str(e)
            })
    
    # 결과 요약
    print_section("지역별 검색 결과 요약")
    
    successful_regions = [r for r in results if r.get("success", False)]
    print(f"\n검색 성공 지역: {len(successful_regions)}/{len(results)}개")
    
    if successful_regions:
        print("\n성공한 지역:")
        for result in successful_regions:
            print(f"  - {result['region']}: {result['total']}개 뉴스")
    
    failed_regions = [r for r in results if not r.get("success", False)]
    if failed_regions:
        print("\n검색 실패 지역:")
        for result in failed_regions:
            print(f"  - {result['region']}: {result.get('error', '결과 없음')}")
    
    return len(successful_regions) > 0


async def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 70)
    print("  뉴스 키워드 필터링 테스트")
    print("=" * 70)
    print("\n이 테스트는 다음을 확인합니다:")
    print("  1. 키워드별로 뉴스가 잘 필터링되는지")
    print("  2. 지역별로 뉴스가 잘 검색되는지")
    print("  3. 복합 키워드 검색이 제대로 동작하는지")
    
    results = {}
    
    # 1단계: 키워드 필터링 테스트
    keyword_success = await test_keyword_filtering()
    results['키워드 필터링'] = keyword_success
    
    # 2단계: 지역별 키워드 테스트
    regional_success = await test_regional_keywords()
    results['지역별 검색'] = regional_success
    
    # 최종 결과
    print_section("최종 결과")
    
    for test_name, success in results.items():
        status = "[OK] 통과" if success else "[FAIL] 실패"
        print(f"  {test_name}: {status}")
    
    print("\n" + "=" * 70)
    all_passed = all(results.values())
    if all_passed:
        print("  [결과] 모든 테스트 통과!")
        print("  키워드 필터링이 정상적으로 동작합니다.")
    else:
        print("  [결과] 일부 테스트 실패")
        print("  위의 오류 메시지를 확인하세요.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
