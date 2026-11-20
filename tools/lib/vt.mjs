// A small interpreter for the control sequences that a terminal build may use (TRM-12).
// It rebuilds the character grid from the bytes that the build wrote to its terminal.

export function createScreen(cols, rows) {
  const blank = () => Array.from({ length: rows }, () => Array(cols).fill(" "));
  const s = { cols, rows, grid: blank(), row: 0, col: 0, cursorShown: true, unknown: [] };
  let pending = "";

  const put = (ch) => {
    if (s.col >= cols) {
      s.col = 0;
      s.row = Math.min(rows - 1, s.row + 1);
    }
    s.grid[s.row][s.col] = ch;
    s.col += 1;
  };

  /** Feed text that the build wrote. A sequence that is cut at the end waits for the next call. */
  s.write = (text) => {
    const data = pending + text;
    pending = "";
    let i = 0;
    while (i < data.length) {
      const ch = data[i];
      if (ch === "\x1b") {
        const m = data[i + 1] === "[" ? /^([?0-9;]*)([A-Za-z~])/.exec(data.slice(i + 2, i + 32)) : null;
        if (!m) {
          const cut = data.length - i < 32 && (data[i + 1] === undefined || data[i + 1] === "[");
          if (cut) {
            pending = data.slice(i);
            return;
          }
          s.unknown.push(JSON.stringify(data.slice(i, i + 6)));
          i += 1;
          continue;
        }
        const [tail, args, op] = m;
        const all = `\x1b[${tail}`;
        const n = args.split(";").map((x) => Number(x) || 0);
        if (op === "H") {
          s.row = Math.min(rows - 1, Math.max(0, (n[0] || 1) - 1));
          s.col = Math.min(cols - 1, Math.max(0, (n[1] || 1) - 1));
        } else if (op === "J" && args === "2") s.grid = blank();
        else if (op === "K" && (args === "" || args === "0")) {
          for (let c = s.col; c < cols; c++) s.grid[s.row][c] = " ";
        } else if (op === "m") { /* attributes do not change the characters */ }
        else if (args === "?25" && (op === "h" || op === "l")) s.cursorShown = op === "h";
        else if (args === "?1049" && (op === "h" || op === "l")) { /* the alternate screen */ }
        else s.unknown.push(JSON.stringify(all));
        i += all.length;
      } else if (ch === "\r") {
        s.col = 0;
        i += 1;
      } else if (ch === "\n") {
        s.row = Math.min(rows - 1, s.row + 1);
        i += 1;
      } else if (ch < " ") {
        s.unknown.push(JSON.stringify(ch));
        i += 1;
      } else {
        const cp = data.codePointAt(i);
        const str = String.fromCodePoint(cp);
        put(str);
        i += str.length;
      }
    }
  };
  s.line = (r) => s.grid[r].join("");
  s.text = () => s.grid.map((r) => r.join("").trimEnd()).join("\n");
  /** The characters inside rect [row, column, height, width], counted from 1, as lines. */
  s.rect = ([row, col, h, w]) => {
    const out = [];
    for (let r = row - 1; r < row - 1 + h && r < rows; r++) out.push(s.grid[r].slice(col - 1, col - 1 + w).join(""));
    return out;
  };
  return s;
}
