# Fremdcode und Referenzen

Die MIT-Lizenz im Repository-Hauptverzeichnis gilt für den eigenen Projektcode.
Fremdcode behält seine jeweiligen Urheber- und Lizenzhinweise. Der KI-Hinweis
im README ändert diese Lizenzbedingungen nicht.

## Mitgelieferter Fremdcode

### CodeMirror 5.65.13

- Dateien: `custom_components/fhem_bridge/codemirror/`
- Herkunft: https://github.com/codemirror/codemirror5/tree/5.65.13
- Lizenz: MIT
- Copyright (C) 2017 by Marijn Haverbeke <marijn@haverbeke.berlin> and others
- Vollständiger Lizenztext: [CodeMirror LICENSE](custom_components/fhem_bridge/codemirror/LICENSE)

Die vorhandenen Lizenz- und Urheberhinweise bleiben unverändert erhalten.
Das Perl-Sprachmodul nennt zusätzlich seinen Ursprung im Projekt
[CodeMirror_mode_perl](https://github.com/sabaca/CodeMirror_mode_perl);
auch dieser Hinweis bleibt in `perl.js` erhalten. Die CodeMirror-Lizenz gilt
auch für die mitgelieferte CSS-Datei.

## Referenzen und externe Laufzeitumgebungen

### ioBroker.fhem

[ioBroker.fhem](https://github.com/iobroker-community-adapters/ioBroker.fhem)
diente als Referenz für dynamische FHEM-Objekte, Befehlslisten und deren
Interpretation. Unsere Projektdokumentation beschreibt eine eigenständige
HA-Implementierung, keinen Port des JavaScript-Adapters. Bei der aktuellen
Prüfung wurde keine ausdrücklich gekennzeichnete direkte Codeübernahme
gefunden; dies ist kein lückenloser Herkunftsnachweis aller Codezeilen.

Der Adapter steht unter [MIT](https://github.com/iobroker-community-adapters/ioBroker.fhem#license).
Bei einer Übernahme von Code oder wesentlichen Codeanteilen müssen dessen
vollständiger Lizenztext und die zugehörigen Urheberhinweise mitgeführt werden.

### FHEM

[FHEM](https://fhem.de/fhem.html) steht unter GPLv2. Das Repository liefert den
FHEM-Kern nicht mit. HABridge nutzt vorhandene FHEM-Funktionen; die
Bedienung orientiert sich an FHEMWEB. Modell- und Kanalinformationen in
`Vorlagen/Default/hmconfig-*.yaml` beziehen sich laut ihren Beschreibungen auf
`HMConfig.pm`; diese Quellenangaben bleiben erhalten. Eine Quellenreferenz
oder Modellbezeichnung allein belegt keine Übernahme von Programmcode.
Tatsächlich übernommener GPL-Code dürfte nicht pauschal unter MIT umgelabelt
werden; für solche Bestandteile wären die GPL-Pflichten gesondert einzuhalten.

### Home Assistant

[Home Assistant Core](https://github.com/home-assistant/core/blob/dev/LICENSE.md)
steht unter Apache 2.0 und wird hier nicht mitgeliefert. Die HA-Integration
verwendet dessen Schnittstellen. Die MIT-Lizenz dieses Projekts ersetzt keine
Lizenzbedingungen von Home Assistant oder anderen Abhängigkeiten.

## Weitere Beiträge

Bei künftig übernommenem Fremdcode sind Quelle, betroffene Dateien, Lizenz
und erforderliche Urheberhinweise hier und gegebenenfalls direkt an den
Dateien zu ergänzen. Vorhandene Hinweise dürfen nicht entfernt werden.
