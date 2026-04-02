#!/usr/bin/env python3
from __future__ import annotations

import html
from datetime import date
from pathlib import Path

from content_loader import ContentError, load_content

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"


def safe(value: str) -> str:
    return html.escape(value, quote=True)


def article_href(slug: str) -> str:
    return f"habit-{slug}.html"


def exercise_href(slug: str) -> str:
    return f"exercise-{slug}.html"


def nav_items() -> list[tuple[str, str, str]]:
    return [
        ("index", "Главная", "index.html"),
        ("habits", "Привычки", "habits.html"),
        ("resources", "PDF", "resources.html"),
        ("exercises", "Упражнения", "exercises.html"),
    ]


def render_header(site: dict, current: str) -> str:
    links = []
    for key, label, href in nav_items():
        state = ' aria-current="page"' if key == current else ""
        active = " is-active" if key == current else ""
        links.append(
            f'<a class="site-nav__link{active}" href="{href}"{state}>{safe(label)}</a>'
        )

    return f"""
    <header class="site-header">
      <div class="shell site-header__inner">
        <a class="brand" href="index.html">
          <span class="brand__eyebrow">Практика</span>
          <span class="brand__title">{safe(site["title"])}</span>
        </a>
        <nav class="site-nav" aria-label="Основная навигация">
          {''.join(links)}
        </nav>
      </div>
    </header>
    """


def render_footer(site: dict) -> str:
    notes = "".join(
        f"<li>{safe(note)}</li>" for note in site["githubPagesNotes"]
    )
    return f"""
    <footer class="site-footer">
      <div class="shell site-footer__grid">
        <div class="site-footer__block">
          <p class="site-footer__label">О проекте</p>
          <p>{safe(site["description"])}</p>
        </div>
        <div class="site-footer__block">
          <p class="site-footer__label">GitHub Pages</p>
          <ul class="plain-list">{notes}</ul>
        </div>
        <div class="site-footer__block">
          <p class="site-footer__label">Дисклеймер</p>
          <p>{safe(site["disclaimer"])}</p>
        </div>
      </div>
      <div class="shell site-footer__meta">
        <span>© {date.today().year} {safe(site["title"])}</span>
        <span>Статический сайт для GitHub Pages</span>
      </div>
    </footer>
    """


def render_layout(title: str, description: str, site: dict, current: str, body: str) -> str:
    full_title = f"{title} | {site['title']}"
    return f"""<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{safe(full_title)}</title>
    <meta name="description" content="{safe(description)}">
    <link rel="icon" href="assets/images/favicon.svg" type="image/svg+xml">
    <link rel="stylesheet" href="assets/css/styles.css">
  </head>
  <body>
    <a class="skip-link" href="#content">Перейти к содержанию</a>
    <div class="page-backdrop"></div>
    {render_header(site, current)}
    <main id="content">
      {body}
    </main>
    {render_footer(site)}
  </body>
</html>
"""


def render_section_intro(eyebrow: str, title: str, text: str) -> str:
    return f"""
    <div class="section-intro">
      <p class="eyebrow">{safe(eyebrow)}</p>
      <h2>{safe(title)}</h2>
      <p>{safe(text)}</p>
    </div>
    """


def render_stat_card(label: str, value: str, text: str) -> str:
    return f"""
    <article class="stat-card">
      <p class="stat-card__label">{safe(label)}</p>
      <p class="stat-card__value">{safe(value)}</p>
      <p class="stat-card__text">{safe(text)}</p>
    </article>
    """


def render_article_card(article: dict) -> str:
    return f"""
    <article class="content-card">
      <div class="content-card__meta">
        <span>{safe(article["category"])}</span>
        <span>{safe(article["readTime"])}</span>
      </div>
      <h3><a href="{article_href(article['slug'])}">{safe(article["title"])}</a></h3>
      <p>{safe(article["summary"])}</p>
      <a class="text-link" href="{article_href(article['slug'])}">Открыть материал</a>
    </article>
    """


def render_resource_card(resource: dict) -> str:
    highlights = "".join(f"<li>{safe(item)}</li>" for item in resource["highlights"])
    return f"""
    <article class="resource-card">
      <img src="{safe(resource['coverPath'])}" alt="" class="resource-card__art">
      <div class="resource-card__body">
        <div class="content-card__meta">
          <span>{safe(resource["format"])}</span>
          <span>{safe(str(resource["pages"]))} стр.</span>
        </div>
        <h3>{safe(resource["title"])}</h3>
        <p>{safe(resource["summary"])}</p>
        <p class="resource-card__audience">{safe(resource["audience"])}</p>
        <ul class="plain-list resource-card__list">{highlights}</ul>
        <a class="button button--small" href="{safe(resource['filePath'])}" download> {safe(resource["downloadLabel"])} </a>
      </div>
    </article>
    """


def render_exercise_card(exercise: dict) -> str:
    return f"""
    <article class="exercise-card">
      <a class="exercise-card__poster-link" href="{exercise_href(exercise['slug'])}">
        <img class="exercise-card__poster" src="{safe(exercise['posterPath'])}" alt="Постер упражнения: {safe(exercise['title'])}">
      </a>
      <div class="exercise-card__body">
        <div class="content-card__meta">
          <span>{safe(exercise["level"])}</span>
          <span>{safe(exercise["duration"])}</span>
        </div>
        <h3><a href="{exercise_href(exercise['slug'])}">{safe(exercise["title"])}</a></h3>
        <p>{safe(exercise["summary"])}</p>
        <p class="exercise-card__focus">Фокус: {safe(exercise["focus"])}</p>
        <a class="text-link" href="{exercise_href(exercise['slug'])}">Смотреть разбор</a>
      </div>
    </article>
    """


def render_article_sections(article: dict) -> str:
    rendered = []
    for section in article["sections"]:
        paragraphs = "".join(f"<p>{safe(text)}</p>" for text in section.get("paragraphs", []))
        bullets = section.get("bullets", [])
        bullet_list = ""
        if bullets:
            bullet_list = (
                '<ul class="plain-list article-bullets">'
                + "".join(f"<li>{safe(item)}</li>" for item in bullets)
                + "</ul>"
            )
        callout = ""
        if section.get("callout"):
            callout = f'<aside class="callout">{safe(section["callout"])}</aside>'
        rendered.append(
            f"""
            <section class="article-section">
              <h2>{safe(section["heading"])}</h2>
              {paragraphs}
              {bullet_list}
              {callout}
            </section>
            """
        )
    return "".join(rendered)


def render_index(data: dict) -> str:
    site = data["site"]
    articles = {article["slug"]: article for article in data["articles"]}
    resources = {resource["slug"]: resource for resource in data["resources"]}
    exercises = {exercise["slug"]: exercise for exercise in data["exercises"]}

    featured_articles = "".join(
        render_article_card(articles[slug]) for slug in site["featuredArticleSlugs"]
    )
    featured_resources = "".join(
        render_resource_card(resources[slug]) for slug in site["featuredResourceSlugs"]
    )
    featured_exercises = "".join(
        render_exercise_card(exercises[slug]) for slug in site["featuredExerciseSlugs"]
    )

    constraints = "".join(
        f'<span class="chip">{safe(note)}</span>' for note in site["githubPagesNotes"]
    )

    body = f"""
    <section class="hero shell">
      <div class="hero__copy">
        <p class="eyebrow">Публичный гид</p>
        <h1>{safe(site["title"])}</h1>
        <p class="hero__tagline">{safe(site["tagline"])}</p>
        <p class="hero__text">{safe(site["heroIntro"])}</p>
        <div class="hero__actions">
          <a class="button" href="habits.html">Читать материалы</a>
          <a class="button button--ghost" href="exercises.html">Открыть упражнения</a>
        </div>
      </div>
      <div class="hero__stats">
        {render_stat_card("Статьи", str(len(data["articles"])), "Короткие объяснения без перегруза")}
        {render_stat_card("PDF", str(len(data["resources"])), "Легкие материалы для скачивания")}
        {render_stat_card("Видео", str(len(data["exercises"])), "Локальные файлы, совместимые с GitHub Pages")}
      </div>
    </section>

    <section class="shell section">
      {render_section_intro("Навигация", "Три входа в контент", "Сначала можно пройти базовые статьи о системе привычек, затем скачать вспомогательные PDF и перейти к спокойным упражнениям для поддержки тела.")}
      <div class="grid-three">
        <article class="spotlight-card">
          <p class="spotlight-card__eyebrow">Привычки</p>
          <h3>Малые шаги вместо всплесков мотивации</h3>
          <p>Раздел помогает выстроить старт, удерживать ритм и уменьшать трение через среду, а не через самодавление.</p>
          <a class="text-link" href="habits.html">Открыть раздел</a>
        </article>
        <article class="spotlight-card">
          <p class="spotlight-card__eyebrow">PDF</p>
          <h3>Дополнительные материалы на одну страницу</h3>
          <p>Шпаргалки и формы для практики можно скачать напрямую без регистрации и лишних переходов.</p>
          <a class="text-link" href="resources.html">Перейти к файлам</a>
        </article>
        <article class="spotlight-card">
          <p class="spotlight-card__eyebrow">Упражнения</p>
          <h3>Мягкие практики с текстовым описанием</h3>
          <p>Каждое упражнение сопровождается локальным видеофайлом, структурой шагов и предупреждениями по безопасности.</p>
          <a class="text-link" href="exercises.html">Смотреть упражнения</a>
        </article>
      </div>
    </section>

    <section class="shell section">
      {render_section_intro("Избранное", "С чего начать", "На старте достаточно выбрать один материал про привычки, один PDF и одно упражнение. Этого хватит, чтобы получить рабочую первую неделю практики.")}
      <div class="cards-grid cards-grid--articles">
        {featured_articles}
      </div>
    </section>

    <section class="shell section">
      <div class="cards-grid cards-grid--resources">
        {featured_resources}
      </div>
    </section>

    <section class="shell section">
      <div class="cards-grid cards-grid--exercises">
        {featured_exercises}
      </div>
    </section>

    <section class="shell section">
      {render_section_intro("GitHub Pages", "Ограничения учтены в структуре", "Первая версия намеренно сделана легкой: контент хранится в файлах, ссылки остаются относительными, а медиатека собрана компактно, чтобы сайт спокойно публиковался как project site на GitHub Pages.")}
      <div class="chips-wrap">
        {constraints}
      </div>
    </section>
    """
    return render_layout("Главная", site["description"], site, "index", body)


def render_habits_page(data: dict) -> str:
    site = data["site"]
    cards = "".join(render_article_card(article) for article in data["articles"])
    body = f"""
    <section class="page-hero shell">
      <p class="eyebrow">Раздел материалов</p>
      <h1>Привычки как система, а не как марафон воли</h1>
      <p>В этом разделе собраны короткие тексты о том, как запускать новую привычку через ясные сигналы, малый порог входа и спокойный недельный обзор.</p>
    </section>
    <section class="shell section">
      <div class="cards-grid cards-grid--articles">
        {cards}
      </div>
    </section>
    """
    return render_layout(
        "Материалы о привычках",
        "Статьи о формировании привычек, настройке среды и недельном обзоре.",
        site,
        "habits",
        body,
    )


def render_article_page(data: dict, article: dict) -> str:
    site = data["site"]
    body = f"""
    <section class="page-hero shell page-hero--narrow">
      <p class="eyebrow">{safe(article["category"])}</p>
      <h1>{safe(article["title"])}</h1>
      <p class="hero__tagline">{safe(article["summary"])}</p>
      <div class="hero-meta">
        <span>{safe(article["readTime"])}</span>
        <span>Раздел: привычки</span>
      </div>
      <p><a class="text-link" href="habits.html">← Вернуться к списку материалов</a></p>
    </section>
    <article class="shell article-layout">
      {render_article_sections(article)}
    </article>
    """
    return render_layout(article["title"], article["summary"], site, "habits", body)


def render_resources_page(data: dict) -> str:
    site = data["site"]
    cards = "".join(render_resource_card(resource) for resource in data["resources"])
    body = f"""
    <section class="page-hero shell">
      <p class="eyebrow">PDF-библиотека</p>
      <h1>Дополнительные материалы для самостоятельной практики</h1>
      <p>Файлы открываются и скачиваются напрямую. Карточки сделаны легкими по весу, а сами PDF подходят для GitHub Pages и быстрой публикации без внешнего хранилища.</p>
    </section>
    <section class="shell section">
      <div class="cards-grid cards-grid--resources">
        {cards}
      </div>
    </section>
    """
    return render_layout(
        "PDF-материалы",
        "Каталог PDF-файлов с короткими описаниями и прямым скачиванием.",
        site,
        "resources",
        body,
    )


def render_exercises_page(data: dict) -> str:
    site = data["site"]
    cards = "".join(render_exercise_card(exercise) for exercise in data["exercises"])
    body = f"""
    <section class="page-hero shell">
      <p class="eyebrow">Видео и описания</p>
      <h1>Физические упражнения с мягкой подачей</h1>
      <p>Раздел собран как публичная библиотека упражнений: локальные видеофайлы, краткое описание, шаги выполнения и обязательные предупреждения по безопасности.</p>
      <aside class="callout">{safe(site["disclaimer"])}</aside>
    </section>
    <section class="shell section">
      <div class="cards-grid cards-grid--exercises">
        {cards}
      </div>
    </section>
    """
    return render_layout(
        "Упражнения",
        "Каталог упражнений с локальными видеофайлами и текстовым описанием выполнения.",
        site,
        "exercises",
        body,
    )


def render_exercise_page(data: dict, exercise: dict) -> str:
    site = data["site"]
    benefits = "".join(f"<li>{safe(item)}</li>" for item in exercise["benefits"])
    steps = "".join(f"<li>{safe(item)}</li>" for item in exercise["steps"])
    cautions = "".join(f"<li>{safe(item)}</li>" for item in exercise["cautions"])

    body = f"""
    <section class="page-hero shell page-hero--narrow">
      <p class="eyebrow">Упражнение</p>
      <h1>{safe(exercise["title"])}</h1>
      <p class="hero__tagline">{safe(exercise["summary"])}</p>
      <div class="hero-meta">
        <span>{safe(exercise["level"])}</span>
        <span>{safe(exercise["duration"])}</span>
        <span>{safe(exercise["focus"])}</span>
      </div>
      <p><a class="text-link" href="exercises.html">← Вернуться к каталогу упражнений</a></p>
    </section>

    <section class="shell exercise-detail">
      <div class="exercise-detail__media">
        <video class="exercise-video" controls preload="metadata" poster="{safe(exercise['posterPath'])}">
          <source src="{safe(exercise['videoPath'])}" type="video/mp4">
          Ваш браузер не поддерживает HTML5 video.
        </video>
        <p class="media-note">{safe(exercise["videoNote"])}</p>
      </div>

      <aside class="exercise-detail__aside">
        <div class="info-panel">
          <p class="info-panel__label">Фокус</p>
          <p>{safe(exercise["focus"])}</p>
        </div>
        <div class="info-panel">
          <p class="info-panel__label">Польза</p>
          <ul class="plain-list">{benefits}</ul>
        </div>
      </aside>
    </section>

    <section class="shell section">
      <div class="detail-grid">
        <article class="detail-card">
          <h2>Как выполнять</h2>
          <ol class="steps-list">{steps}</ol>
        </article>
        <article class="detail-card detail-card--warning">
          <h2>Осторожность и ограничения</h2>
          <ul class="plain-list">{cautions}</ul>
          <p class="detail-card__disclaimer">{safe(site["disclaimer"])}</p>
        </article>
      </div>
    </section>
    """
    return render_layout(exercise["title"], exercise["summary"], site, "exercises", body)


def render_404(data: dict) -> str:
    site = data["site"]
    body = """
    <section class="shell empty-state">
      <p class="eyebrow">404</p>
      <h1>Страница не найдена</h1>
      <p>Возможно, материал был перемещен или ссылка ведет по старому адресу. Вернитесь на главную и продолжите навигацию оттуда.</p>
      <a class="button" href="index.html">На главную</a>
    </section>
    """
    return render_layout("Страница не найдена", site["description"], site, "", body)


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def main() -> None:
    data = load_content()
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    write_text(SITE_DIR / "index.html", render_index(data))
    write_text(SITE_DIR / "habits.html", render_habits_page(data))
    write_text(SITE_DIR / "resources.html", render_resources_page(data))
    write_text(SITE_DIR / "exercises.html", render_exercises_page(data))
    write_text(SITE_DIR / "404.html", render_404(data))
    write_text(SITE_DIR / "robots.txt", "User-agent: *\nAllow: /\n")
    write_text(SITE_DIR / ".nojekyll", "")

    for article in data["articles"]:
        write_text(SITE_DIR / article_href(article["slug"]), render_article_page(data, article))

    for exercise in data["exercises"]:
        write_text(SITE_DIR / exercise_href(exercise["slug"]), render_exercise_page(data, exercise))

    print("Built static pages in site/.")


if __name__ == "__main__":
    try:
        main()
    except ContentError as exc:
        raise SystemExit(f"Content error: {exc}") from exc
