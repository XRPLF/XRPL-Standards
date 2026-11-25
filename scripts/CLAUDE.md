# Site generator

`build_site.py` renders the XLS specs into a static site in `scripts/_site/`, which `.github/workflows/deploy.yml` uploads to GitHub Pages. `xls_parser.py` reads spec preambles for the site and for CI validation.

## Rules

- **Output is plain static HTML.** Jinja templates in `templates/`, one stylesheet in `assets/style.css`. No framework, bundler, package manager, or JS build step. Deploying is "run `build_site.py`, upload `_site/`".
- **Prefer CSS over JS.** Use JS only for what CSS cannot do (today: table sorting, the filter box, KaTeX). Keep all of it in `assets/site.js`. Every page must still work with JS off: content, links, and the table of contents stay usable.
- **Links are relative.** Templates build every internal URL from `root` (the path from the current page to the site root). `LinkResolver` rewrites relative links and images in Markdown: a link to a rendered `.md` goes to its page, other repo files are copied into the site, and anything else goes to GitHub. Do not hard-code `/XRPL-Standards` or write site paths by hand in Markdown. Only redirect pages use `GITHUB_PAGES_BASE_URL`.
- **Templates autoescape.** Mark rendered Markdown with `|safe`; nothing else.
- **Keep Jinja out of HTML tags.** The prettier pre-commit hook formats `templates/*.html` as HTML. It splits Jinja tags inside a tag (`<th {% if x %}...{% endif %}>`) into broken syntax, and it adds whitespace around inline markup. Use `{{ ... }}` expressions in attribute values (`class="{{ 'a' if x }}"`), not `{% %}` blocks, and build inline lists such as author links in Python. Run `pre-commit run --files scripts/templates/*.html` and rebuild after it.
- **Accessibility basics stay.** Keyboard-operable controls (`<button>`, `<details>`), visible focus, `aria-sort` on sorted columns, and the skip link.
- **Keep the parser shared.** `validate_xls_template.py` and `.github/scripts/close-xls-discussions.py` import `xls_parser.py`. Do not change `XLSDocument` fields or `extract_xls_metadata` behavior without checking them.

## Amendment patches

Nested patches (XLS-1 §4.4.4) live at `XLS-NNNN-slug/x.y-amendment-slug/*.md`. `xls_parser.find_patches` attaches them to their parent as `doc.patches`, in numeric order (`65.1.2` before `65.1.10`).

- A patch page mirrors its source path: `xls/XLS-0065-…/65.1-lending-protocol-v1_1/65.1.2-….html`; `README.md` in an amendment folder becomes `index.html`. `xls/xls-65.1.2.html` redirects to it.
- Patches are not rows in the listing. The parent's row links to the "Amendment patches" panel on the parent page.
- `patch_map.py` decides which parent section a patch section changes. It uses only what the patch states: a `../README.md#anchor` link, a `parent §N.N` reference, or the same heading-title path below Specification. Do not add body-text guessing. A wrong marker misleads readers more than a missing one. `validate_xls_template.py` uses the same module: broken parent anchors and `§` references are errors, and Specification sections that match no parent section are warnings.
- The amendment name comes from the patch's prose ("Under the `fixCleanup3_4_0` amendment"), or from its `x.y/README.md` index.
- The amendment filter on parent pages is radio buttons and CSS `:has()`; keep it script-free.

## Check a change

```bash
python scripts/build_site.py
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/xls_parser.py
```

Then serve `scripts/_site` (`python -m http.server -d scripts/_site`) and open the pages you changed at desktop and phone widths. For UI changes, put before/after screenshots in the PR description.
