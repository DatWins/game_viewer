# Game Viewer

A self-contained chess game viewer hosted on GitHub Pages at `datwins.github.io/game_viewer`.

## Architecture

**Single-file HTML** — `index.html` contains everything inline:
- CSS (layout, theming, responsive breakpoints, print styles)
- chess.js library (BSD, Jeff Hlywa) for move parsing
- Base64-encoded SVG piece sprites (12 pieces: wP/wN/wB/wR/wQ/wK/bP/bN/bB/bR/bQ/bK)
- Application JS (game parsing, board rendering, navigation, downloads)

**No external dependencies.** The page works offline.

## Layout

Matches the noteschess 3-column layout exactly:
- **Left sidebar** (`nav.toc`): Game listing — click to switch games
- **Center** (`main`): PGN header + clickable moves + opening tree (mini-board grid, 6 per row)
- **Right panel** (`aside.bp`): Sticky interactive board with ⏮◀▶⏭⇅ controls

Responsive breakpoints:
- `≤1100px`: Single column, board stacks on top, sidebar hidden
- `≤480px`: Compact phone layout
- Landscape + short viewport: Side-by-side board + controls

## Key Components

### GAMES Array (line ~1944)
Each game is an object:
```js
{
  white: 'Player Name',
  black: 'Opponent Name',
  event: 'City/Tournament', date: '1858',
  eco: 'C41', opening: 'Opening Name',
  result: '1-0',
  pgn: '1.e4 e5 2.Nf3 d6 ...'
}
```

### Adding a New Game
1. Add an entry to the `GAMES` array
2. Add a sidebar link in the `<nav class="toc">` section:
   ```html
   <a data-g="N" onclick="loadGame(N)">White – Black</a>
   ```
   where N is the 0-based index matching the array position

### Core Functions
- `parseGame(g)` — Uses chess.js to walk the PGN, builds `positions[]` array with FEN/SAN/from/to for each ply
- `boardHTML(fen, from, to)` — Renders 8×8 grid with pieces, last-move highlight (green background + circles)
- `miniBoardHTML(fen)` — Smaller version for the opening tree grid
- `goTo(ply)` — Navigates to a position, updates board + move highlighting + tree highlighting
- `loadGame(idx)` — Switches to a different game, resets board
- `renderGame(g)` — Builds the center content: header, PGN moves, opening tree

### Board Rendering
- CSS Grid: 8×8 grid of `.sq` divs (`.l` light / `.d` dark)
- Pieces: `.pc` div with base64 SVG background image (class like `.pc.wN`)
- Last move: `.sq.lm` gets green background, `.lm-from` gets small circle, `.lm-to` gets larger circle
- Coordinates: `.rk` (rank labels) and `.fl` (file labels) beside the board
- Board size: `--bw:min(44vw, calc(100vh - 290px), 680px)`

### Features
- **Dark mode**: `data-theme="dark"` on `<html>`, toggled by Dark button
- **Text size**: A−/A+ buttons adjust `--fs` CSS variable (14–32px)
- **Keyboard**: ←→ arrows, Home/End, F to flip
- **Download HTML**: Saves the entire page as a standalone .html file
- **Print/PDF**: Opens print dialog with clean styles (hides chrome)
- **Board flip**: ⇅ button reverses rank/file order

### CSS Variables (Theming)
```
--paper  --ink  --muted  --line  --side    (backgrounds/text)
--main  --var  --hl  --hlink              (accents/highlights)
--light  --dark  --lm  --sel              (board squares)
--btn  --btnb                              (buttons)
```

## Repo
- GitHub: `DatWins/game_viewer`
- Pages URL: `datwins.github.io/game_viewer`
- Branch: `main`
- Single file: `index.html`
