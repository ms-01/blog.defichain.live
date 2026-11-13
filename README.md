# DeFiChain Blog Archive

Independent preservation of historical DeFiChain Blog content.

**Website:** https://blog.defichain.live

## Overview

This repository preserves historical articles originally published
on the DeFiChain Blog.

The archive provides continued access to community announcements,
development updates, technical discussions, security-related
information, and other historical ecosystem content.

The project is an independent community preservation initiative.
It is not an official continuation of the original blog.

## Archive Contents

The initial archive contains:

- 213 historical articles
- 451 locally preserved media files
- Articles covering the years 2020–2026
- Editorial categories: News, Security, Technology, Development
- Static HTML pages with local navigation
- A Python-based archive generator

Historical content is retained for documentation and reference.
Older articles may contain outdated information or external links.

## Repository Structure

- `all-posts.json` — archived article source data
- `article-categories.json` — editorial classifications
- `media-manifest.json` — mapping of preserved media
- `build-offline.py` — static website generator
- `offline/` — generated website published by Netlify
- `netlify.toml` — deployment configuration

The original working files and local backups are excluded from Git.

## Hosting and Deployment

The archive is hosted as a static website using Netlify.

- Domain: https://blog.defichain.live
- Repository: https://github.com/ms-01/blog.defichain.live
- Production branch: `main`
- Publish directory: `offline`

The generated website is committed to GitHub.
Netlify publishes the static files without requiring a Python build.

## Updating the Archive

To regenerate the website locally, run:

    python3 build-offline.py

Review the generated HTML, navigation, and media references
before committing changes.

Changes pushed to the production branch can trigger
a new Netlify deployment once the project is connected.

## Community Contributions

Community contributions are welcome.

Please use GitHub Issues to:

- Report missing or broken archived content
- Identify incorrect article metadata
- Suggest improvements to navigation or accessibility
- Report broken media references
- Propose corrections to editorial categories

Pull requests may be submitted for technical improvements
and corrections.

Historical articles should not be silently rewritten.
Substantive corrections should be documented transparently.

New community articles should be clearly distinguished
from preserved historical content.

## Preservation Principles

The archive follows these principles:

1. Preserve historical context.
2. Maintain traceability to original publications where possible.
3. Distinguish archived material from current information.
4. Document corrections and editorial changes.
5. Keep the archive accessible independently of the original hosting.

## Copyright and Attribution

Original articles, images, logos, and other materials may remain
subject to third-party copyright, trademark, and licensing rights.

Archiving content does not transfer ownership or grant permission
for unrestricted reuse.

Rights holders may open a GitHub Issue to report attribution
concerns or request a review of specific archived materials.

No general license for third-party archived content is implied.

## Disclaimer

This is an independent historical archive and is not an official
DeFiChain communication channel.

Archived articles reflect the information and opinions available
at their original publication dates. They do not necessarily
represent the current technical, financial, or organizational
state of the DeFiChain ecosystem.
