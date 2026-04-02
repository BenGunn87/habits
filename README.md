# Практика Привычек

Статический сайт о выработке привычек, PDF-материалах и упражнениях. Проект рассчитан на размещение через GitHub Pages и не требует внешних npm-зависимостей.

## Запуск

```bash
npm run build
npm run validate
npm run serve
```

Сайт будет доступен по адресу `http://localhost:4173`.

## Как обновлять контент

1. Для общих текстов сайта отредактируйте [`content/site.json`](./content/site.json).
2. Для нового материала скопируйте подходящий шаблон из [`content/templates`](./content/templates):
   - статья: [`content/templates/article.md`](./content/templates/article.md)
   - PDF-материал: [`content/templates/resource.md`](./content/templates/resource.md)
   - упражнение: [`content/templates/exercise.md`](./content/templates/exercise.md)
3. Переименуйте новый файл в slug на латинице и с дефисами, например `morning-reset.md`.
4. Положите файл в нужную папку:
   - статьи: [`content/articles`](./content/articles)
   - PDF-материалы: [`content/resources`](./content/resources)
   - упражнения: [`content/exercises`](./content/exercises)
5. Если это PDF или упражнение, добавьте ассеты с тем же slug:
   - PDF: `site/assets/files/{slug}.pdf`
   - обложка PDF: `site/assets/images/resource-{slug}.svg`
   - видео упражнения: `site/assets/media/{slug}.mp4`
   - постер упражнения: `site/assets/images/poster-{slug}.svg`
6. При необходимости добавьте slug в featured-списки внутри [`content/site.json`](./content/site.json).
7. Выполните `npm run build`.
8. Проверьте `npm run validate`.

## Структура

- `content/site.json` - общие тексты сайта и featured-списки.
- `content/articles/` - статьи, по одному Markdown-файлу на материал.
- `content/resources/` - PDF-материалы, по одному Markdown-файлу на материал.
- `content/exercises/` - упражнения, по одному Markdown-файлу на материал.
- `content/templates/` - шаблоны для добавления новых материалов.
- `scripts/generate_media.py` - генерация стартовых PDF и легких MP4-заглушек.
- `scripts/content_loader.py` - чтение `site.json` и Markdown-контента.
- `scripts/build_site.py` - сборка HTML-страниц в папку `site/`.
- `scripts/validate_content.py` - проверки ссылок, slug и веса медиафайлов.
- `site/` - готовый статический сайт и ассеты для GitHub Pages.

## GitHub Pages

Проект публикуется через workflow [`pages.yml`](./.github/workflows/pages.yml). При деплое workflow:

1. генерирует медиафайлы;
2. собирает HTML из JSON;
3. валидирует контент;
4. публикует папку `site/` как GitHub Pages artifact.

В стартовой версии раздел упражнений использует очень легкие локальные MP4-заглушки, чтобы структура каталога и проигрыватель были рабочими сразу. Их можно заменить собственными роликами без переделки страниц, сохранив те же пути к файлам.
