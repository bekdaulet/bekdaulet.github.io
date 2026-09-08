# bekdaulet.github.io

Personal academic website of Bekdaulet Shukirgaliyev. Static HTML and CSS, hosted on GitHub Pages. No build step.

## Files

| File | What it is |
|------|------------|
| `index.html` | English page (https://bekdaulet.github.io/) |
| `kk/index.html` | Kazakh page (https://bekdaulet.github.io/kk/) |
| `ru/index.html` | Russian page (https://bekdaulet.github.io/ru/) |
| `style.css` | Shared styles, colors, fonts, layout |
| `assets/photo.jpg` | Portrait shown in the header |
| `assets/Shukirgaliyev_CV.pdf` | CV linked from the "Download CV" button |

## Editing text

Each page is one HTML file with the same section order. Search for the section id, then edit the text between the tags:

| Section | Look for |
|---------|----------|
| Name, tagline, intro paragraph | `<section class="hero">` |
| Research topics (six cards) | `<section id="research">` |
| Publications list | `<section id="publications">`, one `<li>` per paper |
| Positions, education, awards | `<section id="experience">`, one `<li>` per row |
| Teaching | `<section id="teaching">`, one card per university |
| Address, emails, profile links | `<section id="contact">` |

To add a publication, copy an existing `<li>...</li>` block inside `<ol class="pubs">` and change the title, DOI link, authors, journal, and year. The numbering is automatic.

The three language pages are independent. A change made in `index.html` must be repeated in `kk/index.html` and `ru/index.html` if it should appear in all languages.

## Replacing the CV or photo

Overwrite `assets/Shukirgaliyev_CV.pdf` or `assets/photo.jpg` with the new file, keeping the same name. Keep the photo under about 1000 px on the long side.

## Publishing changes

```
git add -A
git commit -m "Describe the change"
git push
```

GitHub Pages rebuilds the site within about a minute of each push.

## Local preview

```
python3 -m http.server 8765
```

Then open http://localhost:8765 in a browser.
