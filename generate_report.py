#!/usr/bin/env python3
"""Generate the HeyGen dubbing benchmark report as a static HTML page."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.json"

DEFAULT_BASE_URL = "videos"

# ── Curated examples ──

POSITIVE_EXAMPLES = [
    {
        "id": "frontal-lip-sync",
        "title": "Frontal Dialogue Lip Sync",
        "description": "Standard frontal dialogue produces good lip sync quality with natural-sounding voice and accurate mouth movements.",
        "clip": "forrest_gump_clip_2",
        "lang": "Russian",
        "clip_label": "Forrest Gump — bench scene",
    },
    {
        "id": "named-entities",
        "title": "Named Entities and Proper Nouns",
        "description": "Location names, technical terms, and proper nouns are correctly preserved across languages rather than being mistranslated.",
        "clip": "black_widow_avengers_clip_2",
        "lang": "Hebrew (Israel)",
        "clip_label": "Black Widow — phone call ('Zelinsky Plaza')",
    },
    {
        "id": "non-human",
        "title": "Non-Human and Animated Subjects",
        "description": "CGI and animated characters with non-human face geometry are handled well, with accurate lip sync on stylized mouths.",
        "clip": "zootopia_clip_1",
        "lang": "Spanish",
        "clip_label": "Zootopia — animated animal characters",
    },
    {
        "id": "background-audio",
        "title": "Background Audio Preservation",
        "description": "Background music, sound effects, and ambient sounds are preserved in the dubbed output while the speech is replaced. The sound of a lighter hitting the table is clearly retained.",
        "clip": "lawrence_of_arabia_clip_2",
        "lang": "Spanish",
        "clip_label": "Lawrence of Arabia — lighter on table",
    },
    {
        "id": "full-occlusion",
        "title": "Full Occlusion / Hidden Lips",
        "description": "When lips are consistently hidden behind a mask or in shadow, the model handles the dubbing well without visual artifacts.",
        "clip": "v_for_vendetta_clip_1",
        "lang": "Dutch",
        "clip_label": "V for Vendetta — full face mask",
    },
    {
        "id": "off-screen",
        "title": "Off-Screen and Phone Speech",
        "description": "Speech from an unseen speaker (phone calls, camera cuts away) is handled correctly, even preserving phone-call audio characteristics.",
        "clip": "black_widow_avengers_clip_2",
        "lang": "Hebrew (Israel)",
        "clip_label": "Black Widow — phone call with static",
    },
    {
        "id": "character-accent",
        "title": "Character Accent Preservation",
        "description": "The distinctive accent quality of the original character is reflected in the translated voice.",
        "clip": "forrest_gump_clip_2",
        "lang": "Russian",
        "clip_label": "Forrest Gump — distinctive Southern accent",
    },
]

NEGATIVE_EXAMPLES = [
    {
        "id": "singing",
        "title": "Singing",
        "description": "The model cannot make characters sing. It speaks the lyrics instead, completely losing rhythm and melody. Background music is preserved but the vocal performance is lost.",
        "clip": "kate_bush_wuthering_heights_clip_1",
        "lang": "Spanish",
        "clip_label": "Kate Bush — 'Wuthering Heights'",
    },
    {
        "id": "side-profile",
        "title": "Side Profile Lip Sync",
        "description": "Side-profile shots produce blurry, jittering lips. Especially problematic when combined with eating or hand-to-face gestures.",
        "clip": "pulp_fiction_clip_1",
        "lang": "Hebrew (Israel)",
        "clip_label": "Pulp Fiction — Uma Thurman eating",
    },
    {
        "id": "temp-occlusion",
        "title": "Temporary Lip Occlusion",
        "description": "When an object briefly passes over the lips (hand, person, microphone), the generated lips jitter and produce visual artifacts. Unlike full occlusion which works well, intermittent occlusion is problematic.",
        "clip": "godfather_clip_1",
        "lang": "Swedish",
        "clip_label": "Godfather — lips jitter when occluded",
    },
    {
        "id": "lips-on-arm",
        "title": "Lips Generated on Wrong Surface",
        "description": "When a hand or arm covers the mouth, the model sometimes generates lip movements on the occluding object rather than the face.",
        "clip": "taylor_swift_shake_it_off_clip_3",
        "lang": "Czech",
        "clip_label": "Taylor Swift — lips appear on arm",
    },
    {
        "id": "voice-consistency",
        "title": "Distinctive Voice Preservation",
        "description": "Unique and recognizable voices are poorly preserved. The translated voice sounds generic rather than matching the character's distinctive quality.",
        "clip": "harry_potter_expelliarmus_clip_2",
        "lang": "Spanish",
        "clip_label": "HP — Snape's voice lost",
    },
    {
        "id": "emotion-lost",
        "title": "Emotional Intensity",
        "description": "Strong emotion in the original is lost in translation. The king screams 'forget about the blessed shilling' with real fury, but the dubbed voice sounds calm and measured. The model flattens vocal intensity regardless of the original performance.",
        "clip": "kings_speech_clip_1",
        "lang": "Korean",
        "clip_label": "The King's Speech — screaming flattened",
    },
    {
        "id": "stammering",
        "title": "Non-Standard Speech Patterns",
        "description": "Stammering, gurgling, and non-speech vocalizations are removed. The model normalizes all speech, losing important character and narrative details.",
        "clip": "kings_speech_clip_3",
        "lang": "Spanish",
        "clip_label": "The King's Speech — stammering removed",
    },
    {
        "id": "nonverbal-vocalizations",
        "title": "Non-Verbal Vocalizations Removed",
        "description": "Non-speech vocalizations that are integral to the scene — such as gurgling, choking, or struggling to speak — are completely stripped out. The model only translates clean words, losing vocalizations that carry narrative meaning.",
        "clip": "kings_speech_clip_2",
        "lang": "Hebrew (Israel)",
        "clip_label": "The King's Speech — gurgling removed",
    },
    {
        "id": "overlapping-speakers",
        "title": "Overlapping Speakers",
        "description": "When two speakers talk simultaneously or one cuts into another, the model mutes one of them entirely. The anchor on the left speaks during the clip but all translations silence her, producing a monologue instead of the original crosstalk.",
        "clip": "fox_news_clip_2",
        "lang": "Spanish",
        "clip_label": "Fox News — second anchor muted",
    },
    {
        "id": "bg-music-desync",
        "title": "Lip Sync Degrades with Background Music",
        "description": "When background music is present, the lip sync quality degrades noticeably. The audio track is well-preserved but the dubbed speech drifts out of sync with the mouth movements.",
        "clip": "fight_club_pixies_clip_1",
        "lang": "Spanish",
        "clip_label": "Fight Club — speech out of sync despite good audio",
    },
    {
        "id": "tight-lips",
        "title": "'Tight Lips' Artifact",
        "description": "When a character's lips are tightly sealed between speech segments, the model cannot reproduce this. The video 'jumps' when speech resumes, creating a visible discontinuity.",
        "clip": "forrest_gump_clip_1",
        "lang": "Russian",
        "clip_label": "Forrest Gump — video jumps between segments",
    },
]


def lang_to_filename_part(lang: str) -> str:
    return lang.replace("/", "-").replace(" ", "_")


def load_manifests() -> list[dict]:
    manifests = []
    for d in sorted(RESULTS_DIR.iterdir()):
        mp = d / "manifest.json"
        if mp.exists():
            manifests.append(json.loads(mp.read_text()))
    return manifests


def compute_stats(manifests: list[dict]) -> dict:
    total_clips = len(manifests)
    total_success = sum(m.get("successful", 0) for m in manifests)
    total_failed = sum(m.get("failed", 0) for m in manifests)
    total_jobs = total_success + total_failed
    perfect = sum(1 for m in manifests if m.get("failed", 0) == 0 and m.get("successful", 0) > 0)
    all_failed = sum(1 for m in manifests if m.get("successful", 0) == 0)
    return {
        "total_clips": total_clips,
        "total_jobs": total_jobs,
        "total_success": total_success,
        "total_failed": total_failed,
        "success_rate": total_success / total_jobs * 100 if total_jobs else 0,
        "perfect_clips": perfect,
        "all_failed_clips": all_failed,
    }


def video_url(base_url: str, clip_folder: str, lang: str | None = None) -> str:
    if lang is None:
        return f"{base_url}/originals/{clip_folder}.mp4"
    safe_lang = lang_to_filename_part(lang)
    return f"{base_url}/translations/{clip_folder}_{safe_lang}.mp4"


def generate_example_html(ex: dict, base_url: str, idx: int) -> str:
    orig_url = video_url(base_url, ex["clip"])
    trans_url = video_url(base_url, ex["clip"], ex["lang"])
    pair_id = f"pair-{ex['id']}"
    return f"""
    <div class="example" id="{ex['id']}">
      <h4>{ex['title']}</h4>
      <p class="example-desc">{html.escape(ex['description'])}</p>
      <p class="example-clip">{html.escape(ex['clip_label'])}</p>
      <div class="video-pair" data-pair="{pair_id}">
        <div class="video-container">
          <video id="{pair_id}-orig" loop muted playsinline preload="metadata">
            <source src="{orig_url}" type="video/mp4">
          </video>
          <div class="video-controls">
            <button class="play-btn" data-pair="{pair_id}" title="Play/Pause">&#9654;</button>
            <button class="sound-btn" data-video="{pair_id}-orig" data-pair="{pair_id}" title="Toggle sound">&#128264;</button>
          </div>
          <span class="video-label">Original (English)</span>
        </div>
        <div class="video-container">
          <video id="{pair_id}-trans" loop muted playsinline preload="metadata">
            <source src="{trans_url}" type="video/mp4">
          </video>
          <div class="video-controls">
            <button class="play-btn" data-pair="{pair_id}" title="Play/Pause">&#9654;</button>
            <button class="sound-btn" data-video="{pair_id}-trans" data-pair="{pair_id}" title="Toggle sound">&#128264;</button>
          </div>
          <span class="video-label">Translated ({html.escape(ex['lang'])})</span>
        </div>
      </div>
    </div>"""


def generate_results_table(manifests: list[dict], metadata: dict) -> str:
    id_to_tags = {}
    for v in metadata["videos"]:
        stem = v["filename"].rsplit(".", 1)[0]
        id_to_tags[stem] = ", ".join(v.get("tags", []))

    rows = []
    for m in manifests:
        folder = m.get("folder_name", "")
        s = m.get("successful", 0)
        f = m.get("failed", 0)
        total = s + f
        tags = id_to_tags.get(folder, "")
        rate = s / total * 100 if total else 0
        bar_class = "bar-good" if rate >= 95 else "bar-ok" if rate >= 80 else "bar-bad" if rate > 0 else "bar-none"
        rows.append(f"""      <tr>
        <td class="clip-name">{html.escape(folder)}</td>
        <td class="clip-tags">{html.escape(tags)}</td>
        <td class="clip-stats"><span class="{bar_class}">{s}/{total}</span></td>
      </tr>""")
    return "\n".join(rows)


CSS = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.7;
      color: #1a1a2e;
      background: #fafafa;
    }
    .container { max-width: 920px; margin: 0 auto; padding: 0 24px; }

    /* Hero */
    .hero {
      text-align: center;
      padding: 80px 0 40px;
      border-bottom: 1px solid #e0e0e0;
    }
    .hero h1 { font-size: 2.4em; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 12px; }
    .hero .subtitle { font-size: 1.15em; color: #555; margin-bottom: 8px; }
    .hero .date { font-size: 0.9em; color: #888; }

    /* Sections */
    section { padding: 48px 0; border-bottom: 1px solid #eee; }
    section:last-child { border-bottom: none; }
    h2 { font-size: 1.6em; margin-bottom: 20px; font-weight: 700; }
    h3 { font-size: 1.25em; margin-bottom: 16px; font-weight: 600; }
    h4 { font-size: 1.05em; margin-bottom: 8px; font-weight: 600; }
    p { margin-bottom: 12px; }

    /* TLDR */
    .tldr ul { list-style: none; padding-left: 0; }
    .tldr li { padding: 8px 0 8px 24px; position: relative; font-size: 1.05em; }
    .tldr li::before { content: '\\2022'; position: absolute; left: 4px; color: #4a6cf7; font-weight: bold; }

    /* Stats grid */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin: 24px 0;
    }
    .stat-card {
      background: white;
      border: 1px solid #e8e8e8;
      border-radius: 12px;
      padding: 24px;
      text-align: center;
    }
    .stat-number { font-size: 2em; font-weight: 700; color: #4a6cf7; }
    .stat-label { font-size: 0.85em; color: #666; margin-top: 4px; }

    /* Methodology */
    .method-flow {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      flex-wrap: wrap;
      margin: 20px 0;
      font-size: 0.95em;
    }
    .method-step {
      background: white;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 10px 18px;
      font-weight: 500;
    }
    .method-arrow { color: #aaa; font-size: 1.4em; }

    /* Findings sections */
    .findings-positive h2 { color: #16a34a; }
    .findings-negative h2 { color: #dc2626; }

    .example {
      background: white;
      border: 1px solid #e8e8e8;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 28px;
    }
    .example-desc { color: #444; font-size: 0.95em; }
    .example-clip { color: #888; font-size: 0.85em; font-style: italic; margin-bottom: 16px; }

    /* Video pair */
    .video-pair {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    @media (max-width: 640px) {
      .video-pair { grid-template-columns: 1fr; }
    }
    .video-container {
      position: relative;
      background: #000;
      border-radius: 8px;
      overflow: hidden;
    }
    .video-container video {
      width: 100%;
      display: block;
      border-radius: 8px;
    }
    .video-controls {
      position: absolute;
      bottom: 32px;
      left: 0;
      right: 0;
      display: flex;
      justify-content: center;
      gap: 8px;
      opacity: 0;
      transition: opacity 0.25s;
    }
    .video-container:hover .video-controls { opacity: 1; }
    .video-controls button {
      background: rgba(0,0,0,0.65);
      color: white;
      border: none;
      border-radius: 50%;
      width: 36px;
      height: 36px;
      cursor: pointer;
      font-size: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s;
    }
    .video-controls button:hover { background: rgba(0,0,0,0.85); }
    .video-controls button.active { background: rgba(74, 108, 247, 0.85); }
    .video-label {
      display: block;
      text-align: center;
      padding: 8px 0;
      font-size: 0.82em;
      color: #666;
      background: white;
    }

    /* Results table */
    .results-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9em;
      margin-top: 16px;
    }
    .results-table th {
      text-align: left;
      padding: 10px 12px;
      border-bottom: 2px solid #ddd;
      font-weight: 600;
      color: #333;
    }
    .results-table td {
      padding: 8px 12px;
      border-bottom: 1px solid #eee;
    }
    .results-table tr:hover td { background: #f7f7ff; }
    .clip-name { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.88em; }
    .clip-tags { color: #888; font-size: 0.85em; }
    .bar-good { color: #16a34a; font-weight: 600; }
    .bar-ok { color: #ca8a04; font-weight: 600; }
    .bar-bad { color: #dc2626; font-weight: 600; }
    .bar-none { color: #999; }

    /* Footer */
    footer {
      text-align: center;
      padding: 40px 0;
      color: #aaa;
      font-size: 0.85em;
    }
"""

JS = """
    document.addEventListener('DOMContentLoaded', () => {
      // Play/Pause: synced pair
      document.querySelectorAll('.play-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const pairId = btn.dataset.pair;
          const orig = document.getElementById(pairId + '-orig');
          const trans = document.getElementById(pairId + '-trans');
          if (orig.paused) {
            orig.currentTime = 0;
            trans.currentTime = 0;
            orig.play();
            trans.play();
            // Update all play buttons in this pair
            document.querySelectorAll(`.play-btn[data-pair="${pairId}"]`).forEach(b => b.innerHTML = '&#9646;&#9646;');
          } else {
            orig.pause();
            trans.pause();
            document.querySelectorAll(`.play-btn[data-pair="${pairId}"]`).forEach(b => b.innerHTML = '&#9654;');
          }
        });
      });

      // Sound toggle: unmute one, mute the other
      document.querySelectorAll('.sound-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const videoId = btn.dataset.video;
          const pairId = btn.dataset.pair;
          const video = document.getElementById(videoId);
          const orig = document.getElementById(pairId + '-orig');
          const trans = document.getElementById(pairId + '-trans');

          if (video.muted) {
            // Unmute this, mute the other
            orig.muted = true;
            trans.muted = true;
            video.muted = false;
            // Update button states
            document.querySelectorAll(`.sound-btn[data-pair="${pairId}"]`).forEach(b => {
              b.classList.remove('active');
              b.innerHTML = '&#128264;';
            });
            btn.classList.add('active');
            btn.innerHTML = '&#128266;';
          } else {
            video.muted = true;
            btn.classList.remove('active');
            btn.innerHTML = '&#128264;';
          }
        });
      });

      // Sync loop: when one video loops, restart the other
      document.querySelectorAll('video').forEach(v => {
        v.addEventListener('seeked', () => {
          if (v.currentTime < 0.1) {
            const id = v.id;
            const pairId = id.replace(/-orig$/, '').replace(/-trans$/, '');
            const otherId = id.endsWith('-orig') ? pairId + '-trans' : pairId + '-orig';
            const other = document.getElementById(otherId);
            if (other && !other.paused && Math.abs(other.currentTime - v.currentTime) > 0.5) {
              other.currentTime = 0;
            }
          }
        });
      });
    });
"""


def generate_html(base_url: str) -> str:
    manifests = load_manifests()
    stats = compute_stats(manifests)

    with open(METADATA_PATH) as f:
        metadata = json.load(f)

    positive_examples_html = "\n".join(
        generate_example_html(ex, base_url, i)
        for i, ex in enumerate(POSITIVE_EXAMPLES)
    )
    negative_examples_html = "\n".join(
        generate_example_html(ex, base_url, i)
        for i, ex in enumerate(NEGATIVE_EXAMPLES)
    )
    results_rows = generate_results_table(manifests, metadata)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HeyGen Video Dubbing Benchmark</title>
  <style>{CSS}
  </style>
</head>
<body>

  <!-- Hero -->
  <header class="hero">
    <div class="container">
      <h1>HeyGen Video Dubbing Benchmark</h1>
      <p class="subtitle">Evaluating AI-powered video dubbing across 47 clips and 40 languages</p>
      <p class="date">March 2026 &mdash; LTX Research</p>
    </div>
  </header>

  <div class="container">

    <!-- TL;DR -->
    <section class="tldr">
      <h2>Key Takeaways</h2>
      <ul>
        <li><strong>{stats['success_rate']:.0f}% overall success rate</strong> across {stats['total_jobs']:,} dubbing jobs ({stats['total_clips']} clips &times; 40 languages)</li>
        <li><strong>Frontal dialogue works well</strong> &mdash; good lip sync, voice quality, and accent preservation for standard talking-head content</li>
        <li><strong>Non-human and animated characters handled surprisingly well</strong> &mdash; CGI, animated, and masked faces produce quality results</li>
        <li><strong>Singing is a non-starter</strong> &mdash; the model speaks lyrics instead of singing them, losing rhythm and melody entirely</li>
        <li><strong>Distinctive voices and strong emotions are lost</strong> &mdash; unique voices become generic, screaming becomes calm, crying becomes flat</li>
      </ul>
    </section>

    <!-- Overview -->
    <section>
      <h2>Overview</h2>
      <p>We benchmarked HeyGen's video dubbing (via LTX Studio) on a curated set of {stats['total_clips']} video clips spanning 17 categories: frontal dialogue, side profiles, occlusion, singing, animation, CGI, action, and more. Each clip was dubbed into 40 languages covering European, Asian, Middle Eastern, and African language families.</p>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-number">{stats['total_clips']}</div>
          <div class="stat-label">Video clips tested</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">40</div>
          <div class="stat-label">Target languages</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{stats['total_success']:,}</div>
          <div class="stat-label">Successful dubs</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{stats['success_rate']:.0f}%</div>
          <div class="stat-label">Success rate</div>
        </div>
      </div>
    </section>

    <!-- Methodology -->
    <section>
      <h2>Methodology</h2>
      <p>Each video was processed through the LTX Studio API, which wraps HeyGen's <code>/v2/video_translate</code> endpoint. Lip sync was enabled for all runs. The pipeline:</p>
      <div class="method-flow">
        <span class="method-step">Upload video</span>
        <span class="method-arrow">&rarr;</span>
        <span class="method-step">LTX Studio API</span>
        <span class="method-arrow">&rarr;</span>
        <span class="method-step">HeyGen dubbing</span>
        <span class="method-arrow">&rarr;</span>
        <span class="method-step">Download result</span>
      </div>
      <p>All 40 languages were batched into a single task per video. Typical processing time: 8&ndash;10 minutes per clip (all languages in parallel). Results were manually reviewed for lip sync quality, voice consistency, background preservation, and translation fidelity.</p>
    </section>

    <!-- What Works Well -->
    <section class="findings-positive">
      <h2>What Works Well</h2>
{positive_examples_html}
    </section>

    <!-- What Needs Improvement -->
    <section class="findings-negative">
      <h2>What Needs Improvement</h2>
{negative_examples_html}
    </section>

    <!-- Full Results Table -->
    <section>
      <h2>Full Results</h2>
      <p>Success rates per clip (out of 40 languages):</p>
      <table class="results-table">
        <thead>
          <tr>
            <th>Clip</th>
            <th>Category</th>
            <th>Success</th>
          </tr>
        </thead>
        <tbody>
{results_rows}
        </tbody>
      </table>
    </section>

  </div>

  <footer>
    <div class="container">
      HeyGen Video Dubbing Benchmark &mdash; LTX Research, March 2026
    </div>
  </footer>

  <script>{JS}
  </script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate the HeyGen benchmark report")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base URL for video files (default: GCS bucket URL)",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "reports" / "index.html"),
        help="Output HTML file path",
    )
    args = parser.parse_args()

    html_content = generate_html(args.base_url)
    Path(args.output).write_text(html_content)
    print(f"Report generated: {args.output}")
    print(f"Video base URL: {args.base_url}")


if __name__ == "__main__":
    main()
