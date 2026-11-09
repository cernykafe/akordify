# Architektura

Technický popis Akordify pro každého, kdo chce aplikaci upravovat nebo pochopit, jak uvnitř funguje.

- [Zásady](#zásady)
- [Anatomie index.html](#anatomie-indexhtml)
- [Moduly a jmenný prostor AK](#moduly-a-jmenný-prostor-ak)
- [Jak vzniká progrese](#jak-vzniká-progrese)
- [Datový model](#datový-model)
- [Zvukový engine](#zvukový-engine)
- [Export: MIDI, ZIP, WAV](#export-midi-zip-wav)
- [Uložení v prohlížeči](#uložení-v-prohlížeči)
- [Sdílení odkazem](#sdílení-odkazem)
- [PWA a service worker](#pwa-a-service-worker)
- [Běhová prostředí](#běhová-prostředí)
- [Přístupnost](#přístupnost)
- [Jak aplikaci upravovat](#jak-aplikaci-upravovat)

## Zásady

- **Jeden soubor, žádné závislosti.** Celá aplikace (markup, styly, písma, ikony i logika) je v `public/index.html`. Neexistuje `node_modules`, bundler ani sestavení, které by bylo k běhu potřeba.
- **ES5 bez transpilace.** Kód používá `var`, funkce a IIFE, žádné šipkové funkce, `let`/`const` ani třídy. Běží tak i ve starších prohlížečích a ve WebView bez úprav.
- **Nic nejde ven.** Žádné `fetch`, `XMLHttpRequest`, WebSocket, cookies ani analytika. Data zůstávají v prohlížeči.
- **Deterministická náhoda.** Každý generátor dostává semínko, takže stejné semínko a parametry dají stejný výsledek.
- **Čeština v rozhraní i v kódu.** Komentáře, názvy sekcí i texty jsou česky, identifikátory anglicky nebo zkratkami.

## Anatomie index.html

Soubor má asi 9 100 řádků a 800 kB. Větší část tvoří vložená písma a JavaScript:

| Řádky (přibližně) | Obsah | Velikost |
| --- | --- | --- |
| 1–18 | `<head>`: meta, manifest, ikony, popis | malá |
| 19 | `@font-face` s písmy DM Sans a DM Mono jako base64 WOFF2 | ~190 kB |
| 20–839 | CSS: proměnné vzhledu, rozložení, komponenty, tmavý režim, animace | ~100 kB |
| 841–1325 | `<body>`: SVG sprite ikon, horní lišta, panely, dialogy | ~30 kB |
| 1326–9127 | hlavní `<script>`: všechny moduly | ~500 kB, ~7 800 řádků |
| 9128–9132 | registrace service workeru (jen ve verzi pro web) | malá |

Čísla řádků se s úpravami posouvají. Spolehlivější orientace jsou komentáře sekcí ve tvaru `/* ===== Název ===== */` (moduly) a `/* --- název --- */` (části modulů):

```bash
grep -n '/\* =====' public/index.html
```

## Moduly a jmenný prostor AK

Každý modul je IIFE `(function (AK) { 'use strict'; … })(AK);`, které přidá své API do globálního objektu `AK`. Moduly jsou v souboru seřazené podle závislostí. Pozdější moduly používají dřívější, nikdy obráceně.

| # | Modul (komentář sekce) | Vystavuje | K čemu |
| --- | --- | --- | --- |
| 1 | Teorie: tóny, módy, akordy, názvy | `AK.makeRng`, `AK.newSeed`, `AK.T` | generátor náhody mulberry32 se semínkem, tóny a jejich hláskování, 6 módů, kvality akordů (intervaly a povinné tóny), diatonické akordy, římské číslice |
| 2 | Stylové profily interpretů a nálady | `AK.GROUPS`, `AK.STYLES`, `AK.MOODS`, `AK.mergeStyles` | 16 profilů ve 4 skupinách a 12 nálad. Profil nese váhy módů, postupů (i s odkazem na píseň), akordů, barev, rytmu, odchylek, kytary a basy |
| 3 | Generátor akordových progresí | `AK.P`, `AK.generate` | zásobník diatonických a vypůjčených akordů, funkce T/PD/D, model přechodů, rozvržení taktů, vzorkování a hodnocení sledů |
| 4 | Sekce písně | `AK.S`, `AK.regenPart`, `AK.regenPart2`, `AK.explain` | barvy akordů, harmonické ozdoby (sekundární dominanty, průchodné akordy, obraty, sus), šablony z reálných písní, navazující část, volba tóniny a tempa, vysvětlení v češtině |
| 5 | Hmaty akordů na kytaře a diagramy | `AK.V` | prohledání a hodnocení tvarů na hmatníku, prstoklad, návrh kapodastru, SVG diagram |
| 6 | Generátor riffů a melodických linek | `AK.R`, `AK.genRiff` | stupnice, rytmické vzorce na 16 šestnáctin, mapování na hmatník dynamickým programováním, techniky, licky v pentatonickém boxu, typy partů |
| 7 | Generátor basových linek | `AK.genBass`, `AK.BASS_TYPES` | čtyřstrunná baskytara E A D G, pět typů linek |
| 8 | Vykreslení tabulatury | `AK.tabBars`, `AK.tabText`, `AK.shapeName` | textový tab po taktech s počítáním dob a technikami |
| 9 | Generátor bicích | `AK.genBeat`, `AK.simplifyBeat`, `AK.verseBeat`, `AK.beatInfo`, `AK.BEAT_FILLS` | vzorce kopák, virbl, hi-hat, ride, shaker se silou úderu 1–9, pravidla podle skupiny stylů, přechody |
| 10 | Syntéza zvuků do bufferů | `AK.DSP` | bikvadratické filtry (RBJ Audio EQ Cookbook), struna Karplus-Strong, syntéza bicích, dozvuky. Čistý JS, testovatelný i mimo prohlížeč |
| 11 | Zvukové presety a vzorce bicích | `AK.SOUND`, `AK.BEATS`, `AK.KIT`, `AK.beatKind` | presety podle skupin stylů: snímač, zesilovač, efekty, místnost |
| 12 | Přehrávání ve Web Audio | `AK.Audio` | zvukový engine nad živým i offline `AudioContext`, hlasy nástrojů, přehrávač se smyčkou, vykreslení skladby a WAV |
| 13 | Export do MIDI a zabalení do ZIP | `AK.Midi`, `AK.zip` | SMF formát 1, ZIP bez komprese |
| 14 | Úprava progrese | `AK.Subs` | náhrady akordu: stejná funkce, jiná barva, společné tóny, vypůjčené akordy, dominanta k dalšímu akordu (i tritonová záměna), jiný bas |
| 15 | Galerie akordů | `AK.Book` | názvy akordů, hledání podle textu (i české notace), poznání akordu z hmatu |
| 16 | Uživatelské rozhraní | `AK.App` | stav, vykreslení, ovládání, historie, ukládání, export, sdílení, nápověda, návod |

Moduly 1–15 nesahají na DOM. SVG diagram hmatu vracejí jako řetězec a k Web Audio přistupují jen přes kontext, který dostanou. Dají se proto načíst a testovat i v Node.js: z hlavního `<script>` se vezme část před sekcí *Uživatelské rozhraní* a spustí se. Moduly si objekt `AK` založí na `globalThis` samy.

```js
// test.js, spuštění: node test.js
const fs = require('fs');
const html = fs.readFileSync('public/index.html', 'utf8');
const core = html.slice(html.indexOf('/* ===== Teorie'), html.indexOf('/* ===== Uživatelské rozhraní'));
(0, eval)(core);   // nepřímý eval: AK vznikne jako globální proměnná

const a = AK.generate({ seed: 42, complexity: 3, voc: 'common' });
const b = AK.generate({ seed: 42, complexity: 3, voc: 'common' });
console.log(a.key, a.bpm, a.sections.map(s => s.chords.length));
console.log('deterministické:', JSON.stringify(a) === JSON.stringify(b));
console.log(AK.Book.parse('Hmi'));   // { root: 11, q: 'min', … }
```

## Jak vzniká progrese

`AK.generate(params)` v modulu 3:

1. **Semínko.** `params.seed` nebo nové náhodné. Z něj se vytvoří `rng` (mulberry32).
2. **Styl a nálada.** Vyberou se profily stylu a `AK.mergeStyles` je sloučí do jednoho souboru vah. Nálada váhy dál posune (módy, akordy, tempo, bicí).
3. **Tónina a mód.** Váhy módů ze stylu krát nálada, omezené volbou uživatele. Když je mód „podle stylu“ a výsledné akordy charakteristický tón módu nepoužijí (třeba lydickou kvartu), popisek se zjednoduší na obyčejný dur nebo moll.
4. **Smyčka refrénu.** Buď šablona postupu z profilu (např. `I ii7 V iii7` s odkazem na píseň), nebo sled vzorkovaný z modelu přechodů mezi funkcemi tónika, subdominanta a dominanta. Kandidáti se hodnotí a vybere se nejlepší.
5. **Barvy a ozdoby.** Podle úrovně akordů (`simple`, `common`, `rich`) a složitosti 1–5 se přidají septimy, sus, add9, sekundární dominanty, průchodné akordy a obraty.
6. **Navazující část.** Sloka nebo bridge s více kandidáty, hodnocenými podle napojení na smyčku.
7. **Výsledek** je objekt `state` (viz níže). Riff, basa a bicí se generují zvlášť nad tímto stavem, každý s vlastním semínkem, takže jdou přegenerovat nezávisle.

## Datový model

Hlavní stav nápadu (`state`, verze 2):

```js
{
  v: 2,                       // verze formátu
  seed: 123456789,            // semínko generátoru
  params: { … },              // parametry z levého panelu
  styleIds: ['strokes', …],   // použité stylové profily
  styleName: 'The Strokes',
  group: 'garage',            // skupina stylů nebo null
  moodId: 'melancholy',
  key: { pc: 9, mode: 'aeolian' },   // pc = tónová třída 0–11 (C = 0)
  bpm: 105,
  complexity: 3,              // 1–5
  voc: 'common',              // simple | common | rich
  sections: [
    { bars: 4, chords: [ { q: 'min', beats: 4, … }, … ], ref: { song, artist, exact } },  // 0 = refrén (hlavní smyčka)
    { kind: 'refren', bars: 4, chords: [ … ] },   // navazující část: sloka (název druhu je historický)
    { kind: 'bridge', bars: 4, chords: [ … ] }    // bridge
  ]
}
```

Část 0 je vždy refrén, tedy hlavní smyčka. Za ní může být nejvýš jedna sloka a jeden bridge, v tomto pořadí. Pozor na historický název: navazující část druhu `'refren'` se v rozhraní zobrazuje jako **sloka**. Začíná mimo tóniku a dominantou vede do refrénu. Mapování dělají funkce `partName` a `secLabel` v UI modulu. `ref` nese odkaz na píseň, ze které postup vychází (`exact` = stejný sled stupňů).

Vedle `state` drží UI i další části nápadu:

| Proměnná | Obsah |
| --- | --- |
| `parts` | vygenerované linky leadu a basy, bicí a sled bloků skladby s textem |
| `vsel` | vybraná varianta hmatu pro každý akord |
| `capo` | pozice kapodastru |
| `tempo` | tempo přehrávání (může se lišit od `state.bpm`) |

Uložený nápad, poslední stav i odkaz pro sdílení serializují tutéž sadu `{ state, parts, vsel, capo, tempo, … }`. Před načtením z odkazu proběhne kontrola tvaru dat (`validShare`).

## Zvukový engine

Všechno se syntetizuje. Aplikace nemá jediný zvukový soubor.

- **Struny.** Algoritmus Karplus-Strong s frakčním zpožděním (přesné ladění), místem úhozu, šumovým buzením a modelem snímačů. Kytara pro riffy je model Telecasteru (ocelové struny, jednocívkové snímače u kobylky, uprostřed a u krku), basa model Precision. Struny se předpočítají do bufferů.
- **Filtry.** Bikvadratické filtry podle RBJ Audio EQ Cookbook, rezonance snímačů a korpusu.
- **Bicí.** Jedna syntetizovaná sada pro všechny styly: kopák, virbl, hi-hat, ride, shaker a tři tomy. Kopák a virbl mají tři síly úderu, hi-hat a ride dvě, každý úder ve dvou variantách, aby opakované údery nezněly strojově. Styly se liší místností, filtrem a saturací.
- **Ostatní nástroje** (elektrické piano, varhany, syntezátory, vibrafon, flétna, 8bit, pad) jsou oscilátory Web Audio s obálkami, filtry, vibratem a glissandem.
- **Efekty.** Dozvuk (konvoluce s vygenerovanou impulsní odezvou), ozvěna, zkreslení, jas a místnost bicích. Pět ovladačů *Doladění zvuku* škáluje hodnoty presetu.
- **Přehrávač** plánuje noty dopředu nad `AudioContext.currentTime` a umí smyčku části i celé skladby. Na dotykových zařízeních přepne na úspornější režim (`Player.setLite`).
- **Stejný engine pro živé hraní i export.** `build()` pracuje nad libovolným kontextem, živým i `OfflineAudioContext`, takže WAV zní stejně jako přehrávač.

## Export: MIDI, ZIP, WAV

- **MIDI.** `AK.Midi` zapisuje standardní MIDI soubor formátu 1 bajt po bajtu (hlavička `MThd`, stopy `MTrk`, delta časy jako VLQ, tempo a takt v meta událostech). Stopy: akordy, akordy po blocích, lead, basa a bicí na kanálu 10 (General MIDI).
- **ZIP.** `AK.zip` skládá archiv metodou *stored* (bez komprese) s CRC-32. Na MIDI soubory to stačí a ušetří to knihovnu.
- **WAV.** Skladba se vykreslí v `OfflineAudioContext` a zabalí do stereo WAV (16bitové PCM).
- **Ukládání souborů** jde přes odkaz se `download`. Na dotykových zařízeních přes `navigator.share` se souborem, pokud ho systém umí, a v nativním obalu přes most do aplikace (viz níže).

## Uložení v prohlížeči

| Klíč | Úložiště | Obsah |
| --- | --- | --- |
| `akordarna.settings.v2` | `localStorage` | nastavení: vzhled, barva, značení, nástroje, hlasitosti, rozvržení, sbalené sekce… |
| `akordarna.favs.v1` | `localStorage` | pole uložených nápadů `{ id, name, date, state, parts, vsel, capo, tempo, … }` |
| `akordarna.last.v2` | `localStorage` | poslední rozpracovaný stav, obnoví se po spuštění |
| `akordify.alive` | `sessionStorage` | značka běžící stránky. Při řádném zavření nebo skrytí se smaže. Když po načtení zůstala, stránka spadla nebo ji systém zavřel, a aplikace upozorní, že rozpracovaný nápad zůstal uložený |

Prefix `akordarna.` je historický, z původního názvu aplikace. Starší nastavení `akordarna.settings.v1` se při prvním spuštění převezme. Přístup k úložišti je vždy v `try/catch`, takže aplikace funguje i tam, kde je úložiště zakázané (jen si nic nepamatuje).

Nainstalovaná PWA volá `navigator.storage.persist()`, aby prohlížeč uložené nápady při nedostatku místa nemazal.

## Sdílení odkazem

Celý nápad je zakódovaný v části adresy za `#`. Ta se serveru nikdy neposílá.

```
https://…/#n=z<base64url>   JSON zkomprimovaný přes CompressionStream('deflate-raw')
https://…/#n=j<base64url>   prostý JSON (prohlížeč bez CompressionStream)
```

Při otevření aplikace odkaz dekóduje, ověří tvar dat, uloží předchozí stav do historie (dá se vrátit krokem zpět) a adresu vyčistí přes `history.replaceState`. Sdílení odkazem je dostupné jen na `http(s):`, ne v souboru otevřeném z disku.

## PWA a service worker

- `manifest.webmanifest`: název, barvy, `display: standalone`, ikony 192 a 512 px a maskable ikona.
- `sw.js`:
  - při instalaci uloží do mezipaměti stránku, manifest a ikony (`ASSETS`),
  - při aktivaci smaže mezipaměti jiných verzí,
  - **navigace: nejdřív síť**, aby se po nasazení hned načetla nová verze. Bez připojení vrátí uloženou kopii,
  - **ostatní soubory: nejdřív mezipaměť**, jinak síť.
- `VERSION` v `sw.js` je otisk obsahu cachovaných souborů a přepočítává ho `scripts/build.py`. Změna obsahu tak vždy znamená novou mezipaměť.
- Service worker se registruje jen na `https:` nebo `localhost`.

## Běhová prostředí

Kód počítá se třemi prostředími:

| Prostředí | Jak se pozná | Rozdíly |
| --- | --- | --- |
| Web / PWA | běžný `http(s):` | vše včetně sdílení odkazem a service workeru |
| Samostatný soubor | `file:` | bez service workeru a sdílení odkazem, jinak plná funkce |
| Nativní obal pro macOS | `window.webkit.messageHandlers.akordify` | soubory se ukládají přes most do aplikace. Nabídky aplikace volají `AK.App` (`newProg`, `undo`, `redo`, `save`, `exportMidi`, `togglePlay`) |

Kód také počítá s během v náhledu artefaktu v Claude, kde se stahované soubory balí do ZIPu a sdílení odkazem je vypnuté.

## Přístupnost

- Ovládací prvky mají `aria-label`, přepínače `aria-pressed`, dialogy jsou nativní `<dialog>`.
- Celá aplikace jde ovládat klávesnicí, včetně fokusu drženého v úvodním návodu a zkratek.
- Animace jsou krátké, jen `transform` a `opacity`, a při systémovém omezení pohybu (`prefers-reduced-motion`) se vypnou.
- Světlý i tmavý vzhled, barvy přes CSS proměnné.

## Jak aplikaci upravovat

1. Uprav `public/index.html`. Hledej podle komentářů sekcí (viz [Anatomie](#anatomie-indexhtml)).
2. Vyzkoušej lokálně: `python3 -m http.server 8000 --directory public` a otevři <http://localhost:8000>.
   - Service worker může při vývoji držet starou verzi. V DevTools zapni *Application → Service Workers → Update on reload*, nebo stránku obnov dvakrát.
3. Spusť `python3 scripts/build.py`. Přepočítá `VERSION` v `sw.js` a vyrobí `dist/akordify.html`.
4. Commitni `public/`. Složka `dist/` se do repozitáře neukládá, samostatný soubor se přikládá k vydání (*Releases*).

### Kam sáhnout, když chceš…

| Chceš | Kde |
| --- | --- |
| přidat styl nebo interpreta | modul 2, `STYLES` a `GROUPS` |
| přidat náladu | modul 2, `MOODS` |
| přidat kvalitu akordu | modul 1, `Q`, pak minimální složitost v modulu 3 a barvy v modulu 4 |
| změnit, jak zní nástroj | modul 11 (presety), modul 12 (hlasy) |
| přidat typ basové linky | modul 7, vzorce a `TYPE_NAMES` |
| upravit texty rozhraní | `<body>` (statické texty) a modul 16 (dynamické texty a nápověda) |
