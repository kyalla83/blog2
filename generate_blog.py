import anthropic
import os
import json
from datetime import datetime

REGION   = "서울"
CATEGORY = "맛집"
THEME    = "가성비"

def generate_blog():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    print(f"API KEY 확인: {'있음' if api_key else '없음'}")

    today    = datetime.now().strftime("%Y년 %m월 %d일")
    date_str = datetime.now().strftime("%Y-%m-%d")

    extras = f" | 테마: {THEME}" if THEME else ""
    prompt = f"""당신은 네이버 블로그 맛집 전문 블로거입니다.
오늘 날짜: {today} | 지역: {REGION} | 카테고리: {CATEGORY}{extras}

아래 형식으로 정보형 네이버 블로그 글을 작성하세요.

[제목] SEO 최적화, 구체적이고 매력적으로 작성
[서론] 오늘 소개할 맛집 트렌드 소개 3문장
[본문] 맛집 3곳 각각: 식당명 / 위치 / 가격대 / 대표메뉴 / 추천 포인트
[마무리] 방문 권유 2문장
[해시태그] 관련 해시태그 12개

규칙: 정보 전달 위주 객관적 문체, 이모지 적절히 사용, 900~1100자, 블로그 글만 출력"""

    print("Claude API 호출 중...")
    client  = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model      = "claude-sonnet-4-6",
        max_tokens = 1500,
        messages   = [{"role": "user", "content": prompt}]
    )
    blog_text = message.content[0].text
    print(f"글 생성 완료! 길이: {len(blog_text)}자")

    os.makedirs("posts", exist_ok=True)
    post = {
        "date"    : date_str,
        "region"  : REGION,
        "category": CATEGORY,
        "content" : blog_text
    }
    post_path = f"posts/{date_str}.json"
    with open(post_path, "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=2)
    print(f"포스트 저장: {post_path}")

    all_posts = []
    for fname in sorted(os.listdir("posts"), reverse=True):
        if fname.endswith(".json") and fname != "index.json":
            with open(f"posts/{fname}", encoding="utf-8") as f:
                p = json.load(f)
                all_posts.append({
                    "date"    : p["date"],
                    "region"  : p["region"],
                    "category": p["category"],
                    "preview" : p["content"][:100] + "..."
                })

    with open("posts/index.json", "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)
    print(f"index.json 저장 완료! 총 {len(all_posts)}개 포스트")

if __name__ == "__main__":
    generate_blog()
