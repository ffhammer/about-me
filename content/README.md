# How to edit the site

Each file here is one page: `index.md` → `/`, `work_at_form.md` → `/work_at_form/`.
A new file `foo.md` becomes `/foo/`. This README is not built.

Run the dev daemon once (`./dev.sh start`), then just edit and save. Browser + phone reload by themselves.

## Sections
Every `## ...` starts a new block on the page. Reorder them by moving them.

| Heading | Looks like |
|---|---|
| `## hero` | big video + title on top |
| `## 01 Some title` | chapter: amber number + heading |
| `## Some Title` | normal heading |
| `## intro` (one lowercase word) | block without a visible heading |

## Lines inside a section
| Write | You get |
|---|---|
| plain text | paragraph (blank line = new paragraph) |
| `**bold**`, `*italic*`, `[text](url)` | as usual |
| `# Title` | big page title |
| `- item` | bullet list |
| `label: ETH Zürich · 2026` | small amber caps line |
| `lead: text` | bigger intro paragraph |
| `muted: text` / `note: text` | grey text / small grey text |
| `photo: me.jpg` | round photo (next to the paragraph right after it) |
| `image: file.jpg \| caption` | image with caption (files in `site/assets/media/`) |
| `video: hero` + `poster: hero.jpg` | hero video (only in `## hero`) |
| `number: 48367341` | big counting number |
| `stat: 5.2× \| fewer GPU-hours` | stat box (lines next to each other form a grid) |
| `compare: a.mp4 = Left \| b.mp4 = Right \| caption` | drag slider between two videos |
| `chips: [A](url) · [B](url)` | small link pills |
| `button: Text \| url` | button (first is filled, next ones outlined) |
| `paper: status \| title \| authors` | paper entry |
| `details: Title` … `/details` | tap-to-open box (tables work inside) |
| markdown table, a `**bold**` cell | table, bold row gets highlighted |
| `%% comment` | ignored |

## Rules
Nothing private on the site: no phone, address, grades or unpublished results.
