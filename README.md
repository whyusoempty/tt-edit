# /tt-edit — lyric video в эстетике видеоигры

Скилл для [Claude Code](https://claude.com/claude-code): из MP3 и текста песни делает короткий lyric video (эдит) в стиле видеоигры любой эпохи и жанра. Стиль модель подбирает под конкретный текст и звучание трека. Видео собирается через [HyperFrames](https://hyperframes.heygen.com) + Three.js / Canvas.

Как идёт работа:

1. MP3. Если трек длинный, модель предлагает самые энергичные отрывки.
2. Текст песни.
3. Анализ трека: тайминги каждого слова, доли, паузы вокала и грубый профиль звучания.
4. Модель угадывает звучание и предлагает формат (1:1, 9:16, 16:9). Пользователь поправляет.
5. Пять стилей под этот трек.
6. Где живёт текст: интерфейс, игровой мир или микс. Если уместно — нужен ли Blender.
7. Три сценария на выбор.
8. Готовый MP4 с оригинальным звуком, бит в бит.

## Установка — одной командой

macOS / Linux / Git Bash:

```bash
git clone https://github.com/whyusoempty/tt-edit ~/.claude/skills/tt-edit
```

Windows PowerShell:

```powershell
git clone https://github.com/whyusoempty/tt-edit "$env:USERPROFILE\.claude\skills\tt-edit"
```

Или через [skills CLI](https://skills.sh): `npx skills add whyusoempty/tt-edit`.

Перезапусти Claude Code и напиши `/tt-edit` (можно сразу с путём: `/tt-edit song.mp3`). При первом запуске скилл сам проверит окружение (`scripts/doctor.py`) и скажет, чего не хватает.

Обновление: `git -C ~/.claude/skills/tt-edit pull`.

## Что нужно

- **Node.js 20+** и HyperFrames CLI + скиллы HyperFrames: `npx hyperframes skills update`.
- **ffmpeg / ffprobe** в PATH.
- **Python 3.9+**: `pip install numpy librosa soundfile demucs faster-whisper torch`. Pillow — только для Blender-текстур.
- GPU желателен, но не обязателен: Demucs и Whisper на CPU просто медленнее. Рендер 30-секундного ролика на RTX 5070 занимает 1.5–5 минут, в зависимости от стиля.
- **Blender** не обязателен. Он нужен только стилям с живыми персонажами крупным планом или сложными интерьерами, и скилл спросит про него сам.

## Что внутри

| Путь | Что |
| --- | --- |
| `SKILL.md` | Порядок опроса, правила, сборка и рендер |
| `references/styles.md` | Как собрать пять стилей, как угадать звучание, звучание → стиль |
| `references/text-placement.md` | Текст в UI / в мире / микс, безопасные зоны 9:16 |
| `references/blender.md` | Когда Blender уместен, связка Blender → GLB → HyperFrames, персонажи |
| `references/build.md` | Движки (PS1, рейкастер, VHS, фотореал, карандаш), камера, ритм, шрифты, грабли |
| `scripts/` | `doctor.py` — проверка окружения, `new_project.py` — папка, отрывок и каркас проекта, `prepare.py` — анализ трека, `finalize.py` — исходный звук в MP4 и отчёт |
| `examples/` | Код семи готовых роликов, по папке на технику; оглавление — `examples/README.md` |
| `assets/fonts/` | Шрифты с кириллицей под OFL (`OFL.txt`) |

## Лицензия

Код и тексты — MIT (`LICENSE`). Шрифты — SIL OFL 1.1 (`assets/fonts/OFL.txt`).
