<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: LicenseRef-Wheelly-Brand
-->

# Brand assets

The logo and its variants live here, and **this folder is the one exception to
the licensing of this repository**: everything in it is
`LicenseRef-Wheelly-Brand`, all rights reserved, not the open licence that
applies to the directory it sits in. The terms are in
[`../LICENSES/LicenseRef-Wheelly-Brand.txt`](../LICENSES/LicenseRef-Wheelly-Brand.txt),
and what you may do with the *name* is in [`../TRADEMARK.md`](../TRADEMARK.md).

The exception is wired into the tooling: `tools/spdx_headers.py` stamps this
folder with the brand identifier instead of CC-BY-4.0. Without that, the script
would quietly licence the logo under a licence that lets anyone use it — which
is the opposite of the point.

## What is in here

| | |
|---|---|
| `svg/` | the masters. All type is outlined, so no font is needed to render them |
| `png/` | the same, rasterised at 3x on a transparent background |
| `Wheelly-Brand-Guide.html`, `wheelly-brand-guide.pdf` | the four-page brand guide |
| `logo-package.txt` | the note that came with the package |

Eight files, four pairs: **horizontal** lockup (symbol and wordmark side by
side, the primary one), **vertical** lockup, **mark** on its own (avatar,
favicon, app icon) and **mark in one colour** — each with a *reversed* version
for dark backgrounds.

## The rules that matter when using it

- **The wordmark is never used on its own.** Always with the symbol.
- **Clear space** around the logo is the diameter of the eye.
- **Minimum sizes**: horizontal lockup 120 px wide, vertical 90 px, symbol
  alone 64 px.
- **Colours**: Ink `#16191D` for linework and type, Amber `#EFA00B` for the eye
  and for accents only, Paper `#F7F6F3` for light backgrounds. The assembly
  guide is built on these three, which is why its accent is amber and not the
  teal it used before the logo existed.
- **Amber is not a text colour.** On a light background it sits at about 2.1:1
  of contrast, which is unreadable; where a word has to be read in the brand
  accent the site uses a darkened amber instead.
- **Typeface**: Fredoka SemiBold 600 for the wordmark — already outlined in
  these files — and the live font for headings.

## Where it is used

The assembly guide uses the logo in its sidebar and on its front page, and the
symbol as the favicon. Those copies are **generated**: `src/guide/site.py`
copies the files it needs from here into `docs/assembly/brand/`, because GitHub
Pages publishes only `docs/`. Change the logo here and it changes there at the
next build — do not edit the copies.
