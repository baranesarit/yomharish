---
name: alma-ulama-video
description: Edit a raw vertical clip of Alma into a finished "עלמא ולמה?" (Alma ulama) episode — logo intro with the theme song, tightened cut, pop-up Hebrew captions with yellow keywords, hook box, location tag, and an Instagram/TikTok end card with the last line of the theme. Use whenever the user sends a new Alma video / asks for a new episode of עלמא ולמה, or asks to fix/shorten/re-caption an existing one ("פרק חדש", "עלמא מסבירה על...", "תקצר", "תתקן כתובית").
---

# עלמא ולמה? — episode pipeline

Everything an episode needs is in this folder: `assets/logo.png`, `assets/theme.mp3`
(the Suno theme, 11.6s), `assets/fonts/Heebo-Black-HebLatin.ttf` (Hebrew + Latin
digits, OFL), and `scripts/`. Output is 576×1024, 30fps, H.264/AAC, loudness −15 LUFS.

## Hard rules (from the creator)

1. **Logo + episode title are on screen from the very first frame** — always inside the
   first 0.5s. `intro.py` draws them fully at frame 0 and only adds a "punch" accent;
   never add a fade-in, slide-in or grow-from-zero to the logo or title. Check frames at
   0.0s and 0.5s in the preview every time.
2. Intro music = `assets/theme.mp3`; the song's last line "עלמא ולמה?" (from 9.0s)
   plays again over the end card.
3. End card: blurred freeze + logo + "מוזמנים לעקוב אחרינו / באינסטגרם @sarita.baranes /
   ובטיקטוק @sarita.baranes". (Not "בפרק הבא".)
4. Keep it tight — long raw clips should end up roughly 60–95s of footage. Cut pauses,
   retakes, stutters ("את ה... את ה..."), and tangents that confuse the story; keep the
   question → answer flow, the fun kid moments, and a punchy ending.
5. Captions are what was said, lightly corrected. The off-camera adult greets with
   "היי" (Whisper sometimes hears a name like "טלי" — it is "היי").

## Workflow

1. **Setup** (fresh container): `bash .claude/skills/alma-ulama-video/scripts/setup.sh`.
   Hugging Face hosts must be allowed in the environment for the first model download.
2. **Look**: `ffprobe` the clip and make a contact sheet
   (`ffmpeg -i in.mov -vf "fps=1/5,scale=120:-1,tile=10x3" -frames:v 1 sheet.jpg`) to see
   the location and framing.
3. **Transcribe**: `python3 scripts/transcribe.py in.mov work/words.json` — prints every
   word with `[start-end]` seconds. Read it, understand the story, and fix mishearings
   from context (e.g. אורחות→לוחות, נער רגל→נהר רגיל, שאיחד→שיחד). If a phrase is
   genuinely unclear, cross-check with `ALMA_WHISPER=ivrit-ai/whisper-large-v3-ct2` on a
   short excerpt, then pick the sensible reading and **tell the user which words you
   guessed**.
4. **Write the episode JSON** next to the words file (see `examples/qasr-al-yahud.json`):

   | field | meaning |
   |---|---|
   | `video`, `words`, `out` | paths (relative to the JSON) |
   | `title` | episode name, big yellow (auto-fits width) — e.g. "קומראן", "קאסר אל יהוד" |
   | `subtitle` | short white pill under the title — e.g. "מעברות הירדן" |
   | `hook` | yellow box on top for the whole video, a teasing question ending in "???"; `\\N` = line break |
   | `tag` | location pill shown 0.3–4.6s, "מקום • אזור" |
   | `segments` | `[[start,end],...]` source seconds to keep, **in play order** (may reorder). Omit = whole clip. Start ~0.1s before the first word, end ~0.1s after the last; never cut inside a word. |
   | `fixes` | `{"heard": "correct"}` per Whisper token (punctuation included, e.g. `"רגל.": "רגיל."`); `""` drops a token; `"מ": "מ־"` joins a prefix to the next word |
   | `glue` | words that must stay on the same caption as the following word ("ארון" → "ארון הברית") |
   | `highlights` | words shown in yellow — places, names, numbers, key terms of the episode |
   | `handles` | `{"instagram": "sarita.baranes", "tiktok": "sarita.baranes"}` (default) |

5. **Render**: `python3 scripts/render.py work/episode.json --preview` (~3 min on 4 CPUs).
   Then check `work_*/captions.txt` (every caption with timing) and look at
   `*_preview.png` — frames at 0.0s, 0.5s, footage, and the end card. Grab full-size
   frames for anything doubtful (RTL punctuation, a word split across captions, text off
   the edge). Iterate on the JSON, not on the scripts.
6. **Deliver**: copy the mp4 to the repo root as `<topic>-alma-ulama.mp4`, keep the
   episode JSON + words file under `episodes/<topic>/`, commit, push, and send the file
   with SendUserFile. Tell the user in Hebrew what was cut, and which words were guessed.

## Notes / gotchas

- Hebrew in ASS: every caption line ends with U+200F (RLM) so "?" and "!" land on the
  left; Latin handles are wrapped in U+200E. `render.py` does this already.
- Theme timing constants live at the top of `render.py` (`INTRO=9.6`, `THEME_LEN=11.6`,
  `LAST_LINE=9.0`). If the user supplies a new theme song, transcribe it to find where the
  last line starts and update them.
- The Suno page cannot be downloaded without the user's login — ask the user to upload the
  MP3 (⋯ → Download → MP3 Audio) instead of trying to fetch it.
- Footage of other aspect ratios is scaled to cover 576×1024 and center-cropped.
