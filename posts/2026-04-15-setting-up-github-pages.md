---
title: Setting Up GitHub Pages as a Constellation
date: 2026-04-15
tags: dev, github
---

Today I set up my GitHub Pages as an interactive point-cloud constellation. Each project is a glowing node — click it, the camera zooms in, and you land on the project page.

The main page is just one HTML file with a canvas. No frameworks, no build step. Projects are configured in a simple array:

```js
const PROJECTS = [
  { name: 'Blog', url: '...', hue: 50 },
  // add more nodes here
];
```

The sub-projects (like this blog) live in their own repos and get served at `username.github.io/repo-name` automatically.

## Things I like about this setup

- **Zero maintenance** — push markdown, everything else is automated
- **Each project is independent** — its own repo, its own deploy pipeline
- **The main page is fun** — not another cookie-cutter portfolio template
