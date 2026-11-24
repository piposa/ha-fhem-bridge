# FHEM Bridge für Home Assistant

<p align="center">
  <img src="logo.jpg" alt="FHEM Bridge – FHEM und Home Assistant verbinden" width="360">
</p>

**Bestehende FHEM-Geräte in Home Assistant nutzen – mit ihren Readings, Befehlen und Attributen.**

| Bestandteil | Stand |
| --- | --- |
| HA-Integration | **0.9.69 · Vorabversion** |
| FHEM-Modul HABridge | **0.9.44** |
| Home Assistant | **2026.11 oder neuer** |
| Verbindung | Lokales TCP mit TLS und gemeinsamem Secret |

## Inhalt

- [Einführung](#einführung)
- [Funktionsumfang](#funktionsumfang)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Verbindung einrichten](#verbindung-einrichten)
- [Geräte importieren und gruppieren](#geräte-importieren-und-gruppieren)
- [Geräteseite gestalten](#geräteseite-gestalten)
- [Geräte bedienen und Attribute bearbeiten](#geräte-bedienen-und-attribute-bearbeiten)
- [Automationen](#automationen)
- [Vorlagen](#vorlagen)
- [Updates und Vorabversionen](#updates-und-vorabversionen)
- [Status und Diagnose](#status-und-diagnose)
- [Grenzen](#grenzen)
- [Fehler melden](#fehler-melden)

## Einführung

FHEM Bridge verbindet eine bestehende FHEM-Installation mit Home Assistant. Geräte bleiben an FHEM angeschlossen und werden dort weiterhin von ihren bewährten Modulen angesprochen. Home Assistant übernimmt die Darstellung, Bedienung und auf Wunsch die Automationen.

Die Integration ist für Installationen gedacht, die schrittweise zu Home Assistant wechseln oder beide Systeme dauerhaft gemeinsam nutzen möchten. Insbesondere bei älteren Funkgeräten, speziellen FHEM-Modulen oder individuellen Erweiterungen ist ein Austausch der bestehenden Geräteanbindung nicht immer sinnvoll.

FHEM Bridge besteht aus zwei Teilen: dem Perl-Modul **HABridge** in FHEM und der Integration **FHEM Bridge** in Home Assistant. Beide kommunizieren im lokalen Netzwerk über eine dauerhafte TLS-Verbindung. Für die Bridge ist kein MQTT-Broker erforderlich. Nach der Installation benötigt die Gerätekommunikation keinen Cloud-Dienst.

## Funktionsumfang

- Geräte gezielt nach Raum, FHEM-Modul und Modell auswählen.
- Mehrere FHEM-Instanzen als getrennte, benennbare Hubs verbinden.
- Zusammengehörige Kanäle auf einer gemeinsamen HA-Geräteseite darstellen.
- Readings als Messwert, Binärsensor, Diagnose, ausgeblendet oder nicht übernommen konfigurieren.
- Set-/Get-Befehle über Formulare ausführen und geeignete Befehle als HA-Bedienelemente bereitstellen.
- Automatisch zugeordnete oder manuell gewählte Vorlagen nutzen und bearbeiten.
- FHEM-Attribute lesen, hinzufügen, ändern und löschen.
- Berechtigungen je Gerät beziehungsweise Kanal steuern.
- Ungespeicherte FHEM-Konfigurationen pro Bridge erkennen und bei entsprechender Freigabe speichern.

Funktionen und Entitäten richten sich nach den von FHEM gelieferten Metadaten und der gewählten Vorlage. Eine Vorlage ergänzt keine Fähigkeiten, die das Gerät beziehungsweise sein FHEM-Modul nicht besitzt.

## Voraussetzungen

| System | Voraussetzung |
| --- | --- |
| Home Assistant | Version 2026.11 oder neuer; Administratorzugang für die Einrichtung |
| FHEM | Funktionierende Geräteanbindung; Perl mit den vom Modul benötigten Sprachfunktionen und Bibliotheken |
| TLS in FHEM | `IO::Socket::SSL` und `Net::SSLeay`, einschließlich EC-Zertifikatsunterstützung |
| Netzwerk | HA erreicht den gewählten TCP-Port von FHEM; die in HABridge hinterlegte HA-Quelladresse stimmt |
| Installation und Updates | Zugriff auf GitHub; für das Hinzufügen per GitHub-Link eine GitHub-Verbindung im HA-Marketplace |

Unter Ubuntu lassen sich die TLS-Bibliotheken beispielsweise so installieren:

```bash
sudo apt install libio-socket-ssl-perl libnet-ssleay-perl
```

Bei OpenWrt und anderen Plattformen hängen die Paketnamen vom System ab. Auch dort müssen die genannten Perl- und TLS-Funktionen vorhanden sein. Für schwächere Hardware besteht keine pauschale Leistungszusage; die Einrichtungs- und Abgleichzeiten lassen sich mit der abschaltbaren Diagnose untersuchen.

## Installation

Installiere beide Bestandteile. Die HA-Integration installiert das Perl-Modul nicht automatisch auf dem FHEM-Rechner.

### 1. HABridge in FHEM installieren

Die folgenden Befehle einzeln in der **FHEMWEB-Befehlszeile** ausführen:

```text
update add https://raw.githubusercontent.com/piposa/ha-fhem-bridge/main/FHEM/controls_habridge.txt
```

```text
update check habridge
```

```text
update all habridge
```

Die Quelle installiert ausschließlich das Perl-Modul, das FHEMWEB-Icon und den zugehörigen MIT-Lizenztext. [CHANGED](FHEM/CHANGED) enthält die Updatehinweise; [MAINTAINER.txt](FHEM/MAINTAINER.txt) nennt `pantau` als Ansprechpartner im FHEM-Forum. Diese beiden Informationsdateien liegen neben der Kontrolldatei und überschreiben keine globalen FHEM-Dateien. FHEM-Konfigurationen und Zertifikate werden nicht mitgeliefert. Ein Prozessneustart wird von dieser Updatequelle nicht angefordert.

Alternativ die Dateien aus diesem Repository relativ zum FHEM-Installationsverzeichnis ablegen:

| Repository-Datei | Ziel in FHEM |
| --- | --- |
| `FHEM/FHEM/98_HABridge.pm` | `FHEM/98_HABridge.pm` |
| `FHEM/FHEM/HABridge-LICENSE.txt` | `FHEM/HABridge-LICENSE.txt` |
| `FHEM/www/images/default/habridge.png` | `www/images/default/habridge.png` |

### 2. FHEM Bridge über den HA-Marketplace installieren

1. **Einstellungen → Marketplace** öffnen.
2. Über die Funktion **Über einen GitHub-Link hinzufügen** dieses Repository hinzufügen:
   `https://github.com/piposa/ha-fhem-bridge`
3. **FHEM Bridge** installieren. Für die Teststände die **Vorabversionen** des Repositorys aktivieren und die gewünschte Version auswählen.
4. Falls HA nach der Installation einen Neustart verlangt, diesen selbst zum passenden Zeitpunkt durchführen.

Die Integration wird nach `custom_components/fhem_bridge/` im HA-Konfigurationsverzeichnis installiert. Ein selbst erstelltes oder manuell hochgeladenes ZIP ist nicht erforderlich.

### Manuelle HA-Installation

Den vollständigen Ordner `custom_components/fhem_bridge/` in das gleichnamige Unterverzeichnis der HA-Konfiguration kopieren. Zu einer bestehenden Installation gehören auch die JavaScript-Dateien, Vorlagen, Übersetzungen, Icons und CodeMirror-Dateien. Anschließend HA selbst neu starten, damit der Python-Code geladen wird.

## Verbindung einrichten

### 1. Secret erzeugen

In einem Terminal auf dem Mac, Linux-Rechner oder einem anderen geeigneten System:

```bash
openssl rand -hex 32
```

Das erzeugt 64 Hexadezimalzeichen. Dasselbe Secret auf beiden Seiten eintragen; für jede weitere Bridge ein eigenes Secret verwenden.

### 2. HABridge in FHEM definieren

In FHEMWEB:

```text
define HA_Bridge HABridge <HA-IPv4> 19091 <Secret>
```

| Parameter | Bedeutung |
| --- | --- |
| `HA_Bridge` | Frei wählbarer Name der FHEM-Definition |
| `HABridge` | Fester FHEM-Modulname |
| `<HA-IPv4>` | Erlaubte Quelladresse des HA-Rechners, wie FHEM sie im Netzwerk sieht |
| `19091` | Freier TCP-Port auf dem FHEM-Rechner; möglich sind 1024 bis 65535 |
| `<Secret>` | 32 bis 128 ASCII-Buchstaben, Ziffern, Unterstriche oder Bindestriche |

Beim ersten Define erzeugt FHEM ein lokales TLS-Zertifikat samt privatem Schlüssel. Die Datei `.habridge-<Port>.pem` liegt unter `global modpath` und muss vertraulich behandelt werden. Das Secret steht in der Definition und nach `save` auch in der gespeicherten FHEM-Konfiguration.

### 3. Hub in HA hinzufügen

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → FHEM Bridge** öffnen. Bei einer weiteren FHEM-Instanz **Hub hinzufügen** verwenden.
2. Optional einen Bridge-Namen vergeben. Ohne eigene Angabe verwendet HA `FHEM · <Host>`.
3. Die **FHEM-Adresse**, den TCP-Port und das gemeinsame Secret eingeben.
4. Den angezeigten SHA-256-Fingerabdruck mit `TLS_FINGERPRINT` aus `list HA_Bridge` in FHEM vergleichen und bestätigen.

Das Secret wird erst nach Bestätigung des Zertifikats übermittelt. Jede FHEM-Instanz bekommt einen eigenen HA-Hub. Bei verschiedenen FHEM-IP-Adressen darf derselbe Port verwendet werden. Jede HABridge-Definition akzeptiert jeweils nur eine Clientverbindung.

Für das FHEMWEB-Icon optional:

```text
set WEB rereadicons
attr HA_Bridge icon habridge
```

`WEB` und `HA_Bridge` durch die tatsächlichen Namen der verwendeten FHEM-Definitionen ersetzen.

## Geräte importieren und gruppieren

Am **Zahnrad der Bridge** stehen die Import- und Gruppierungsfunktionen zur Verfügung.

1. **Geräte importieren** öffnen. Bei Bedarf nach Name, Raum, FHEM-Modul oder Modell filtern.
2. Die gewünschten Geräte beziehungsweise Gruppen auswählen.
3. Weiter zu **Bereichen und Labels** wechseln. HA erlaubt pro Gerät einen Bereich; weitere Zuordnungen lassen sich als Labels übernehmen. Zuletzt gewählte verfügbare Bereiche und Labels stehen bei den weiteren Geräten oben, werden aber nicht automatisch ausgewählt.
4. Das Ziel unter **Nach dem Import öffnen** wählen und den Import bestätigen.

Eine FHEM-Definition ist nicht immer ein physisches Gerät. Die Oberfläche unterscheidet deshalb Geräte und ihre zugehörigen Definitionen beziehungsweise Kanäle.

Unter **Geräte gruppieren** lassen sich zusammengehörige Definitionen einem Hauptgerät zuordnen. Die Vorschau vor dem Speichern prüfen. Die Kanäle erscheinen anschließend auf der gemeinsamen HA-Geräteseite; ihre Befehle, Readings und Berechtigungen bleiben dem jeweiligen Kanal zugeordnet. Eine manuelle Gruppe lässt sich über die Gruppenverwaltung wieder auflösen.

Nach einem Import kann direkt zum Gruppierungsdialog für die gerade importierten Geräte gewechselt werden. Der Import und das anschließende Gruppieren sind getrennte Bestätigungen.

## Geräteseite gestalten

Auf der HA-Geräteseite **Besuchen → Geräteseite gestalten** öffnen und bei Mehrkanalgeräten den gewünschten Kanal wählen.

- **Vorlage:** automatisch erkannten Aufbau verwenden, eine andere Vorlage wählen oder die Vorlage deaktivieren.
- **Readings:** festlegen, welche Werte als Messwert, Binärsensor oder Diagnose erscheinen, ausgeblendet bleiben oder nicht übernommen werden.
- **Bedienelemente:** angebotene Set-/Get-Befehle hinzufügen, beschriften und ihre Eingabeform konfigurieren.

Der Ablauf ist **Ändern → Änderungen prüfen → Änderungen anwenden**. Bei der Prüfung den Geltungsbereich für das einzelne Gerät, ausgewählte Geräte oder eine passende Geräteklasse festlegen. Vorlagenzuordnung und individuelle Anpassungen sind getrennte Einstellungen.

Für geänderte sichtbare Readings zeigt die Prüfung zusätzlich den zuletzt empfangenen Wert und die vorgesehene Einheit. Fehlt ein Wert im HA-Cache, wird dies ausgewiesen. Die Vorschau startet keine zusätzliche FHEM-Leseabfrage.

## Geräte bedienen und Attribute bearbeiten

### Berechtigungen

Das **Zahnrad der oberen Gerätezeile** öffnet die Geräteoptionen. Dort werden je Kanal Set, Get, Attributänderungen und technische Befehle freigegeben. Bei neuen Importen sind diese vier Freigaben standardmäßig aktiv; Protokollabonnements sind standardmäßig aus.

Ein Entzug der Freigabe entfernt bestehende Bedienelemente nicht. Die Ausführung wird gesperrt, bis die erforderliche Freigabe wieder vorliegt. Die Gestaltung der Geräteseite bleibt möglich.

### Set und Get

Unter **Besuchen → Gerätebedienung** den Kanal und den gewünschten Befehl auswählen. Die Formulare berücksichtigen die von FHEM angebotenen Wertlisten und unterstützten Widgetangaben. Eine Wertliste mit nur einem Eintrag ist ebenfalls eine Auswahl. Komplexe, nicht unterstützte FHEMWEB-Widgets können eine manuelle Argumenteingabe erfordern.

### Attribute

Unter **Besuchen → Geräteattribute** stehen die gesetzten Attribute mit Suche und Bearbeitung bereit. Ein Klick auf den Attributnamen öffnet den Editor im selben Reiter. Neue Attribute können aus dem von FHEM gelieferten Katalog gewählt werden. Lange Werte lassen sich mit Syntaxdarstellung, weichem Zeilenumbruch und optionalem Vollbild bearbeiten.

**Wert speichern** setzt das Attribut in FHEM. Es entspricht keinem globalen FHEM-`save`. Harte Zeilenumbrüche, Backslashes und Formeln sind Bestandteil des Wertes und sollten bewusst bearbeitet werden.

### FHEM-Konfiguration dauerhaft speichern

Bei ungespeicherten Änderungen erscheint eine eigene HA-Benachrichtigung pro Bridge, mit Bridge-Namen, FHEM-Adresse und Link zur passenden Konfiguration. Dort kann das globale Speichern ausgelöst werden, wenn es in FHEM ausdrücklich erlaubt ist:

```text
attr HA_Bridge allowConfigSave 1
```

Ein globales `save` speichert sämtliche offenen FHEM-Konfigurationsänderungen, auch Änderungen außerhalb von HA. Standardmäßig ist diese Freigabe aus. Erfolgreiches Speichern entfernt nur die Meldung der betreffenden Bridge.

## Automationen

Importierte Sensoren und Bedienelemente sind normale HA-Entitäten und können im Automationseditor verwendet werden. Für variable Set-/Get-Aufrufe steht zusätzlich die Aktion `fhem_bridge.execute` zur Verfügung. Sie nimmt das HA-Gerät, bei Bedarf den FHEM-Kanal, Befehlsart, Befehlsnamen und Argumente entgegen.

Unter **Gerätebedienung → Für Automation verwenden** lässt sich ein angebotener Befehl für eine Automation vorbereiten oder als HA-Skript speichern. Bereits vorhandene zugehörige Skripte werden in der Gerätebedienung aufgelistet.

FHEM-Automationen wie DOIF, notify oder at werden nicht automatisch nach HA übersetzt. Bei einer Migration zunächst die HA-Automation prüfen und danach die entsprechende FHEM-Automation bewusst deaktivieren, damit Befehle nicht doppelt ausgeführt werden.

## Vorlagen

Mitgelieferte Vorlagen ordnen Geräte anhand von FHEM-Modul, Modell und bei Bedarf Kanalrolle oder Funktionsmerkmalen ein. Ein vorhandenes Modell hat bei der Klassifizierung Vorrang. Gerätenamen und Raumnamen sind keine allgemeine Klassifizierungsregel.

Vorlagen bestimmen Readings, Metadaten und Bedienelemente. Eigene Geräteanpassungen können davon abweichen. Unter **Vorlagen verwalten** werden Vorlagen bearbeitet und Varianten angelegt; die gerätespezifische Auswahl bleibt auf der jeweiligen Gestaltungsseite.

| Gerätegruppe | Beispiele für die Darstellung |
| --- | --- |
| Schaltaktoren und Steckdosen | Ein/Aus, verfügbare Timer und tatsächlich vorhandene Messwerte |
| Dimmer | Helligkeit und angebotene Befehle |
| Rollladen und Markise | Fahrbefehle und gegebenenfalls Stopp; keine erfundene Rückmeldung |
| Unterstützte Thermostate | Klimabedienung, Messwerte und bei unterstützter Familie Wochenplan |
| Kontakte, Bewegungs- und Rauchmelder | Binäre Zustände und passende Diagnosewerte |
| Umwelt- und Wettersensoren | Temperatur, Feuchte und weitere vorhandene Messwerte |
| Zähler und elektrische Messgeräte | Readings mit geeigneten Einheiten und Zustandsklassen |
| DLPIO8 | Digitale `value`-Zustände beziehungsweise bereits in FHEM nach °C umgerechnete Analogwerte |

Bei DLPIO8Voltage mit echten Spannungs- oder Stromwerten die Temperaturvorlage beziehungsweise die Einheit anpassen. Die Vorlage selbst nimmt keine Umrechnung vor.

Mitgelieferte Standards liegen unter `custom_components/fhem_bridge/Vorlagen/Default/`. Arbeitskopien und eigene Vorlagen liegen je Bridge im HA-Konfigurationsverzeichnis unter `fhem_bridge/Vorlagen/<Bridge-Eintrag>/`. Angepasste Arbeitskopien werden durch einen neuen Standard nicht ungeprüft ersetzt; verfügbare Standardupdates werden zur Prüfung angezeigt.

## Updates und Vorabversionen

### Home Assistant

Updates über den Marketplace installieren. Zum Testen die Vorabversionen dieses Repositorys aktivieren und eine neuere veröffentlichte Version auswählen. Ein Git-Tag allein ist keine Marketplace-Veröffentlichung; dafür gehört eine GitHub-Release dazu. Einen erforderlichen HA-Neustart selbst planen.

### FHEM

```text
update check habridge
```

```text
update all habridge
```

Das aktualisiert Dateien, lädt aber eine bereits laufende Modulversion nicht automatisch neu. Das Modul lässt sich anschließend bewusst ohne FHEM-Prozessneustart laden:

```text
reload 98_HABridge
```

Die geladene Version steht unter `MODULE_VERSION` in `list HA_Bridge`. Eine reine Änderung an der HA-Integration erfordert kein erneutes Update des unveränderten Perl-Moduls.

**Die FHEM-Quelle auf `main` enthält die freigegebenen Teststände.** FHEM berücksichtigt den GitHub-Vorabversionsschalter nicht. HA- und FHEM-Versionsnummer werden deshalb getrennt ausgewiesen; nicht jede HA-Veröffentlichung verändert das Perl-Modul.

## Status und Diagnose

In FHEM zeigt `state` **online**, **offline**, **error** oder **disabled**. `statusReason` erklärt den Zustand. Weitere Readings nennen die letzte Verbindung, Trennung und den zuletzt gespeicherten Fehler. Ein alter Fehler bedeutet nicht automatisch, dass die aktuelle Verbindung getrennt ist. HA stellt eigene Bridge-Status- und Diagnoseentitäten bereit.

| Zweck | Aktivieren | Abschalten |
| --- | --- | --- |
| FHEM-Verbindungswechsel | `attr HA_Bridge verbose 4` | `deleteattr HA_Bridge verbose` – danach gilt wieder die globale Einstellung |
| FHEM-Zeitmessung und Verkehrszähler | `attr HA_Bridge bridgeDiagnostics 1` | `attr HA_Bridge bridgeDiagnostics 0` |
| Bridgeeigene Speicherentwicklung, Intervall in Sekunden | `attr HA_Bridge memoryDiagnostics 60` | `attr HA_Bridge memoryDiagnostics 0` |
| HA-Einrichtungsdiagnose | Logger `custom_components.fhem_bridge.config_flow.diagnostics` auf `debug` | Logger auf `critical`; `warning` zeigt nur langsame Phasen |

Die HA-Logger lassen sich mit der Aktion `logger.set_level` einstellen. Einrichtungsdiagnose und normale Verbindungsfehler sind getrennte Logger. Die neuen Einrichtungsdiagnosen protokollieren keine Secrets. FHEM-Speicherwerte beziehen sich auf Bridge-Puffer und Datenstrukturen, nicht auf den gesamten Prozess oder Container. `Devel::Size` ergänzt optional die Perl-Strukturschätzung.

Auf der HA-Integrationsseite stehen Debug-Protokollierung und Diagnosedownload zur Verfügung. In FHEM beschreibt `help HABridge` die aktuellen Befehle, Attribute und Readings.

## Grenzen

- **Vorabversion:** Lokale Regressionstests ersetzen keine vollständige Abnahme mit realen Geräten. Die Marketplace- und FHEM-Updatewege gehören zur laufenden Abnahme.
- **FHEM bleibt die Geräteanbindung:** Verfügbare Befehle und Readings hängen von dessen Modulen und Gerätekonfiguration ab.
- **Keine garantierte Geräterückmeldung:** Insbesondere einseitige Funkprotokolle liefern nicht zwingend einen bestätigten Schaltzustand oder eine Position.
- **Nicht jedes FHEMWEB-Widget ist in HA nachgebildet:** Fremdes FHEMWEB-JavaScript wird nicht ausgeführt.
- **Nicht blockierende Übertragung ist keine asynchrone Geräteausführung:** TLS-Sockets werden nicht blockierend verarbeitet. Die eigentlichen FHEM-Gerätebefehle und Attributfunktionen laufen wie native FHEM-Aufrufe in dessen Hauptschleife.
- **Keine automatische Automationsmigration:** FHEM-Regeln müssen fachlich nach HA übertragen und geprüft werden.

## Fehler melden

Für einen Fehlerbericht im [Issue-Tracker](https://github.com/piposa/ha-fhem-bridge/issues) bitte angeben:

- HA-Version sowie Versionen von Integration und geladenem HABridge-Modul.
- Betroffene FHEM-Modultypen und Modelle.
- Die ausgeführte Aktion, erwartetes Ergebnis und tatsächliches Verhalten.
- Zeitpunkt und passende Diagnosemeldungen.

Keine Secrets, Zertifikatschlüssel oder vollständigen privaten FHEM-Konfigurationen veröffentlichen. Für Quellen und Lizenzbedingungen mitgelieferter Bibliotheken siehe [Fremdcode und Hinweise](THIRD_PARTY_NOTICES.md).

---

<sub>[MIT-Lizenz](LICENSE) · Mit Unterstützung von OpenAI Codex entwickelt.</sub>
