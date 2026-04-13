import anthropic
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

# 검색 키워드 → 블로그 파일명 매핑
KEYWORDS = [
    {"keyword": "생생정보통 맛집",  "slug": "saengsaeng"},
    {"keyword": "생방송투데이 맛집", "slug": "today"},
    {"keyword": "6시내고향 맛집",   "slug": "hometown"},
]

def search_naver_news(keyword, client_id, client_secret, display=5):
    """네이버 뉴스 검색 API 호출"""
    enc = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/news.json?query={enc}&display={display}&sort=date"
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode("utf-8"))
    items = data.get("items", [])
    # HTML 태그 제거
    results = []
    for item in items:
        title = item["title"].replace("<b>","").replace("</b>","").replace("&amp;","&").replace("&lt;","<").replace("&gt;",">").replace("&quot;",'"')
        desc  = item["description"].replace("<b>","").replace("</b>","").replace("&amp;","&").replace("&lt;","<").replace("&gt;",">").replace("&quot;",'"')
        results.append(f"- 제목: {title}\n  내용: {desc}\n  링크: {item['link']}")
    return "\n".join(results) if results else "검색 결과 없음"

def generate_blog(keyword, news_text, client):
    """Claude API로 블로그 글 생성"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    prompt = f"""당신은 네이버 블로그 맛집 전문 블로거입니다.
오늘 날짜: {today}
키워드: {keyword}

아래는 오늘 관련 뉴스 검색 결과입니다:
{news_text}

위 뉴스를 참고해서 정보형 네이버 블로그 글을 작성하세요.

[제목] 오늘 방송된 맛집 정보를 담은 SEO 최적화 제목
[서론] 오늘 방송 소개 2~3문장
[본문] 뉴스에서 언급된 맛집 정보 위주로 식당명 / 위치 / 대표메뉴 / 특징 / 추천 포인트
[마무리] 방문 권유 2문장
[해시태그] 관련 해시태그 12개

규칙: 정보 전달 위주 객관적 문체, 이모지 적절히 사용, 900~1100자, 블로그 글만 출력"""

    message = client.messages.create(
        model      = "claude-sonnet-4-6",
        max_tokens = 1500,
        messages   = [{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def main():
    api_key       = os.environ.get("ANTHROPIC_API_KEY")
    naver_id      = os.environ.get("NAVER_CLIENT_ID")
    naver_secret  = os.environ.get("NAVER_CLIENT_SECRET")

    print(f"Anthropic API KEY: {'있음' if api_key else '없음'}")
    print(f"Naver Client ID:   {'있음' if naver_id else '없음'}")

    client   = anthropic.Anthropic(api_key=api_key)
    date_str = datetime.now().strftime("%Y-%m-%d")

    os.makedirs("posts", exist_ok=True)
    all_posts = []

    # 기존 포스트 불러오기
    for fname in sorted(os.listdir("posts"), reverse=True):
        if fname.endswith(".json") and fname != "index.json":
            with open(f"posts/{fname}", encoding="utf-8") as f:
                p = json.load(f)
                all_posts.append({
                    "date"    : p["date"],
                    "slug"    : p.get("slug", fname.replace(".json","")),
                    "keyword" : p.get("keyword", ""),
                    "preview" : p["content"][:100] + "..."
                })

    # 오늘 날짜 기존 포스트 제거 (재실행 시 덮어쓰기)
    all_posts = [p for p in all_posts if not p["date"].startswith(date_str)]

    today_posts = []
    for item in KEYWORDS:
        keyword = item["keyword"]
        slug    = item["slug"]
        print(f"\n[{keyword}] 뉴스 검색 중...")
        news_text = search_naver_news(keyword, naver_id, naver_secret)
        print(f"검색 완료. Claude API 호출 중...")
        blog_text = generate_blog(keyword, news_text, client)
        print(f"글 생성 완료! 길이: {len(blog_text)}자")

        post = {
            "date"    : date_str,
            "slug"    : slug,
            "keyword" : keyword,
            "content" : blog_text
        }
        filename = f"posts/{date_str}-{slug}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(post, f, ensure_ascii=False, indent=2)
        print(f"저장 완료: {filename}")

        today_posts.append({
            "date"    : date_str,
            "slug"    : slug,
            "keyword" : keyword,
            "preview" : blog_text[:100] + "..."
        })

    # index.json 갱신 (오늘 글 + 기존 글)
    merged = today_posts + all_posts
    with open("posts/index.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"\nindex.json 저장 완료! 총 {len(merged)}개 포스트")

if __name__ == "__main__":
    main()
