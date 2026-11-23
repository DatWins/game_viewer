#!/usr/bin/env python3
"""
build_viewer.py — Generate a Game Viewer HTML from PGN files.

Usage:
    python build_viewer.py game1.pgn game2.pgn ...
    python build_viewer.py *.pgn
    python build_viewer.py mygames.pgn -o output.html
    python build_viewer.py folder_of_pgns/ -o viewer.html

Each PGN file can contain one or multiple games.
The script reads PGN headers (White, Black, Event, Date, ECO, Opening, Result)
and the moves, then generates a self-contained HTML file identical to the
Game Viewer at datwins.github.io/game_viewer.

Options:
    -o FILE     Output filename (default: game_viewer.html)
    -t TITLE    Page title (default: "Game Viewer")
"""

import sys
import os
import re
import argparse


def parse_pgn_file(filepath):
    """Parse a PGN file and return a list of game dicts."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()

    games = []
    # Split into individual games by looking for [Event lines
    # preceded by a blank line (or start of file)
    game_chunks = re.split(r'\n(?=\[Event\s)', text)

    for chunk in game_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Extract headers
        headers = {}
        for m in re.finditer(r'\[(\w+)\s+"([^"]*)"\]', chunk):
            headers[m.group(1)] = m.group(2)

        # Extract moves — everything after the last ]
        last_bracket = chunk.rfind(']')
        if last_bracket < 0:
            continue
        moves_text = chunk[last_bracket + 1:].strip()

        if not moves_text:
            continue

        # Clean up moves: remove comments {}, variations (), NAGs $N
        moves_text = re.sub(r'\{[^}]*\}', '', moves_text)
        moves_text = re.sub(r'\([^)]*\)', '', moves_text)
        moves_text = re.sub(r'\$\d+', '', moves_text)
        # Remove move numbers like 1. or 1...
        # But keep the actual moves
        moves_text = re.sub(r'\d+\.{3}', '', moves_text)  # remove 1...
        moves_text = re.sub(r'\d+\.', '', moves_text)      # remove 1.
        moves_text = re.sub(r'\s+', ' ', moves_text).strip()

        # Remove result at end
        result = headers.get('Result', '*')
        moves_text = re.sub(r'\s*(1-0|0-1|1/2-1/2|\*)\s*$', '', moves_text).strip()

        if not moves_text:
            continue

        # Rebuild clean PGN with move numbers
        sans = moves_text.split()
        pgn_parts = []
        for i, san in enumerate(sans):
            move_num = (i // 2) + 1
            if i % 2 == 0:
                pgn_parts.append(f'{move_num}.{san}')
            else:
                pgn_parts.append(san)
        clean_pgn = ' '.join(pgn_parts)
        if result and result != '*':
            clean_pgn += ' ' + result

        game = {
            'white': headers.get('White', 'White'),
            'black': headers.get('Black', 'Black'),
            'event': headers.get('Event', ''),
            'date': headers.get('Date', '').split('.')[0] if headers.get('Date') else '',
            'eco': headers.get('ECO', ''),
            'opening': headers.get('Opening', ''),
            'result': result,
            'pgn': clean_pgn
        }

        games.append(game)

    return games


def escape_js(s):
    """Escape a string for use in a JS single-quoted string."""
    return s.replace('\\', '\\\\').replace("'", "\\'")


def build_games_array(games):
    """Build the JavaScript GAMES array source."""
    lines = ['const GAMES = [']
    for i, g in enumerate(games):
        lines.append('  {')
        lines.append(f"    white: '{escape_js(g['white'])}',")
        lines.append(f"    black: '{escape_js(g['black'])}',")
        lines.append(f"    event: '{escape_js(g['event'])}', date: '{escape_js(g['date'])}',")
        lines.append(f"    eco: '{escape_js(g['eco'])}', opening: '{escape_js(g['opening'])}',")
        lines.append(f"    result: '{escape_js(g['result'])}',")
        lines.append(f"    pgn: '{escape_js(g['pgn'])}'")
        comma = ',' if i < len(games) - 1 else ''
        lines.append('  }' + comma)
    lines.append('];')
    return '\n'.join(lines)


def build_sidebar_links(games):
    """Build the sidebar <a> links."""
    lines = []
    for i, g in enumerate(games):
        cls = ' class="on"' if i == 0 else ''
        label = f"{g['white']} – {g['black']}"
        lines.append(f'    <a{cls} data-g="{i}" onclick="loadGame({i})">{label}</a>')
    return '\n'.join(lines)


def build_html(games, title='Game Viewer'):
    """Build the complete self-contained HTML page."""
    # Read the template from the existing index.html
    # Instead, we embed the template directly so the script is self-contained
    games_js = build_games_array(games)
    sidebar = build_sidebar_links(games)

    # The HTML template is the same as index.html but with GAMES and sidebar
    # replaced by the generated content.
    html = TEMPLATE.replace('<!-- GAMES_ARRAY -->', games_js)
    html = html.replace('<!-- SIDEBAR_LINKS -->', sidebar)
    html = html.replace('<!-- PAGE_TITLE -->', title)
    return html


# ─── The full HTML template ───
# This is the game viewer template with placeholders for GAMES array,
# sidebar links, and page title.

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><!-- PAGE_TITLE --></title>
<style>
:root{
  --fs:21px;
  --paper:#fbfaf7; --ink:#1d1f22; --muted:#5d6670; --line:#e2e0da; --side:#f2f0eb;
  --main:#1f4fa3; --var:#2b2f36; --hl:#ffe08a; --hlink:#e8eefb;
  --light:#dee3e6; --dark:#8ca2ad; --lm:rgba(155,199,0,.45); --sel:rgba(20,85,30,.5);
  --btn:#ffffff; --btnb:#cfd5db;
}
:root[data-theme="dark"]{
  --paper:#16191d; --ink:#e4e6e9; --muted:#9aa3ad; --line:#2c3238; --side:#1d2126;
  --main:#86b4ff; --var:#d5d9de; --hl:#6b5a1e; --hlink:#25324a;
  --btn:#232930; --btnb:#3a434c;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--paper);color:var(--ink)}
body{font-family:Georgia,"Iowan Old Style","Palatino Linotype",serif;font-size:var(--fs);line-height:1.6}

/* top bar */
.top{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:10px;padding:8px 16px;background:var(--side);border-bottom:1px solid var(--line);font-family:system-ui,"Segoe UI",sans-serif;font-size:15px}
.top a.lib{color:var(--main);text-decoration:none;font-weight:600;white-space:nowrap}
.top .t{font-weight:700;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
button{font:inherit;font-family:system-ui,"Segoe UI",sans-serif;background:var(--btn);color:var(--ink);border:1px solid var(--btnb);border-radius:7px;padding:6px 12px;cursor:pointer;min-width:40px}
button:hover{border-color:var(--main)}
button:disabled{opacity:.35;cursor:default}

/* 3-column layout: toc | content | board */
.wrap{display:grid;grid-template-columns:230px minmax(0,1fr) auto;align-items:start}
:root{--bw:min(44vw, calc(100vh - 290px), 680px)}

/* left sidebar – game list */
nav.toc{position:sticky;top:49px;height:calc(100vh - 49px);overflow:auto;padding:18px 14px;border-right:1px solid var(--line);background:var(--side);font-family:system-ui,"Segoe UI",sans-serif;font-size:15px}
nav.toc .h{font-weight:700;color:var(--muted);text-transform:uppercase;font-size:12px;letter-spacing:.06em;margin-bottom:8px}
nav.toc a{display:block;padding:8px 10px 8px 12px;margin:2px 0;border-radius:6px;border-left:4px solid transparent;color:var(--ink);font-weight:600;text-decoration:none;cursor:pointer;line-height:1.35}
nav.toc a:hover{background:var(--hlink);color:var(--main)}
nav.toc a.on{background:var(--main);color:#fff;font-weight:700;border-left-color:#f2b500}
:root[data-theme="dark"] nav.toc a.on{color:#111}

/* center content */
main{padding:28px 40px 120px;max-width:44em;margin:0 auto;width:100%}
.kicker{font-family:system-ui,"Segoe UI",sans-serif;font-size:.7em;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
h1{font-family:system-ui,"Segoe UI",sans-serif;font-size:2.3em;line-height:1.1;margin:.2em 0 .15em}
.gamehead{font-size:.9em;line-height:1.5;margin:.4em 0 .8em;color:var(--muted)}
.gamehead b{color:var(--ink)}
h2{font-family:system-ui,"Segoe UI",sans-serif;font-size:1.25em;margin:1.8em 0 .5em;padding-top:.4em;border-top:2px solid var(--line)}
p.ml{line-height:2}
a.mv{display:inline-block;padding:2px 5px;margin:1px;border-radius:4px;text-decoration:none;color:var(--var);border:1px solid transparent;cursor:pointer;font-family:system-ui,"Segoe UI",sans-serif;font-size:.82em}
a.mv:hover{background:var(--hlink);border-color:var(--main);color:var(--main)}
a.mv.cur{background:var(--sel);color:#fff;border-color:transparent;font-weight:700}

/* opening tree */
.tree-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:1em 0}
.tree-cell{cursor:pointer;border:2px solid transparent;border-radius:6px;padding:4px;text-align:center;font-family:system-ui,"Segoe UI",sans-serif;font-size:.65em;font-weight:600;color:var(--muted)}
.tree-cell:hover{border-color:var(--main);background:var(--hlink)}
.tree-cell.on{border-color:var(--sel);background:rgba(20,85,30,.12)}
.mini-bd{display:grid;grid-template-columns:repeat(8,1fr);aspect-ratio:1;border-radius:3px;overflow:hidden}

/* board */
aside.bp{position:sticky;top:49px;padding:16px 20px 16px 10px}
.bhead{font-family:system-ui,"Segoe UI",sans-serif;font-size:.82em;text-align:center;padding:4px 0 8px;min-height:1.6em}
.bwrap{display:flex;align-items:start}
.bd{display:grid;grid-template-columns:repeat(8,1fr);width:var(--bw);height:var(--bw);border-radius:4px;overflow:hidden}
.sq{position:relative;display:flex;align-items:center;justify-content:center}
.sq.l{background:var(--light)}
.sq.d{background:var(--dark)}
.sq.lm{background:var(--lm)}
.pc{position:absolute;inset:0;background-size:100% 100%;background-repeat:no-repeat;z-index:1}
.circ{position:absolute;border-radius:50%;border:3px solid rgba(20,85,30,.8);z-index:3;pointer-events:none}
.sq.lm-from .circ{inset:15%}
.sq.lm-to .circ{inset:8%;border-width:4px;border-color:rgba(20,85,30,.9)}
.rk{display:flex;flex-direction:column;justify-content:space-around;width:18px;font-family:system-ui,"Segoe UI",sans-serif;font-size:11px;color:var(--muted);text-align:center;height:var(--bw)}
.fl{display:flex;justify-content:space-around;font-family:system-ui,"Segoe UI",sans-serif;font-size:11px;color:var(--muted);text-align:center;width:var(--bw);margin-left:18px}
.ctrls{display:flex;gap:6px;justify-content:center;padding:10px 0 2px;margin-left:18px;width:var(--bw)}
.ctrls button{flex:1;font-size:1.1em;padding:8px 0}
.msg{font-family:system-ui,"Segoe UI",sans-serif;font-size:.82em;text-align:center;padding:6px 0;color:var(--muted);min-height:1.8em;margin-left:18px;width:var(--bw)}

/* responsive */
@media(max-width:1100px){
  .wrap{display:block!important}
  nav.toc{display:none}
  aside.bp{position:relative;top:auto;display:flex;flex-direction:column;align-items:center;padding:14px}
  :root{--bw:min(94vw, calc(100vh - 220px), 520px)}
  body.hideb aside.bp{display:none}
  .tog{display:inline-block}
}
@media(min-width:1101px){.tog{display:none}}
@media(max-width:480px){
  :root{--bw:min(97vw,420px);--fs:17px}
  main{padding:16px 10px 80px}
  .tree-grid{grid-template-columns:repeat(3,1fr)}
}
@media(orientation:landscape) and (max-height:500px){
  aside.bp{flex-direction:row;flex-wrap:wrap;justify-content:center;gap:8px}
  :root{--bw:min(45vh, 300px)}
}

/* print */
@media print{
  .top,nav.toc,aside.bp,.ctrls,.tog{display:none!important}
  .wrap{display:block!important}
  main{padding:0!important;max-width:none!important}
  a.mv{color:inherit!important;border:none!important}
  .tree-grid{grid-template-columns:repeat(6,1fr)!important}
  .tree-cell{border:1px solid #ccc!important;break-inside:avoid}
  .tree-cell .mini-bd{width:100%;aspect-ratio:1}
  .tree-cell .mini-bd .sq{position:relative}
  .tree-cell .mini-bd .pc{position:absolute;inset:0;background-size:100% 100%;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .sq.l,.sq.d{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
</style>
<style>
.pc.wP{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PHBhdGggZD0iTTIyLjUgOWMtMi4yMSAwLTQgMS43OS00IDQgMCAuODkuMjkgMS43MS43OCAyLjM4QzE3LjMzIDE2LjUgMTYgMTguNTkgMTYgMjFjMCAyLjAzLjk0IDMuODQgMi40MSA1LjAzLTMgMS4wNi03LjQxIDUuNTUtNy40MSAxMy40N2gyM2MwLTcuOTItNC40MS0xMi40MS03LjQxLTEzLjQ3IDEuNDctMS4xOSAyLjQxLTMgMi40MS01LjAzIDAtMi40MS0xLjMzLTQuNS0zLjI4LTUuNjIuNDktLjY3Ljc4LTEuNDkuNzgtMi4zOCAwLTIuMjEtMS43OS00LTQtNHoiIGZpbGw9IiNmZmYiIHN0cm9rZT0iIzAwMCIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==')}
.pc.wB{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxnIGZpbGw9IiNmZmYiIHN0cm9rZS1saW5lY2FwPSJidXR0Ij48cGF0aCBkPSJNOSAzNmMzLjM5LS45NyAxMC4xMS40MyAxMy41LTIgMy4zOSAyLjQzIDEwLjExIDEuMDMgMTMuNSAyIDAgMCAxLjY1LjU0IDMgMi0uNjguOTctMS42NS45OS0zIC41LTMuMzktLjk3LTEwLjExLjQ2LTEzLjUtMS0zLjM5IDEuNDYtMTAuMTEuMDMtMTMuNSAxLTEuMzU0LjQ5LTIuMzIzLjQ3LTMtLjUgMS4zNTQtMS45NCAzLTIgMy0yeiIvPjxwYXRoIGQ9Ik0xNSAzMmMyLjUgMi41IDEyLjUgMi41IDE1IDAgLjUtMS41IDAtMiAwLTIgMC0yLjUtMi41LTQtMi41LTQgNS41LTEuNSA2LTExLjUtNS0xNS41LTExIDQtMTAuNSAxNC01IDE1LjUgMCAwLTIuNSAxLjUtMi41IDQgMCAwLS41LjUgMCAyeiIvPjxwYXRoIGQ9Ik0yNSA4YTIuNSAyLjUgMCAxIDEtNSAwIDIuNSAyLjUgMCAxIDEgNSAweiIvPjwvZz48cGF0aCBkPSJNMTcuNSAyNmgxME0xNSAzMGgxNW0tNy41LTE0LjV2NU0yMCAxOGg1IiBzdHJva2UtbGluZWpvaW49Im1pdGVyIi8+PC9nPjwvc3ZnPg==')}
.pc.wN{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0yMiAxMGMxMC41IDEgMTYuNSA4IDE2IDI5SDE1YzAtOSAxMC02LjUgOC0yMSIgZmlsbD0iI2ZmZiIvPjxwYXRoIGQ9Ik0yNCAxOGMuMzggMi45MS01LjU1IDcuMzctOCA5LTMgMi0yLjgyIDQuMzQtNSA0LTEuMDQyLS45NCAxLjQxLTMuMDQgMC0zLTEgMCAuMTkgMS4yMy0xIDItMSAwLTQuMDAzIDEtNC00IDAtMiA2LTEyIDYtMTJzMS44OS0xLjkgMi0zLjVjLS43My0uOTk0LS41LTItLjUtMyAxLTEgMyAyLjUgMyAyLjVoMnMuNzgtMS45OTIgMi41LTNjMSAwIDEgMyAxIDMiIGZpbGw9IiNmZmYiLz48cGF0aCBkPSJNOS41IDI1LjVhLjUuNSAwIDEgMS0xIDAgLjUuNSAwIDEgMSAxIDB6bTUuNDMzLTkuNzVhLjUgMS41IDMwIDEgMS0uODY2LS41LjUgMS41IDMwIDEgMSAuODY2LjV6IiBmaWxsPSIjMDAwIi8+PC9nPjwvc3ZnPg==')}
.pc.wR{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PGcgZmlsbD0iI2ZmZiIgZmlsbC1ydWxlPSJldmVub2RkIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik05IDM5aDI3di0zSDl2M3ptMy0zdi00aDIxdjRIMTJ6bS0xLTIyVjloNHYyaDVWOWg1djJoNVY5aDR2NSIgc3Ryb2tlLWxpbmVjYXA9ImJ1dHQiLz48cGF0aCBkPSJNMzQgMTRsLTMgM0gxNGwtMy0zIi8+PHBhdGggZD0iTTMxIDE3djEyLjVIMTRWMTciIHN0cm9rZS1saW5lY2FwPSJidXR0IiBzdHJva2UtbGluZWpvaW49Im1pdGVyIi8+PHBhdGggZD0iTTMxIDI5LjVsMS41IDIuNWgtMjBsMS41LTIuNSIvPjxwYXRoIGQ9Ik0xMSAxNGgyMyIgZmlsbD0ibm9uZSIgc3Ryb2tlLWxpbmVqb2luPSJtaXRlciIvPjwvZz48L3N2Zz4=')}
.pc.wQ{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PGcgZmlsbD0iI2ZmZiIgZmlsbC1ydWxlPSJldmVub2RkIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik04IDEyYTIgMiAwIDEgMS00IDAgMiAyIDAgMSAxIDQgMHptMTYuNS00LjVhMiAyIDAgMSAxLTQgMCAyIDIgMCAxIDEgNCAwek00MSAxMmEyIDIgMCAxIDEtNCAwIDIgMiAwIDEgMSA0IDB6TTE2IDguNWEyIDIgMCAxIDEtNCAwIDIgMiAwIDEgMSA0IDB6TTMzIDlhMiAyIDAgMSAxLTQgMCAyIDIgMCAxIDEgNCAweiIvPjxwYXRoIGQ9Ik05IDI2YzguNS0xLjUgMjEtMS41IDI3IDBsMi0xMi03IDExVjExbC01LjUgMTMuNS0zLTE1LTMgMTUtNS41LTE0VjI1TDcgMTRsMiAxMnoiIHN0cm9rZS1saW5lY2FwPSJidXR0Ii8+PHBhdGggZD0iTTkgMjZjMCAyIDEuNSAyIDIuNSA0IDEgMS41IDEgMSAuNSAzLjUtMS41IDEtMS41IDIuNS0xLjUgMi41LTEuNSAxLjUuNSAyLjUuNSAyLjUgNi41IDEgMTYuNSAxIDIzIDAgMCAwIDEuNS0xIDAtMi41IDAgMCAuNS0xLjUtMS0yLjUtLjUtMi41LS41LTIgLjUtMy41IDEtMiAyLjUtMiAyLjUtNC04LjUtMS41LTE4LjUtMS41LTI3IDB6IiBzdHJva2UtbGluZWNhcD0iYnV0dCIvPjxwYXRoIGQ9Ik0xMS41IDMwYzMuNS0xIDE4LjUtMSAyMiAwTTEyIDMzLjVjNi0xIDE1LTEgMjEgMCIgZmlsbD0ibm9uZSIvPjwvZz48L3N2Zz4=')}
.pc.wK{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0yMi41IDExLjYzVjZNMjAgOGg1IiBzdHJva2UtbGluZWpvaW49Im1pdGVyIi8+PHBhdGggZD0iTTIyLjUgMjVzNC41LTcuNSAzLTEwLjVjMCAwLTEtMi41LTMtMi41cy0zIDIuNS0zIDIuNWMtMS41IDMgMyAxMC41IDMgMTAuNSIgZmlsbD0iI2ZmZiIgc3Ryb2tlLWxpbmVjYXA9ImJ1dHQiIHN0cm9rZS1saW5lam9pbj0ibWl0ZXIiLz48cGF0aCBkPSJNMTEuNSAzN2M1LjUgMy41IDE1LjUgMy41IDIxIDB2LTdzOS00LjUgNi0xMC41Yy00LTYuNS0xMy41LTMuNS0xNiA0VjI3di0zLjVjLTMuNS03LjUtMTMtMTAuNS0xNi00LTMgNiA1IDEwIDUgMTBWMzd6IiBmaWxsPSIjZmZmIi8+PHBhdGggZD0iTTExLjUgMzBjNS41LTMgMTUuNS0zIDIxIDBtLTIxIDMuNWM1LjUtMyAxNS41LTMgMjEgMG0tMjEgMy41YzUuNS0zIDE1LjUtMyAyMSAwIi8+PC9nPjwvc3ZnPg==')}
.pc.bP{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PHBhdGggZD0iTTIyLjUgOWMtMi4yMSAwLTQgMS43OS00IDQgMCAuODkuMjkgMS43MS43OCAyLjM4QzE3LjMzIDE2LjUgMTYgMTguNTkgMTYgMjFjMCAyLjAzLjk0IDMuODQgMi40MSA1LjAzLTMgMS4wNi03LjQxIDUuNTUtNy40MSAxMy40N2gyM2MwLTcuOTItNC40MS0xMi40MS03LjQxLTEzLjQ3IDEuNDctMS4xOSAyLjQxLTMgMi40MS01LjAzIDAtMi40MS0xLjMzLTQuNS0zLjI4LTUuNjIuNDktLjY3Ljc4LTEuNDkuNzgtMi4zOCAwLTIuMjEtMS43OS00LTQtNHoiIHN0cm9rZT0iIzAwMCIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==')}
.pc.bB{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxnIGZpbGw9IiMwMDAiIHN0cm9rZS1saW5lY2FwPSJidXR0Ij48cGF0aCBkPSJNOSAzNmMzLjM5LS45NyAxMC4xMS40MyAxMy41LTIgMy4zOSAyLjQzIDEwLjExIDEuMDMgMTMuNSAyIDAgMCAxLjY1LjU0IDMgMi0uNjguOTctMS42NS45OS0zIC41LTMuMzktLjk3LTEwLjExLjQ2LTEzLjUtMS0zLjM5IDEuNDYtMTAuMTEuMDMtMTMuNSAxLTEuMzU0LjQ5LTIuMzIzLjQ3LTMtLjUgMS4zNTQtMS45NCAzLTIgMy0yeiIvPjxwYXRoIGQ9Ik0xNSAzMmMyLjUgMi41IDEyLjUgMi41IDE1IDAgLjUtMS41IDAtMiAwLTIgMC0yLjUtMi41LTQtMi41LTQgNS41LTEuNSA2LTExLjUtNS0xNS41LTExIDQtMTAuNSAxNC01IDE1LjUgMCAwLTIuNSAxLjUtMi41IDQgMCAwLS41LjUgMCAyeiIvPjxwYXRoIGQ9Ik0yNSA4YTIuNSAyLjUgMCAxIDEtNSAwIDIuNSAyLjUgMCAxIDEgNSAweiIvPjwvZz48cGF0aCBkPSJNMTcuNSAyNmgxME0xNSAzMGgxNW0tNy41LTE0LjV2NU0yMCAxOGg1IiBzdHJva2U9IiNlY2VjZWMiIHN0cm9rZS1saW5lam9pbj0ibWl0ZXIiLz48L2c+PC9zdmc+')}
.pc.bN{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0yMiAxMGMxMC41IDEgMTYuNSA4IDE2IDI5SDE1YzAtOSAxMC02LjUgOC0yMSIgZmlsbD0iIzAwMCIvPjxwYXRoIGQ9Ik0yNCAxOGMuMzggMi45MS01LjU1IDcuMzctOCA5LTMgMi0yLjgyIDQuMzQtNSA0LTEuMDQyLS45NCAxLjQxLTMuMDQgMC0zLTEgMCAuMTkgMS4yMy0xIDItMSAwLTQuMDAzIDEtNC00IDAtMiA2LTEyIDYtMTJzMS44OS0xLjkgMi0zLjVjLS43My0uOTk0LS41LTItLjUtMyAxLTEgMyAyLjUgMyAyLjVoMnMuNzgtMS45OTIgMi41LTNjMSAwIDEgMyAxIDMiIGZpbGw9IiMwMDAiLz48cGF0aCBkPSJNOS41IDI1LjVhLjUuNSAwIDEgMS0xIDAgLjUuNSAwIDEgMSAxIDB6bTUuNDMzLTkuNzVhLjUgMS41IDMwIDEgMS0uODY2LS41LjUgMS41IDMwIDEgMSAuODY2LjV6IiBmaWxsPSIjZWNlY2VjIiBzdHJva2U9IiNlY2VjZWMiLz48cGF0aCBkPSJNMjQuNTUgMTAuNGwtLjQ1IDEuNDUuNS4xNWMzLjE1IDEgNS42NSAyLjQ5IDcuOSA2Ljc1UzM1Ljc1IDI5LjA2IDM1LjI1IDM5bC0uMDUuNWgyLjI1bC4wNS0uNWMuNS0xMC4wNi0uODgtMTYuODUtMy4yNS0yMS4zNC0yLjM3LTQuNDktNS43OS02LjY0LTkuMTktNy4xNmwtLjUxLS4xeiIgZmlsbD0iI2VjZWNlYyIgc3Ryb2tlPSJub25lIi8+PC9nPjwvc3ZnPg==')}
.pc.bR{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PGcgZmlsbC1ydWxlPSJldmVub2RkIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik05IDM5aDI3di0zSDl2M3ptMy41LTdsMS41LTIuNWgxN2wxLjUgMi41aC0yMHptLS41IDR2LTRoMjF2NEgxMnoiIHN0cm9rZS1saW5lY2FwPSJidXR0Ii8+PHBhdGggZD0iTTE0IDI5LjV2LTEzaDE3djEzSDE0eiIgc3Ryb2tlLWxpbmVjYXA9ImJ1dHQiIHN0cm9rZS1saW5lam9pbj0ibWl0ZXIiLz48cGF0aCBkPSJNMTQgMTYuNUwxMSAxNGgyM2wtMyAyLjVIMTR6TTExIDE0VjloNHYyaDVWOWg1djJoNVY5aDR2NUgxMXoiIHN0cm9rZS1saW5lY2FwPSJidXR0Ii8+PHBhdGggZD0iTTEyIDM1LjVoMjFtLTIwLTRoMTltLTE4LTJoMTdtLTE3LTEzaDE3TTExIDE0aDIzIiBmaWxsPSJub25lIiBzdHJva2U9IiNlY2VjZWMiIHN0cm9rZS13aWR0aD0iMSIgc3Ryb2tlLWxpbmVqb2luPSJtaXRlciIvPjwvZz48L3N2Zz4=')}
.pc.bQ{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PGcgZmlsbC1ydWxlPSJldmVub2RkIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxnIHN0cm9rZT0ibm9uZSI+PGNpcmNsZSBjeD0iNiIgY3k9IjEyIiByPSIyLjc1Ii8+PGNpcmNsZSBjeD0iMTQiIGN5PSI5IiByPSIyLjc1Ii8+PGNpcmNsZSBjeD0iMjIuNSIgY3k9IjgiIHI9IjIuNzUiLz48Y2lyY2xlIGN4PSIzMSIgY3k9IjkiIHI9IjIuNzUiLz48Y2lyY2xlIGN4PSIzOSIgY3k9IjEyIiByPSIyLjc1Ii8+PC9nPjxwYXRoIGQ9Ik05IDI2YzguNS0xLjUgMjEtMS41IDI3IDBsMi41LTEyLjVMMzEgMjVsLS4zLTE0LjEtNS4yIDEzLjYtMy0xNC41LTMgMTQuNS01LjItMTMuNkwxNCAyNSA2LjUgMTMuNSA5IDI2eiIgc3Ryb2tlLWxpbmVjYXA9ImJ1dHQiLz48cGF0aCBkPSJNOSAyNmMwIDIgMS41IDIgMi41IDQgMSAxLjUgMSAxIC41IDMuNS0xLjUgMS0xLjUgMi41LTEuNSAyLjUtMS41IDEuNS41IDIuNS41IDIuNSA2LjUgMSAxNi41IDEgMjMgMCAwIDAgMS41LTEgMC0yLjUgMCAwIC41LTEuNS0xLTIuNS0uNS0yLjUtLjUtMiAuNS0zLjUgMS0yIDIuNS0yIDIuNS00LTguNS0xLjUtMTguNS0xLjUtMjcgMHoiIHN0cm9rZS1saW5lY2FwPSJidXR0Ii8+PHBhdGggZD0iTTExIDM4LjVhMzUgMzUgMSAwIDAgMjMgMCIgZmlsbD0ibm9uZSIgc3Ryb2tlLWxpbmVjYXA9ImJ1dHQiLz48cGF0aCBkPSJNMTEgMjlhMzUgMzUgMSAwIDEgMjMgMG0tMjEuNSAyLjVoMjBtLTIxIDNhMzUgMzUgMSAwIDAgMjIgMG0tMjMgM2EzNSAzNSAxIDAgMCAyNCAwIiBmaWxsPSJub25lIiBzdHJva2U9IiNlY2VjZWMiLz48L2c+PC9zdmc+')}
.pc.bK{background-image:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0NSIgaGVpZ2h0PSI0NSI+PGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0yMi41IDExLjYzVjYiIHN0cm9rZS1saW5lam9pbj0ibWl0ZXIiLz48cGF0aCBkPSJNMjIuNSAyNXM0LjUtNy41IDMtMTAuNWMwIDAtMS0yLjUtMy0yLjVzLTMgMi41LTMgMi41Yy0xLjUgMyAzIDEwLjUgMyAxMC41IiBmaWxsPSIjMDAwIiBzdHJva2UtbGluZWNhcD0iYnV0dCIgc3Ryb2tlLWxpbmVqb2luPSJtaXRlciIvPjxwYXRoIGQ9Ik0xMS41IDM3YzUuNSAzLjUgMTUuNSAzLjUgMjEgMHYtN3M5LTQuNSA2LTEwLjVjLTQtNi41LTEzLjUtMy41LTE2IDRWMjd2LTMuNWMtMy41LTcuNS0xMy0xMC41LTE2LTQtMyA2IDUgMTAgNSAxMFYzN3oiIGZpbGw9IiMwMDAiLz48cGF0aCBkPSJNMjAgOGg1IiBzdHJva2UtbGluZWpvaW49Im1pdGVyIi8+PHBhdGggZD0iTTMyIDI5LjVzOC41LTQgNi4wMy05LjY1QzM0LjE1IDE0IDI1IDE4IDIyLjUgMjQuNWwuMDEgMi4xLS4wMS0yLjFDMjAgMTggOS45MDYgMTQgNi45OTcgMTkuODVjLTIuNDk3IDUuNjUgNC44NTMgOSA0Ljg1MyA5IiBzdHJva2U9IiNlY2VjZWMiLz48cGF0aCBkPSJNMTEuNSAzMGM1LjUtMyAxNS41LTMgMjEgMG0tMjEgMy41YzUuNS0zIDE1LjUtMyAyMSAwbS0yMSAzLjVjNS41LTMgMTUuNS0zIDIxIDAiIHN0cm9rZT0iI2VjZWNlYyIvPjwvZz48L3N2Zz4=')}
</style>
<script>try{if(window.self!==window.top)document.documentElement.classList.add('embed')}catch(e){document.documentElement.classList.add('embed')}</script>
</head>
<body>
<div class="top">
  <span class="t"><!-- PAGE_TITLE --></span>
  <button id="fminus" title="Smaller text">A−</button>
  <button id="fplus" title="Larger text">A+</button>
  <button id="dark" title="Dark mode">Dark</button>
  <button id="dlHtml" title="Download HTML">⬇ HTML</button>
  <button id="dlPrint" title="Print / Save PDF">🖨 PDF</button>
  <button id="bTog" class="tog" title="Show or hide the board">Hide board</button>
</div>
<div class="wrap">
  <nav class="toc">
    <div class="h">Games</div>
<!-- SIDEBAR_LINKS -->
  </nav>
  <main id="content">
  </main>
  <aside class="bp">
    <div class="bhead"><span id="who"></span></div>
    <div id="live"><div class="bwrap"><div class="rk" id="rk"></div><div class="bd" id="bd"></div><div class="fl" id="fl"></div></div></div>
    <div class="ctrls">
      <button id="bStart" title="Start">⏮</button>
      <button id="bPrev" title="Back">◀</button>
      <button id="bNext" title="Forward">▶</button>
      <button id="bEnd" title="End">⏭</button>
      <button id="bFlip" title="Flip board">⇅</button>
    </div>
    <div class="msg" id="status"></div>
  </aside>
</div>

<script>
''' + r'''CHESS_JS_PLACEHOLDER''' + r'''

/* ── Game database ── */
<!-- GAMES_ARRAY -->

/* ── Parse game ── */
const PIECE_MAP = {p:'bP',r:'bR',n:'bN',b:'bB',q:'bQ',k:'bK',P:'wP',R:'wR',N:'wN',B:'wB',Q:'wQ',K:'wK'};
let positions = [];
let totalPly = 0;
let curPly = 0;
let flipped = false;
let curGameIdx = 0;

function parseGame(g) {
  const chess = new Chess();
  positions = [{fen: chess.fen(), san: null, from: null, to: null, ply: 0}];
  const sans = g.pgn.replace(/\s*(1-0|0-1|1\/2-1\/2|\*)\s*$/, '')
    .replace(/\d+\.\s*/g, ' ').trim().split(/\s+/)
    .filter(s => s.length > 0 && !s.match(/^\d+\.?$/));
  sans.forEach((san, i) => {
    const m = chess.move(san);
    if (m) positions.push({fen: chess.fen(), san: m.san, from: m.from, to: m.to, ply: i + 1});
  });
  totalPly = positions.length - 1;
  curPly = 0;
}

/* ── Board rendering ── */
function fenToBoard(fen) {
  const rows = fen.split(' ')[0].split('/');
  const board = [];
  for (const row of rows) {
    const r = [];
    for (const ch of row) {
      if (ch >= '1' && ch <= '8') for (let j = 0; j < +ch; j++) r.push(null);
      else r.push(ch);
    }
    board.push(r);
  }
  return board;
}

function boardHTML(fen, lastFrom, lastTo) {
  const board = fenToBoard(fen);
  let html = '';
  const ranks = flipped ? [7,6,5,4,3,2,1,0] : [0,1,2,3,4,5,6,7];
  const files = flipped ? [7,6,5,4,3,2,1,0] : [0,1,2,3,4,5,6,7];
  for (const r of ranks) {
    for (const f of files) {
      const isLight = (r + f) % 2 === 0;
      const sq = 'abcdefgh'[f] + (8 - r);
      let cls = 'sq ' + (isLight ? 'l' : 'd');
      let circHTML = '';
      if (lastFrom === sq) { cls += ' lm lm-from'; circHTML = '<div class="circ"></div>'; }
      else if (lastTo === sq) { cls += ' lm lm-to'; circHTML = '<div class="circ"></div>'; }
      const piece = board[r][f];
      const pcHTML = piece ? '<div class="pc ' + PIECE_MAP[piece] + '"></div>' : '';
      html += '<div class="' + cls + '">' + pcHTML + circHTML + '</div>';
    }
  }
  return html;
}

function miniBoardHTML(fen) {
  const board = fenToBoard(fen);
  let html = '';
  for (let r = 0; r < 8; r++) {
    for (let f = 0; f < 8; f++) {
      const isLight = (r + f) % 2 === 0;
      const piece = board[r][f];
      const pcHTML = piece ? '<div class="pc ' + PIECE_MAP[piece] + '"></div>' : '';
      html += '<div class="sq ' + (isLight ? 'l' : 'd') + '">' + pcHTML + '</div>';
    }
  }
  return html;
}

function updateCoords() {
  const rkEl = document.getElementById('rk');
  const flEl = document.getElementById('fl');
  const ranks = flipped ? ['1','2','3','4','5','6','7','8'] : ['8','7','6','5','4','3','2','1'];
  const files = flipped ? 'hgfedcba' : 'abcdefgh';
  rkEl.innerHTML = ranks.map(r => '<span>' + r + '</span>').join('');
  flEl.innerHTML = files.split('').map(f => '<span>' + f + '</span>').join('');
}

function moveLabel(ply, san) {
  const n = Math.ceil(ply / 2);
  return ply % 2 === 1 ? n + '.' + san : n + '...' + san;
}

/* ── Navigate ── */
function goTo(ply) {
  ply = Math.max(0, Math.min(totalPly, ply));
  curPly = ply;
  const pos = positions[ply];
  document.getElementById('bd').innerHTML = boardHTML(pos.fen, pos.from, pos.to);

  const whoEl = document.getElementById('who');
  const g = GAMES[curGameIdx];
  if (ply === 0) whoEl.innerHTML = '<b>' + g.white + '</b> vs <b>' + g.black + '</b>';
  else {
    const turn = ply % 2 === 1 ? g.white : g.black;
    whoEl.innerHTML = '<b>' + turn + '</b> played ' + moveLabel(ply, pos.san);
  }

  document.getElementById('status').textContent = ply === totalPly ? 'Game over – ' + g.result : '';

  document.querySelectorAll('a.mv').forEach(a => {
    a.classList.toggle('cur', +a.dataset.ply === ply);
  });
  document.querySelectorAll('.tree-cell').forEach(c => {
    c.classList.toggle('on', +c.dataset.ply === ply);
  });

  const curMv = document.querySelector('a.mv.cur');
  if (curMv) curMv.scrollIntoView({block: 'nearest', behavior: 'smooth'});
}

/* ── Render game into main content ── */
function renderGame(g) {
  parseGame(g);
  const el = document.getElementById('content');
  let html = '';

  // header
  html += '<div class="kicker">' + g.eco + ' ' + g.opening + '</div>';
  html += '<h1>' + g.white + ' vs ' + g.black + '</h1>';
  html += '<p class="gamehead">' + g.event + ', ' + g.date + ' &middot; Result: <b>' + g.result + '</b></p>';

  // PGN moves
  html += '<p class="ml">';
  for (let i = 1; i <= totalPly; i++) {
    const pos = positions[i];
    if (i % 2 === 1) html += '<b>' + Math.ceil(i/2) + '.</b>';
    html += '<a class="mv" data-ply="' + i + '" onclick="goTo(' + i + ')">' + pos.san + '</a> ';
  }
  html += '<b>' + g.result + '</b></p>';

  // opening tree
  html += '<h2>Opening Tree</h2>';
  html += '<p style="font-size:.85em;color:var(--muted)">Click any position to jump there on the board.</p>';
  html += '<div class="tree-grid" id="tree">';
  for (let i = 0; i <= totalPly; i++) {
    const pos = positions[i];
    const label = i === 0 ? 'Start' : moveLabel(i, pos.san);
    html += '<div class="tree-cell' + (i === 0 ? ' on' : '') + '" data-ply="' + i + '" onclick="goTo(' + i + ')">';
    html += '<div class="mini-bd">' + miniBoardHTML(pos.fen) + '</div>';
    html += '<div class="label">' + label + '</div>';
    html += '</div>';
  }
  html += '</div>';

  el.innerHTML = html;
}

/* ── Controls ── */
document.getElementById('bStart').onclick = function() { goTo(0); };
document.getElementById('bPrev').onclick = function() { goTo(curPly - 1); };
document.getElementById('bNext').onclick = function() { goTo(curPly + 1); };
document.getElementById('bEnd').onclick = function() { goTo(totalPly); };
document.getElementById('bFlip').onclick = function() { flipped = !flipped; updateCoords(); goTo(curPly); rebuildTree(); };

function rebuildTree() {
  var tree = document.getElementById('tree');
  if (!tree) return;
  var html = '';
  for (var i = 0; i <= totalPly; i++) {
    var pos = positions[i];
    var label = i === 0 ? 'Start' : moveLabel(i, pos.san);
    html += '<div class="tree-cell' + (i === curPly ? ' on' : '') + '" data-ply="' + i + '" onclick="goTo(' + i + ')">';
    html += '<div class="mini-bd">' + miniBoardHTML(pos.fen) + '</div>';
    html += '<div class="label">' + label + '</div>';
    html += '</div>';
  }
  tree.innerHTML = html;
}

/* keyboard */
document.addEventListener('keydown', function(e) {
  if (e.key === 'ArrowLeft') { e.preventDefault(); goTo(curPly - 1); }
  else if (e.key === 'ArrowRight') { e.preventDefault(); goTo(curPly + 1); }
  else if (e.key === 'Home') { e.preventDefault(); goTo(0); }
  else if (e.key === 'End') { e.preventDefault(); goTo(totalPly); }
  else if (e.key === 'f' || e.key === 'F') { flipped = !flipped; updateCoords(); goTo(curPly); rebuildTree(); }
});

/* dark mode */
document.getElementById('dark').onclick = function() {
  var root = document.documentElement;
  var isDark = root.getAttribute('data-theme') === 'dark';
  root.setAttribute('data-theme', isDark ? '' : 'dark');
  this.textContent = isDark ? 'Dark' : 'Light';
};

/* text size */
var fs = 21;
document.getElementById('fplus').onclick = function() { fs = Math.min(32, fs + 2); document.documentElement.style.setProperty('--fs', fs + 'px'); };
document.getElementById('fminus').onclick = function() { fs = Math.max(14, fs - 2); document.documentElement.style.setProperty('--fs', fs + 'px'); };

/* board toggle (mobile) */
document.getElementById('bTog').onclick = function() {
  document.body.classList.toggle('hideb');
  this.textContent = document.body.classList.contains('hideb') ? 'Show board' : 'Hide board';
};

/* ── Load a game by index ── */
function loadGame(idx) {
  curGameIdx = idx;
  flipped = false;
  updateCoords();
  renderGame(GAMES[idx]);
  goTo(0);
  // update sidebar highlight
  document.querySelectorAll('nav.toc a').forEach(a => {
    a.classList.toggle('on', +a.dataset.g === idx);
  });
}

/* ── Download HTML ── */
document.getElementById('dlHtml').onclick = function() {
  var html = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
  var blob = new Blob([html], {type: 'text/html'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  var g = GAMES[curGameIdx];
  a.download = (g.white + ' vs ' + g.black).replace(/[^a-zA-Z0-9 ]/g,'').replace(/ +/g,'_') + '.html';
  a.click();
  URL.revokeObjectURL(a.href);
};

/* ── Print / PDF ── */
document.getElementById('dlPrint').onclick = function() {
  window.print();
};

/* ── Init ── */
updateCoords();
renderGame(GAMES[0]);
goTo(0);
</script>
</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser(
        description='Generate a Game Viewer HTML from PGN files.',
        epilog='Examples:\n'
               '  python build_viewer.py morphy.pgn\n'
               '  python build_viewer.py *.pgn -o famous_games.html\n'
               '  python build_viewer.py games/ -o collection.html -t "My Games"',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('inputs', nargs='+', help='PGN files or directories containing PGN files')
    parser.add_argument('-o', '--output', default='game_viewer.html', help='Output HTML filename (default: game_viewer.html)')
    parser.add_argument('-t', '--title', default='Game Viewer', help='Page title (default: Game Viewer)')

    args = parser.parse_args()

    # Collect all PGN files
    pgn_files = []
    for inp in args.inputs:
        if os.path.isdir(inp):
            for f in sorted(os.listdir(inp)):
                if f.lower().endswith('.pgn'):
                    pgn_files.append(os.path.join(inp, f))
        elif os.path.isfile(inp):
            pgn_files.append(inp)
        else:
            print(f'Warning: {inp} not found, skipping.', file=sys.stderr)

    if not pgn_files:
        print('Error: No PGN files found.', file=sys.stderr)
        sys.exit(1)

    # Parse all games
    all_games = []
    for pf in pgn_files:
        try:
            games = parse_pgn_file(pf)
            all_games.extend(games)
            print(f'  Parsed {len(games)} game(s) from {pf}')
        except Exception as e:
            print(f'  Warning: Error reading {pf}: {e}', file=sys.stderr)

    if not all_games:
        print('Error: No valid games found in the PGN files.', file=sys.stderr)
        sys.exit(1)

    print(f'\nTotal: {len(all_games)} games')

    # Read the chess.js library from the existing index.html
    # (it's embedded between the <script> tag and the GAMES array)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(script_dir, 'index.html')

    chess_js = ''
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Extract chess.js: between first <script> and "/* ── Game database ── */"
        start = content.find('<script>') + len('<script>')
        # skip the embed detection script
        start = content.find('<script>', start) + len('<script>')
        end = content.find('/* ── Game database ── */')
        if start > 0 and end > 0:
            chess_js = content[start:end].strip()

    if not chess_js:
        print('Warning: Could not find chess.js in index.html. Looking for tools/chess.js...',
              file=sys.stderr)
        # Fallback: try tools/chess.js from the what_ya_playing repo
        alt_paths = [
            os.path.join(script_dir, 'chess.js'),
            os.path.expanduser('~/datwins/what_ya_playing/tools/chess.js'),
        ]
        for ap in alt_paths:
            if os.path.exists(ap):
                with open(ap, 'r', encoding='utf-8') as f:
                    chess_js = f.read()
                break

    if not chess_js:
        print('Error: Could not find chess.js library.', file=sys.stderr)
        sys.exit(1)

    # Build HTML
    html = build_html(all_games, args.title)
    html = html.replace('CHESS_JS_PLACEHOLDER', chess_js)

    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'Written: {args.output} ({os.path.getsize(args.output):,} bytes)')
    print(f'Open {args.output} in a browser to view.')


if __name__ == '__main__':
    main()
