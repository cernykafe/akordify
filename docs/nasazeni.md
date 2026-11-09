# Nasazení a provoz

Akordify je statický web. Stačí servírovat obsah složky [`public/`](../public) jako kořen webu. Server nic nepočítá, nepotřebuje databázi ani proměnné prostředí.

- [Cloudflare Pages](#cloudflare-pages)
- [Jiný statický hosting](#jiný-statický-hosting)
- [Lokální spuštění](#lokální-spuštění)
- [Samostatný soubor](#samostatný-soubor)
- [Hlavičky (_headers)](#hlavičky-_headers)
- [Vydání nové verze](#vydání-nové-verze)
- [Kontrolní seznam po nasazení](#kontrolní-seznam-po-nasazení)

## Cloudflare Pages

Složka `public/` je pro Cloudflare Pages připravená včetně souboru `_headers`.

### A. Napojení na GitHub (doporučeno)

Každý push do `main` se nasadí sám.

1. V Cloudflare otevři **Workers & Pages → Create → Pages → Connect to Git** a vyber repozitář `akordify`.
2. Nastavení sestavení:

   | Pole | Hodnota |
   | --- | --- |
   | Framework preset | `None` |
   | Build command | *(prázdné)* |
   | Build output directory | `public` |
   | Production branch | `main` |

3. **Save and Deploy.** Za chvíli běží web na `https://<projekt>.pages.dev`.
4. Vlastní doménu přidáš v **Custom domains**.

Build command zůstává prázdný schválně. Verzi service workeru přepočítáváš lokálně skriptem `scripts/build.py` před commitem (viz [Vydání nové verze](#vydání-nové-verze)), takže Cloudflare jen zkopíruje hotové soubory.

Náhledové nasazení vznikne pro každou jinou větev a pull request na vlastní adrese `https://<větev>.<projekt>.pages.dev`.

### B. Ruční nahrání

1. **Workers & Pages → Create → Pages → Upload assets.**
2. Nahraj obsah složky `public/` (nebo ZIP s jejím obsahem, soubory musí být v kořeni archivu, ne ve složce).

### C. Z příkazové řádky (Wrangler)

```bash
npx wrangler pages deploy public --project-name akordify
```

## Jiný statický hosting

Funguje cokoli, co umí servírovat soubory přes HTTPS: Netlify, Vercel, GitHub Pages, vlastní nginx…

- **Kořen webu** musí být obsah `public/`, protože service worker a manifest používají absolutní cesty (`/sw.js`, `/icons/…`). Pro umístění do podsložky (např. `https://example.com/akordify/`) je potřeba upravit cesty v `index.html`, `manifest.webmanifest` (`start_url`, `scope`, `id`, ikony) a `sw.js` (`ASSETS`, navigace na `/`).
- **HTTPS** je nutné kvůli service workeru. Na `http://` (kromě `localhost`) aplikace funguje, jen ji nepůjde nainstalovat a nebude fungovat bez připojení.
- **Hlavičky.** Soubor `_headers` je formát Cloudflare Pages a Netlify. Jinde nastav ekvivalent v konfiguraci serveru (viz [Hlavičky](#hlavičky-_headers)). Hlavně `Cache-Control: no-cache` pro `sw.js` a `manifest.webmanifest` a typ `application/manifest+json` pro manifest.

Příklad pro nginx:

```nginx
location = /sw.js                { add_header Cache-Control "no-cache"; }
location = /manifest.webmanifest { add_header Cache-Control "no-cache"; default_type application/manifest+json; }
add_header X-Content-Type-Options nosniff;
add_header Referrer-Policy same-origin;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()";
```

## Lokální spuštění

```bash
python3 -m http.server 8000 --directory public
```

Otevři <http://localhost:8000>. Na `localhost` se service worker zaregistruje stejně jako na HTTPS, takže jde vyzkoušet instalace i režim bez připojení (DevTools → *Network → Offline*).

Při úpravách může service worker podržet starší verzi stránky. Pomůže obnovit stránku dvakrát, nebo v DevTools zapnout *Application → Service Workers → Update on reload*.

## Samostatný soubor

```bash
python3 scripts/build.py
```

vyrobí `dist/akordify.html`, jediný soubor, který jde poslat e-mailem, dát na flashku nebo otevřít dvojklikem. Proti verzi pro web:

- ikona je vložená přímo do stránky,
- chybí manifest a registrace service workeru (z disku by stejně nefungovaly),
- sdílení odkazem je vypnuté, protože adresa `file://` nejde poslat dál. Všechno ostatní funguje, včetně ukládání nápadů a exportu.

Hotový soubor se přikládá ke každému [vydání na GitHubu](https://github.com/cernykafe/akordify/releases).

## Hlavičky (_headers)

```
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: same-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Robots-Tag: noindex, nofollow

/sw.js
  Cache-Control: no-cache

/manifest.webmanifest
  Content-Type: application/manifest+json
  Cache-Control: no-cache
```

| Hlavička | Proč |
| --- | --- |
| `X-Content-Type-Options: nosniff` | prohlížeč nebude hádat typ souboru |
| `Referrer-Policy: same-origin` | při prokliku na jiný web se neposílá adresa stránky |
| `Permissions-Policy` | stránka nemá přístup ke kameře, mikrofonu ani poloze, nepotřebuje je |
| `X-Robots-Tag: noindex, nofollow` | vyhledávače web neindexují. **Smaž tento řádek, pokud chceš, aby šel Akordify najít přes Google.** |
| `Cache-Control: no-cache` u `sw.js` | prohlížeč se při každém načtení zeptá na novou verzi service workeru |
| `Cache-Control: no-cache` u manifestu | změny názvu, barev a ikon se projeví hned |

## Vydání nové verze

1. Uprav `public/index.html` (případně ikony nebo manifest).
2. Spusť build. Přepočítá `VERSION` v `public/sw.js` a vyrobí `dist/akordify.html`:

   ```bash
   python3 scripts/build.py
   ```

3. Commitni a pushni. Cloudflare Pages nasadí `main` automaticky.

   ```bash
   git add public && git commit -m "Popis změny" && git push
   ```

4. Volitelně vydej verzi se samostatným souborem:

   ```bash
   gh release create v1.1.0 dist/akordify.html --title "Akordify 1.1.0" --notes "Co je nového…"
   ```

Uživatelé novou verzi dostanou při dalším otevření. Navigace jde nejdřív na síť, nový service worker se nainstaluje a smaže starou mezipaměť (`skipWaiting` + `clients.claim`).

> **Pozor:** když změníš `index.html` a nespustíš build, `VERSION` zůstane stejná. Stránka se načte nová (síť má přednost), ale ikony a manifest zůstanou ve staré mezipaměti. Kontrola: `python3 scripts/build.py --check` vrátí chybu, když verze nesedí.

## Kontrolní seznam po nasazení

- [ ] Stránka se načte a vygeneruje progresi.
- [ ] Přehrávání hraje (klepni nejdřív kamkoli na stránku).
- [ ] V DevTools → *Application → Manifest* nejsou chyby, ikony se načtou.
- [ ] *Application → Service Workers* ukazuje aktivní `sw.js` se správnou verzí.
- [ ] Po přepnutí do režimu offline a obnovení se aplikace načte.
- [ ] Odkaz na nápad (Export → Odkaz) se otevře v anonymním okně se stejným obsahem.
- [ ] Hlavičky: `curl -I https://<doména>/` ukazuje `X-Content-Type-Options` a další.
