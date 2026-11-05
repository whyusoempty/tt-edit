# FEARS TO FATHOM: 05:00 AM

Второй lyric video на тот же трек, в стилистике psychological horror от первого лица. Первый проект в корне папки не тронут.

Готовое видео: `renders/FTF-0500AM.mp4` (1500×1500, 30 fps, 26.68 с, оригинальный звук).

## Файлы

| Файл | Что внутри |
| --- | --- |
| `index.html` | Корневая композиция: мир, интерфейс, трек |
| `compositions/world.html` | Three.js: квартира, свет, силуэт, камера, VHS-обработка, веки |
| `compositions/hud.html` | GSAP: субтитры рассказчика, подсказки `[E]`, прицел, уведомление и телефон с Telegram |
| `DIRECTION.md` | Режиссёрская карта: что происходит на каждой строке |
| `assets/fonts/` | EB Garamond (субтитры) и Inter (интерфейс), оба с кириллицей |

Тайминги строк и слов взяты из `../transcript/TRANSCRIPT.md` без изменений.

## Как пересобрать

```bash
npx hyperframes check --json
npx hyperframes snapshot --at 7.3,13.25,22.4,25.0 --no-end -o snaps/x
npx hyperframes render -q delivery -o renders/raw.mp4
ffmpeg -y -i renders/raw.mp4 -i assets/track.mp3 -map 0:v -map 1:a -c copy -t 26.68 -movflags +faststart renders/FTF-0500AM.mp4
```

Последний шаг обязателен: рендерер сам понижает громкость на 3 dB, поэтому звук подменяется исходным треком.

Звук кладётся в MP4 исходным MP3-потоком без перекодирования (`-c copy`). Встроенный AAC-энкодер ffmpeg на этом очень громком мастере (пики +2.1 dBFS) теряет ещё около 0.6 LU: −5.7 вместо −5.1 LUFS. При копировании потока декодированный звук совпадает с `assets/track.mp3` бит в бит (одинаковый MD5).

## Где что крутить

- Время событий: константы в начале модуля `world.html` (`WALK1`, `T_CLOSE`, `T_FLIP`, `PASS2`, `T_LAMP_OFF`, `FIG_DOOR`, `FIG_BED`, `T_BLACK`).
- Камера: вызовы `K(время, позиция, точка взгляда, опции)` в разделе `camera path`.
- Яркость: `uExp` в `renderAt`, моргания в `lidAt`, расфокус в `blurAt`.
- Текст и подсказки: `hud.html`. Каждое слово появляется в момент из `data-t`.
