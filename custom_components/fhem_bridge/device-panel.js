const weekDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const words = {
  de: {
    loading: "Gerät wird geladen …", missing: "Öffne dieses Gerät über die HA-Geräteseite.",
    back: "Zurück zum Gerät", integration: "Zur FHEM Bridge", refresh: "Aktualisieren", set: "Steuern", get: "Abfragen",
    attr: "Attribute", search: "Suchen …", choose: "Auswählen …", run: "Ausführen",
    save: "Speichern", remove: "Entfernen", used: "Gesetzt", unused: "Hinzufügen",
    noItems: "Keine Einträge gefunden.", denied: "Ausführen gesperrt. In den Geräteoptionen freigeben.",
    upgrade: "Für vollständige Bedienung 98_HABridge.pm aktualisieren.",
    automation: "Für Automation verwenden", script: "Als HA-Skript speichern",
    existingScripts: "Vorhandene HA-Skripte", loadingScripts: "Skripte werden geladen …",
    noScripts: "Für dieses Gerät gibt es noch keine HA-Skripte mit einem FHEM-Befehl.",
    scriptsFailed: "Vorhandene Skripte konnten nicht geladen werden.",
    variableScript: "Variable Eingaben", fixedScript: "Feste Argumente", noScriptArgs: "Ohne Argumente",
    scriptName: "Name des HA-Skripts", copied: "Aktionsblock kopiert.", copy: "YAML kopieren",
    accepted: "Von FHEM angenommen.", saved: "HA-Skript gespeichert. Es erscheint nach dem Neuladen im Automationseditor.",
    arg: "Argument", add: "Argument hinzufügen", seconds: "Dauer in Sekunden",
    percent: "Pegel in Prozent", hold: "Haltezeit in Sekunden", ramp: "Rampenzeit in Sekunden",
    temperature: "Solltemperatur in °C", gap: "Optionale Argumente von links nach rechts ausfüllen.",
    confirm: "Attribut wirklich entfernen?", current: "Aktueller Wert",
    technical: "Technischer Befehl. Technische Freigabe in den Geräteoptionen erforderlich.",
    truncated: "Ausgabe gekürzt.",
    getOutput: "Get-Ausgabe", setOutput: "Set-Rückmeldung",
    noGetOutput: "FHEM hat die Abfrage angenommen und keinen Text zurückgegeben.",
    publish: "HA-Geräteseite gestalten", reading: "Readings", objects: "Veröffentlichte Befehle",
    publishHelp: "Hier legst du fest, welche Readings und Bedienelemente auf der HA-Geräteseite erscheinen.",
    operate: "FHEM bedienen", operateHelp: "Führe Befehle direkt aus. Mit „Auf Geräteseite hinzufügen“ merkst du ein Bedienelement für HA vor.",
    attributeHelp: "Hier liest und änderst du die Attribute des FHEM-Kanals.",
    scope: "Geltungsbereich", device: "Nur dieses Gerät", class: "Geräteklasse", type: "Alle dieses TYPE",
    future: "Auch später aufgenommene Geräte", commit: "Änderungen übernehmen",
    staged: "In Auswahl übernommen", changes: "Änderungen", reset: "Vorlagenwert verwenden",
    sensor: "Messwert", binary: "Binärsensor", diagnostic: "Diagnose", hidden: "Ausgeblendet",
    internal: "Nur intern", off: "Nicht übernehmen", button: "Button mit festen Argumenten",
    form: "Eingabefelder und Senden auf der Geräteseite", box: "Zahlenfeld", slider: "Schieberegler",
    direct: "Ein Feld · Wert direkt senden",
    number_slider: "Schieberegler mit Rückmeldung",
    rawArgs: "Rohargumente eingeben", inputCount: "Anzahl der Argumentfelder",
    minValue: "Minimum", maxValue: "Maximum", stepValue: "Schrittweite", optionValues: "Ein Wert pro Zeile",
    scriptInputs: "Skript mit variablen Eingaben anlegen",
    observeReading: "Späteres Reading beobachten (optional)",
    localInputs: "Werte werden in HA eingegeben. Erst der Senden-Knopf führt den Befehl aus.",
    directInput: "Beim Bestätigen des Felds wird der FHEM-Befehl ausgeführt.",
    startDate: "Startdatum", startTime: "Startzeit", endDate: "Enddatum", endTime: "Endzeit",
    channel: "FHEM-Kanal", discardDraft: "Ungespeicherte Änderungen beim Kanalwechsel verwerfen?",
    readingFilter: "Anzeigeart filtern", allModes: "Alle Anzeigearten",
    readingHelp: "Ausgeblendet bleibt als HA-Entität nutzbar. Nur intern überträgt das Reading ohne Entität. Nicht übernehmen lässt es weg, sofern kein Bedienelement die Rückmeldung benötigt.",
    select: "Auswahlliste", number: "Zahlenfeld", text: "Textfeld", label: "Name auf der Geräteseite",
    variant: "Zusätzliche Variante", template: "Gespeicherte Anpassung", newRule: "Neue Anpassung",
    applyDone: "Auswahl gespeichert. Die Geräteseite ist aktualisiert.",
    applying: "Auswahl wird gespeichert. Die Bridge verbindet sich anschließend neu.",
    reloadFailed: "Auswahl gespeichert. Die Bridge konnte nicht geladen werden. Prüfe den Integrationseintrag und lade ihn erneut.",
    refreshFailed: "Auswahl gespeichert. Öffne die Gerätekonfiguration erneut, um den aktuellen Stand zu sehen.",
    allFiltered: "Auf alle gefilterten Readings anwenden", pending: "Ungespeicherte Änderungen an der HA-Geräteseite",
    pendingItem: "Vorgemerkt", pendingRemoval: "Zum Entfernen vorgemerkt", savedLayout: "Keine ungespeicherten Änderungen",
    review: "Änderungen prüfen", discard: "Verwerfen",
    pin: "Auf Geräteseite hinzufügen", emptyDraft: "Wähle zuerst ein Reading oder einen Befehl aus.",
    hiddenState: "Auf Geräteseite ausblenden", edit: "Bearbeiten", requiredReading: "Rückmeldung für Bedienelement", feedback: "Reading für Rückmeldung",
    diagnostics: "Diagnosedaten herunterladen",
    deviceOptions: "Geräteoptionen", writable: "Steuern erlauben (Set)", query: "Get-Abfragen erlauben",
    edit_attributes: "Attribute ändern erlauben", technicalOption: "Technische Befehle erlauben",
    subscribeLogs: "FHEM-Protokolle abonnieren", cancel: "Abbrechen",
    locked: "Gesperrt",
    permissionsSaved: "Geräteoptionen gespeichert. Die Bridge wird neu geladen.",
    readOnlyHelp: "Readings und Bedienelemente lassen sich gestalten. Gesperrte Befehle werden erst nach Freigabe ausführbar.",
    deleteRule: "Anpassung entfernen", copySelection: "Aktuelle Geräteauswahl übernehmen",
    week: "Wochenplan", loadWeek: "Wochenplan aus FHEM lesen", saveWeek: "Wochenplan speichern",
    dayTemp: "Komforttemperatur", nightTemp: "Absenktemperatur", disableWindow: "Fenster deaktivieren",
    copyDay: "Tag kopieren nach …", addInterval: "Zeitabschnitt teilen",
    scheduleFht: "Zwei Komfortfenster pro Tag. 24:00 deaktiviert ein Fenster. Zeiten im 10-Minuten-Raster.",
    scheduleHm: "Bis zu 13 Abschnitte je Tag. Zeiten im 5-Minuten-Raster. Die letzte Endzeit ist 24:00.",
    scheduleReadOnly: "Zum Bearbeiten ist die Set-Freigabe erforderlich.",
    scheduleDraft: "FHEM meldet keinen vollständigen, bestätigten Wochenplan. Ergänze den Entwurf vor dem Speichern.",
    scheduleReplace: "Den vollständigen Entwurf an FHEM senden? Er ersetzt den Wochenplan am Thermostat.",
    scheduleReported: "Angezeigt wird der letzte in FHEM vorliegende Plan.",
    scheduleAccepted: "FHEM hat die Änderungen zum Senden angenommen. Lies den Plan nach der Funkübertragung erneut.",
    schedulePending: "Der zuletzt gesendete Plan ist in den FHEM-Readings noch nicht angekommen.",
    scheduleReload: "Wochenplan neu lesen und Entwurf verwerfen?", scheduleUnchanged: "Keine Änderung zu speichern.",
  },
  en: {
    loading: "Loading device …", missing: "Open this device from its Home Assistant device page.",
    back: "Back to device", integration: "Open FHEM Bridge", refresh: "Refresh", set: "Control", get: "Queries",
    attr: "Attributes", search: "Search …", choose: "Select …", run: "Run",
    save: "Save", remove: "Remove", used: "Configured", unused: "Add",
    noItems: "No items found.", denied: "Allow this operation for the device in bridge options.",
    upgrade: "Update 98_HABridge.pm for full device controls.",
    automation: "Use in automation", script: "Save as HA script", scriptName: "HA script name",
    existingScripts: "Existing HA scripts", loadingScripts: "Loading scripts …",
    noScripts: "No HA scripts with a FHEM command for this device.",
    scriptsFailed: "Could not load existing scripts.",
    variableScript: "Variable inputs", fixedScript: "Fixed arguments", noScriptArgs: "No arguments",
    copied: "Action copied.", copy: "Copy YAML", accepted: "Accepted by FHEM.",
    saved: "HA script saved. It will appear in the automation editor after scripts reload.",
    arg: "Argument", add: "Add argument", seconds: "Duration in seconds", percent: "Level in percent",
    hold: "Hold time in seconds", ramp: "Ramp time in seconds", temperature: "Target temperature in °C",
    gap: "Fill optional arguments from left to right.", confirm: "Remove this attribute?",
    current: "Current value", technical: "Enable technical commands for this device in bridge options.",
    truncated: "Output truncated.",
    getOutput: "Get output", setOutput: "Set feedback",
    noGetOutput: "FHEM accepted the request and returned no text.",
    publish: "Customize HA device page", reading: "Readings", objects: "Published commands",
    publishHelp: "Choose which readings and controls appear on the HA device page.",
    operate: "Operate FHEM", operateHelp: "Run commands directly. Use “Add to device page” to queue a control for HA.",
    attributeHelp: "Read and edit the FHEM channel’s attributes here.",
    scope: "Scope", device: "This device only", class: "Device class", type: "All of this TYPE",
    future: "Include devices added later", commit: "Apply changes",
    staged: "Added to selection", changes: "changes", reset: "Use inherited setting",
    sensor: "Measurement", binary: "Binary sensor", diagnostic: "Diagnostic", hidden: "Hidden",
    internal: "Internal only", off: "Do not import", button: "Button with fixed arguments",
    form: "Inputs and send button on the device page", box: "Number field", slider: "Slider",
    direct: "One field · send value directly",
    number_slider: "Slider with feedback",
    rawArgs: "Enter raw arguments", inputCount: "Number of argument fields",
    minValue: "Minimum", maxValue: "Maximum", stepValue: "Step", optionValues: "One option per line",
    scriptInputs: "Create script with variable inputs",
    observeReading: "Observe a later reading (optional)",
    localInputs: "Enter values in HA. Only the send button executes the command.",
    directInput: "Confirming the field executes the FHEM command.",
    startDate: "Start date", startTime: "Start time", endDate: "End date", endTime: "End time",
    channel: "FHEM channel", discardDraft: "Discard unsaved changes before switching channels?",
    readingFilter: "Filter by visibility", allModes: "All visibility modes",
    readingHelp: "Hidden keeps a usable HA entity. Internal only receives the reading without an entity. Do not import skips it unless it is needed as feedback.",
    select: "Selection", number: "Number field", text: "Text field", label: "Name on device page",
    variant: "Additional variant", template: "Saved customization", newRule: "New customization",
    applyDone: "Selection saved and device page updated.",
    applying: "Saving selection. The bridge will reconnect afterward.",
    reloadFailed: "Selection saved. The bridge could not be loaded. Check the integration entry and reload it.",
    refreshFailed: "Selection saved. Reopen device configuration to see the current settings.",
    allFiltered: "Apply to all filtered readings", pending: "Unsaved changes to the HA device page",
    pendingItem: "Pending", pendingRemoval: "Pending removal", savedLayout: "No unsaved changes",
    review: "Review changes", discard: "Discard",
    pin: "Add to device page", emptyDraft: "Select a reading or command first.",
    hiddenState: "Hide on device page", edit: "Edit", requiredReading: "Feedback used by a control", feedback: "Feedback reading",
    diagnostics: "Download diagnostics",
    deviceOptions: "Device options", writable: "Allow control (Set)", query: "Allow Get queries",
    edit_attributes: "Allow attribute changes", technicalOption: "Allow technical commands",
    subscribeLogs: "Subscribe to FHEM logs", cancel: "Cancel",
    locked: "Blocked",
    permissionsSaved: "Device options saved. The bridge is reloading.",
    readOnlyHelp: "Configure readings and controls here. Blocked commands become executable after permission is granted.",
    deleteRule: "Remove customization", copySelection: "Copy current device selection",
    week: "Weekly schedule", loadWeek: "Read schedule from FHEM", saveWeek: "Save weekly schedule",
    dayTemp: "Comfort temperature", nightTemp: "Setback temperature", disableWindow: "Disable window",
    copyDay: "Copy day to …", addInterval: "Split interval",
    scheduleFht: "Two comfort windows per day. 24:00 disables a window. Times use 10-minute increments.",
    scheduleHm: "Up to 13 intervals per day, in 5-minute increments. The final end time is 24:00.",
    scheduleReadOnly: "Editing requires Set permission.",
    scheduleDraft: "FHEM has no complete, confirmed schedule. Complete this draft before saving.",
    scheduleReplace: "Send the complete draft to FHEM? It replaces the schedule on the thermostat.",
    scheduleReported: "This is the last schedule reported in FHEM.",
    scheduleAccepted: "FHEM accepted the changes for transmission. Read the schedule again after radio transmission.",
    schedulePending: "The last requested schedule has not appeared in the FHEM readings yet.",
    scheduleReload: "Read the schedule again and discard the draft?", scheduleUnchanged: "No changes to save.",
  },
};

function uniqueId() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)),
    (byte) => byte.toString(16).padStart(2, "0")).join("");
}

const attributeEditorAssets = "/fhem_bridge_panel/codemirror-5.65.13/";
let attributeEditorLoader;

function loadAttributeEditor() {
  attributeEditorLoader ??= (async () => {
    await import(attributeEditorAssets + "codemirror.js");
    await Promise.all(["perl.js", "matchbrackets.js", "searchcursor.js"].map((name) =>
      import(attributeEditorAssets + name)));
    return globalThis.CodeMirror;
  })().catch((error) => {
    attributeEditorLoader = undefined;
    throw error;
  });
  return attributeEditorLoader;
}

class FhemBridgeDevicePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode: "open"});
  }

  set hass(value) {
    this._hass = value;
    this.openDevice();
  }

  set route(value) {
    this._route = value;
    this.openDevice();
  }

  connectedCallback() {
    this.openDevice();
    this._focusRefresh = () => { if (this.data && this.isConnected && !new URLSearchParams(window.location.search).has("attributes")) void this.load(); };
    window.addEventListener("focus", this._focusRefresh);
  }

  disconnectedCallback() {
    window.removeEventListener("focus", this._focusRefresh);
  }

  get labels() {
    return this._hass?.locale?.language?.startsWith("de") ? words.de : words.en;
  }

  node(tag, text, parent) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    parent?.append(element);
    return element;
  }

  button(label, parent, handler) {
    const button = this.node("button", label, parent);
    button.type = "button";
    button.addEventListener("click", handler);
    return button;
  }

  openDevice() {
    if (!this.isConnected || !this._hass || this.importDialog) return;
    const params = new URLSearchParams(window.location.search);
    const bridge = params.get("bridge");
    const route = window.location.search;
    if (bridge && !params.has("device")) {
      if (this._locationSearch === route) return;
      this._locationSearch = route;
      this.bridgeEntry = bridge;
      this.configView = params.has("config");
      this.data = null;
      this.libraryData = null;
      this.libraryError = "";
      this.render();
      if (!this.configView) void this.loadLibrary();
      return;
    }
    const identifier = params.get("device");
    const device = Object.values(this._hass.devices ?? {}).find(
      (item) => item.identifiers?.some(([domain, id]) => domain === "fhem_bridge" && id === identifier)
    );
    const deviceId = device?.id;
    if (this._initialized && this._locationSearch === route && this.deviceId === deviceId) return;
    this._locationSearch = route;
    this.bridgeEntry = null;
    this.attributeDraftDirty = false;
    this.identifier = identifier;
    this._initialized = true;
    this.deviceId = deviceId;
    this.source = params.get("reference");
    this.data = null;
    this.commandResult = null;
    this.commandRequest = null;
    this.selection = {};
    this.schedule = null;
    this.scheduleRequest = null;
    this.publication = null;
    this.draft = new Map();
    this.templateDraft = null;
    this.deviceTab = "template";
    this.commandEditor = null;
    this.scope = "device";
    this.publicationMode = params.get("editor") === "1" ? "editor" : params.has("assign") ? "assignment" : "adjustment";
    this.assignOnLoad = params.get("assign");
    this.templateId = this.publicationMode === "editor" ? params.get("template") ?? "" : "";
    this.templateDisabled = false;
    this.targets = [];
    this.ruleId = null;
    this.future = false;
    this.render();
    if (deviceId) void this.load();
  }

  async request(op, fields = {}) {
    return this._hass.callWS({type: "fhem_bridge/device", ...this.deviceTarget, op, ...fields});
  }

  get deviceTarget() {
    return {device_id: this.deviceId, ...(this.source ? {source: this.source} : {})};
  }

  get targetKey() {
    return JSON.stringify(this.deviceTarget);
  }

  async load(refresh = false) {
    const target = this.targetKey;
    try {
      const result = await this.request("describe", {refresh});
      if (this.targetKey !== target) return;
      this.data = result;
      this.render();
      if (new URLSearchParams(window.location.search).has("attributes")) {
        // Fetch publication choices only when the user returns to customization.
        return true;
      }
      const publication = await this.publishRequest("list");
      if (this.targetKey !== target) return;
      if (!this.publication) {
        this.ruleId = this.matchingPublicationRules(publication)[0]?.id ?? null;
        this.future = publication.rules.find((rule) => rule.id === this.ruleId)?.future ?? (this.scope !== "device");
      }
      this.publication = publication;
      if (this.publicationMode === "editor") {
        location.replace(this.libraryLink(this.templateId, publication.bridge_entry_id));
        return;
      }
      if (this.assignOnLoad && publication.templates[this.assignOnLoad]) {
        this.templateId = this.assignOnLoad;
        this.assignOnLoad = null;
        this.templateDraft = {key: this.templateId, disabled: false};
      }
      this.render();
      return true;
    } catch (error) {
      if (this.targetKey === target) this.show(error.message ?? String(error), true);
    }
  }

  show(message, error = false) {
    if (!this.notice) return;
    this.notice.textContent = message;
    this.notice.classList.toggle("error", error);
  }

  renderCommandResult() {
    const result = this.commandResult;
    const {output, title, text} = this.commandOutput;
    output.hidden = !result || result.target !== this.targetKey;
    if (output.hidden) return;
    title.textContent = result.title;
    text.textContent = result.message;
    text.classList.toggle("error", result.error);
  }

  render() {
    const t = this.labels;
    this.closeAttributeFullscreen?.();
    this.refreshCommandScripts = null;
    this.shadowRoot.replaceChildren();
    if (new URLSearchParams(window.location.search).has("attributes")) {
      const css = this.node("link", undefined, this.shadowRoot);
      css.rel = "stylesheet";
      css.href = attributeEditorAssets + "codemirror.css";
    }
    this.node("style", `
      :host { display:block; color:var(--primary-text-color); font:inherit }
      main { max-width:760px; padding:20px; margin:auto }
      .import-modal { max-width:none; padding:0 }
      .import-modal h1 { margin:0 0 14px; font-size:1.5rem }
      header, .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap }
      header h1 { flex:1; margin:0; font-size:1.65rem }
      a { color:var(--primary-color) }
      details { border:1px solid var(--divider-color); border-radius:12px; margin:12px 0; padding:12px }
      summary { cursor:pointer; font-size:1.1em; font-weight:600 }
      .form { display:grid; gap:8px; margin:12px 0 }
      .form [hidden] { display:none }
      .view-tabs { display:flex; gap:12px; flex-wrap:wrap; margin:12px 0; border-bottom:1px solid var(--divider-color) }
      .view-tabs > * { padding:9px 6px; border:0; border-radius:0; background:none; color:inherit; text-decoration:none }
      .view-tabs [aria-current="page"], .view-tabs [aria-pressed="true"] {
        border-bottom:3px solid var(--primary-color); color:var(--primary-text-color); font-weight:700 }
      .view-tabs a:hover, .view-tabs button:hover { text-decoration:underline }
      .section-heading { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap }
      .editor-card { border:1px solid var(--divider-color); border-radius:12px; padding:16px; margin:14px 0 }
      .commands-table { width:100%; border-collapse:collapse; margin-bottom:16px; text-align:left }
      .commands-table td, .commands-table th { padding:10px 8px; border-bottom:1px solid var(--divider-color); vertical-align:top }
      .commands-table td { overflow-wrap:anywhere }
      .commands-table th { font-size:.85em; color:var(--secondary-text-color) }
      .command-scripts { margin:12px 0 }
      .command-scripts h2 { margin:0 0 4px }
      .command-scripts-list { list-style:none; margin:0; padding:0 }
      .command-scripts-list li { padding:8px 0; border-bottom:1px solid var(--divider-color); overflow-wrap:anywhere }
      .command-scripts-list small { display:block; color:var(--secondary-text-color) }
      .command-code { font-family:var(--code-font-family, monospace); font-size:.9em }
      .edit-name { border:0; background:none; padding:0; color:var(--primary-text-color); text-decoration:underline; font-weight:600; text-align:left }
      :focus-visible { outline:2px solid var(--primary-color); outline-offset:3px }
      .reading-row { display:grid; grid-template-columns:minmax(8em,1fr) minmax(8em,1fr) minmax(6em,1fr);
        gap:12px; align-items:center; border-bottom:1px solid var(--divider-color); padding:8px 0 }
      .attr-row { display:grid; grid-template-columns:minmax(8em,1fr) minmax(0,3fr); gap:14px;
        align-items:start; border-bottom:1px solid var(--divider-color); padding:10px 4px }
      .attr-row .edit-name { overflow-wrap:anywhere }
      .attr-value { text-align:left; white-space:pre-wrap; overflow-wrap:anywhere; margin:0 0 6px;
        font:inherit; font-family:var(--code-font-family,monospace) }
      .attribute-workspace { display:grid; grid-template-columns:minmax(0,1fr); min-width:0; gap:10px }
      .attribute-tools input[type=search] { flex:1 1 12em; width:auto; min-width:0 }
      main.attribute-page { max-width:none }
      main.attribute-page > :not(.attribute-editor) { max-width:760px; margin-inline:auto }
      .attribute-editor { min-width:0 }
      .attribute-editor .form { grid-template-columns:minmax(0,1fr); min-width:0 }
      .attribute-editor h3 { margin:0 }
      dialog.attribute-fullscreen {
        box-sizing:border-box; width:100vw; height:100dvh; max-width:none; max-height:none;
        margin:0; padding:clamp(12px, 2vw, 24px); border-radius:0; overscroll-behavior:contain }
      .attribute-fullscreen .attribute-editor { margin:0; border:0; padding:0 }
      .attribute-code { min-width:0; border:1px solid var(--divider-color); border-radius:6px; overflow:hidden }
      .attribute-code > textarea { display:block; width:100%; resize:vertical; font-family:monospace }
      .attribute-code > textarea, .attribute-code .CodeMirror-scroll { overscroll-behavior:contain }
      .attribute-fullscreen .attribute-code > textarea { height:calc(100dvh - 13rem) }
      .attribute-code .CodeMirror { height:clamp(12em, 48dvh, 35em); font: .95rem/1.5 monospace;
        color:var(--primary-text-color); background:var(--card-background-color) }
      .attribute-fullscreen .attribute-code .CodeMirror { height:calc(100dvh - 13rem); min-height:8em }
      .attribute-code .CodeMirror-gutters { color:var(--secondary-text-color); background:var(--secondary-background-color);
        border-color:var(--divider-color) }
      .attribute-code .CodeMirror-cursor { border-color:var(--primary-text-color) }
      .attribute-code .cm-keyword, .attribute-code .cm-def { color:var(--primary-text-color); font-weight:700 }
      .attribute-code .cm-string, .attribute-code .cm-string-2 { color:var(--success-color, #248041) }
      .attribute-code .cm-number, .attribute-code .cm-atom, .attribute-code .cm-builtin,
      .attribute-code .cm-variable-2, .attribute-code .cm-variable-3 { color:var(--primary-color) }
      .attribute-code .cm-comment, .attribute-eol { color:var(--secondary-text-color) }
      .attribute-eol { user-select:none }
      .attribute-code .CodeMirror-matchingbracket { color:inherit; background:var(--divider-color); outline:1px solid var(--primary-color) }
      .attribute-code .CodeMirror-nonmatchingbracket { color:var(--error-color); text-decoration:underline }
      @media(max-width:600px) { .attr-row { grid-template-columns:1fr; gap:4px } }
      .reading-headings { color:var(--secondary-text-color); font-size:.88em }
      .setting-origin { display:flex; gap:6px; flex-wrap:wrap; align-items:center }
      .setting-origin button { padding:4px 6px }
      dialog { max-width:min(520px, 94vw); padding:20px; border:1px solid var(--divider-color);
        border-radius:12px; color:inherit; background:var(--card-background-color) }
      fieldset .row input:is([type="checkbox"],[type="radio"]) { width:auto }
      .reading-metadata { grid-column:1/-1; min-width:0 }
      .reading-metadata summary { width:fit-content; cursor:pointer; color:var(--secondary-text-color) }
      .reading-metadata .row { align-items:end; margin:8px 0 0 }
      .reading-row small { display:block; color:var(--secondary-text-color) }
      .draft-badge { display:inline-block; margin-left:5px; color:var(--warning-color, #a86700); font-size:.85em }
      @media(max-width:600px) {
        .reading-row { grid-template-columns:1fr 1fr }
        .commands-table, .commands-table tbody { display:block }
        .commands-table thead { position:absolute; inline-size:1px; block-size:1px; overflow:hidden; clip-path:inset(50%) }
        .commands-table tr { display:grid; grid-template-columns:1fr 1fr; padding:8px 0; border-bottom:1px solid var(--divider-color) }
        .commands-table td { display:block; border:0; padding:3px 6px }
        .commands-table td:first-child, .commands-table .command-code { grid-column:1 / -1 }
        .commands-table td[data-label]:not(.command-code)::before { content:attr(data-label) " · "; color:var(--secondary-text-color) }
      }
      label { display:grid; gap:4px }
      input, select, textarea, button {
        box-sizing:border-box; color:inherit; font:inherit; padding:8px;
        background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:6px;
      }
      input,select,textarea { width:100% }
      button { cursor:pointer } button:disabled { cursor:default; opacity:.55 }
      .attribute-tools button[aria-pressed="true"] {
        background:var(--primary-color); color:var(--text-primary-color,white);
        border-color:var(--primary-color); font-weight:600 }
      .attribute-tools button[aria-pressed="true"]::before { content:"✓ "; }
      button.primary { background:var(--primary-color); color:var(--text-primary-color,white) }
      .import-toolbar, .import-footer { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin:12px 0 }
      .import-toolbar input[type="search"] { flex:1 1 14em; min-width:0; width:auto }
      .import-filters { display:grid; grid-template-columns:repeat(auto-fit,minmax(9em,1fr)); gap:8px }
      .import-filters details { max-height:15em; overflow:auto; margin:0 }
      .import-check { display:flex; align-items:center; gap:8px; padding:4px 0; cursor:pointer }
      .import-check input { width:auto; flex-shrink:0 }
      .import-check span { min-width:0; overflow-wrap:anywhere }
      .import-list { max-height:52vh; overflow:auto; border-block:1px solid var(--divider-color); overflow-anchor:none }
      .import-list.group-list { max-height:none; overflow:visible }
      .import-item { padding:7px 10px; border-bottom:1px solid var(--divider-color) }
      .import-item:nth-child(even) { background:var(--secondary-background-color) }
      .import-item small { display:block; color:var(--secondary-text-color) }
      .import-item details { margin:2px 0 4px 24px; padding:4px 8px }
      .import-item summary { font-size:.9em }
      .import-assignment { display:grid; gap:8px; margin:12px 0; border:1px solid var(--divider-color); border-radius:8px }
      .import-assignment details { margin:0 }
      .import-footer { justify-content:space-between }
      .import-footer .primary { margin-inline-start:auto }
      .message { white-space:pre-wrap; overflow-wrap:anywhere }
      .command-output { margin:12px 0; padding:12px; border-radius:8px;
        border:1px solid var(--divider-color); background:var(--card-background-color) }
      .command-output h2 { margin:0 0 6px; font-size:1rem }
      .command-output p { margin:0; max-height:30vh; overflow:auto }
      .change-bar { padding:12px; border-radius:10px;
        background:var(--card-background-color, var(--primary-background-color, white));
        border:1px solid var(--divider-color) }
      .change-bar[data-pending], .change-bar:has(.change-preview:not(:empty)) {
        position:sticky; bottom:0; z-index:1; border:2px solid var(--warning-color, #a86700) }
      .change-bar [role="status"] { flex:1 }
      .change-preview:not(:empty) { display:grid; gap:8px; margin-top:8px }
      .change-preview > ul { margin:0; max-height:25vh; overflow:auto }
      .pending-item:not([hidden]) { display:inline-block; font-weight:600; border-inline-start:3px solid
        var(--warning-color, #a86700); padding-inline-start:8px }
      .error { color:var(--error-color) }
      [hidden] { display:none !important }
      textarea:not(.attribute-code textarea) { min-height:6em }
      dialog { color:inherit; background:var(--card-background-color); border:1px solid var(--divider-color);
        border-radius:12px; max-width:680px; max-height:85vh; overflow:auto }
      dialog input[type=checkbox] { width:auto }
      dialog .permission { display:flex; align-items:center; gap:8px; margin:10px 0 }
      .week-row { display:grid; grid-template-columns:repeat(2,minmax(5em,1fr)) auto; gap:8px;
        align-items:end; margin:8px 0 }
      .timeline { display:flex; height:10px; gap:1px; background:var(--divider-color); margin:10px 0 }
      .timeline span { min-width:0; background:var(--primary-color) }
      .timeline span:nth-child(even) { background:var(--accent-color, var(--primary-color)) }
    `, this.shadowRoot);
    const main = this.node("main", undefined, this.shadowRoot);
    if (this.importDialog) {
      main.className = "import-modal";
      void this.importPanel(main, this.importDialog.entryId);
      return;
    }
    if (this.bridgeEntry) {
      if (this.configView) {
        const de = this._hass.locale?.language?.startsWith("de");
        this.node("a", this.labels.integration, main).href = "/config/integrations/integration/fhem_bridge";
        this.node("h1", de ? "FHEM-Konfiguration" : "FHEM configuration", main);
        void this.configurationPanel(this.node("div", undefined, main), this.bridgeEntry);
      } else this.renderLibrary(main);
      return;
    }
    if (!this.deviceId) {
      this.node("p", t.missing, main);
      return;
    }
    const links = this.node("nav", undefined, main);
    links.className = "row";
    const editor = this.publicationMode === "editor";
    const de = this._hass.locale?.language?.startsWith("de");
    const back = this.node("a", editor ? (de ? "Zurück zu Vorlagen" : "Back to templates") : t.back, links);
    const devicePath = "/config/devices/device/" + encodeURIComponent(this.deviceId);
    back.href = editor && this.publication ? this.libraryLink(this.templateId, this.publication.bridge_entry_id) : devicePath;
    back.addEventListener("click", (event) => {
      if (editor || event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      const fromDevice = [history.state?.from, document.referrer].some((previous) => {
        if (typeof previous !== "string" || !previous) return false;
        const url = new URL(previous, location.origin);
        return url.origin === location.origin && url.pathname === devicePath;
      });
      if (fromDevice) {
        history.back();
        return;
      }
      history.replaceState(history.state, "", devicePath);
      window.dispatchEvent(new CustomEvent("location-changed", {detail: {replace: true}}));
    });
    const integration = this.node("a", t.integration, links);
    integration.href = "/config/integrations/integration/fhem_bridge";
    const header = this.node("header", undefined, main);
    this.node("h1", this.data?.name ?? "FHEM", header);
    this.button(t.refresh, header, () => {
      if (this.attributeDraftDirty && !window.confirm(t.discardDraft)) return;
      this.attributeDraftDirty = false;
      void this.load(true);
    });

    this.button(t.diagnostics, header, async () => {
      try {
        const data = await this._hass.callWS({type: "fhem_bridge/diagnostics", ...this.deviceTarget});
        const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type: "application/json"}));
        const link = this.node("a", undefined, this.shadowRoot);
        link.href = url;
        link.download = "fhem-device-diagnostics.json";
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      } catch (error) {
        this.show(error.message ?? String(error), true);
      }
    });
    this.notice = this.node("p", this.data ? "" : t.loading, main);
    this.notice.className = "message";
    this.notice.setAttribute("role", "status");
    if (!this.data) return;
    const output = this.node("section", undefined, main);
    output.className = "command-output";
    output.hidden = true;
    output.setAttribute("role", "status");
    const outputTitle = this.node("h2", "", output);
    const outputText = this.node("p", "", output);
    outputText.className = "message";
    this.commandOutput = {output, title: outputTitle, text: outputText};
    this.renderCommandResult();
    const params = new URLSearchParams(location.search);
    const showDetails = params.has("attributes") ? "attributes" : params.has("details");
    this.deviceViews(main, showDetails);
    if (this.data.sources?.length > 1) {
      const picker = this.node("select", undefined, this.node("label", t.channel, main));
      for (const source of this.data.sources) this.node("option", source.name, picker).value = source.id;
      picker.value = this.data.source;
      picker.addEventListener("change", () => {
        if ((this.draft.size || this.templateDraft || this.attributeDraftDirty) && !window.confirm(t.discardDraft)) {
          picker.value = this.data.source;
          return;
        }
        this.attributeDraftDirty = false;
        this.source = picker.value;
        this.data = null;
        this.commandResult = null;
        this.commandRequest = null;
        this.publication = null;
        this.selection = {};
        this.draft.clear();
        this.templateDraft = null;
        this.commandEditor = null;
        this.scope = "device";
        this.publicationMode = "adjustment";
        this.templateId = "";
        this.targets = [];
        this.ruleId = null;
        this.future = false;
        this.render();
        void this.load();
      });
    }
    this.node("p", [this.data.type, this.data.model].filter(Boolean).join(" · "), main);
    if (!this.data.enhanced) this.node("p", t.upgrade, main);
    if (showDetails === "attributes") {
      main.classList.add("attribute-page");
      void this.attributePanel(main);
    } else if (showDetails) {
      this.commandScripts(main);
      if (this.data.sources?.some((source) => source.schedule)) this.schedulePanel(main);
      this.node("h2", t.operate, main);
      for (const kind of ["set", "get"]) this.section(main, kind);
    } else if (this.publication) {
      this.publicationPanel(main);
      this.changeBar(main);
    }
  }

  prioritizeImportOptions(options, recent, key = (value) => value) {
    const ranks = new Map(recent.map((value, index) => [value, index]));
    return [...options].sort((a, b) => (ranks.get(key(a)) ?? Infinity) - (ranks.get(key(b)) ?? Infinity));
  }

  async importPanel(main, entryId) {
    const de = this._hass.locale?.language?.startsWith("de");
    const tr = (german, english) => de ? german : english;
    const bridgeUrl = "/config/integrations/integration/fhem_bridge";
    const api = (op, data = {}) => this._hass.callWS({type: "fhem_bridge/import", entry_id: entryId, op, ...data});
    const compare = (a, b) => a.localeCompare(b, this._hass.locale?.language);
    const make = (tag, value, parent) => this.node(tag, value, parent);
    const action = (text, parent, fn, primary = false) => {
      const button = this.button(text, parent, fn);
      if (primary) button.className = "primary";
      return button;
    };
    const link = (title, href, parent) => { make("a", title, parent).href = href; };
    const emptyFilters = () => ({
      rooms: new Set(), types: new Set(), models: new Set(), technical: false, individual: false, sort: "room",
    });
    const setTitle = this.importDialog?.setTitle;
    const title = setTitle ? null : make("h1", "", main);
    const body = make("div", undefined, main);
    const status = make("p", "", main);
    status.setAttribute("role", "status");
    status.className = "message";
    let catalog, definitions, groupBySource;
    let search = "", filters = emptyFilters(), filtersOpen = false, selectionOpen = false, scrollTop = 0;
    let destination;
    const selected = new Map();
    const assignments = new Map();
    const recentAreas = [], recentLabels = [];
    let assignmentWidgets = [];

    const showError = (error) => {
      status.textContent = error?.message ?? String(error);
      status.classList.add("error");
    };
    const show = (heading) => {
      this.importDialog?.setFooter?.(null);
      this.importDialog?.resetScroll?.();
      if (setTitle) setTitle(heading);
      else title.textContent = heading;
      body.replaceChildren();
      status.textContent = "";
      status.classList.remove("error");
    };
    const groupFooter = () => {
      const native = this.importDialog?.setFooter;
      const footer = make("div", undefined, native ? undefined : body);
      if (native) native(footer);
      else footer.className = "import-footer";
      return {footer, footerAction: (label, handler, primary = false) => {
        if (!native) return action(label, footer, handler, primary);
        const button = make("ha-button", label, footer);
        if (!primary) button.setAttribute("appearance", "plain");
        button.style.maxWidth = "100%";
        button.addEventListener("click", handler);
        return button;
      }};
    };
    const setCatalog = (result) => {
      catalog = result;
      definitions = new Map(result.definitions.map((item) => [item.id, item]));
      groupBySource = new Map(Object.entries(result.groups).flatMap(([key, group]) =>
        group.members.map((id) => [id, [key, group]])));
    };
    const payload = () => ({
      selected: Object.fromEntries([...selected].map(([key, item]) => [key, item.members])),
      room_hints: Object.fromEntries([...selected].map(([key, item]) => [key, item.roomHints])),
    });
    const deviceName = (item) => item.alias && item.alias !== item.name ? item.alias + " (" + item.name + ")" : item.name;
    const searchField = (parent, placeholder, value, update) => {
      const input = make("input", undefined, parent);
      input.type = "search";
      input.placeholder = placeholder;
      input.setAttribute("aria-label", placeholder);
      input.value = value;
      const clear = action("×", parent, () => {
        input.value = "";
        changed();
        input.focus();
      });
      clear.setAttribute("aria-label", tr("Suche leeren", "Clear search"));
      clear.disabled = !value;
      const changed = () => {
        clear.disabled = !input.value;
        update(input.value);
      };
      input.addEventListener("input", changed);
      return input;
    };
    const deviceRow = (parent, item, selected, change, {radio, address, note} = {}) => {
      const entry = make("div", undefined, parent);
      entry.className = "import-item";
      const label = make("label", undefined, entry);
      label.className = "import-check";
      const input = make("input", undefined, label);
      input.type = radio ? "radio" : "checkbox";
      if (radio) input.name = radio;
      input.value = item.id;
      input.checked = selected;
      const info = make("span", undefined, label);
      make("strong", deviceName(item), info);
      make("small", [item.type, item.model, address, item.rooms.join(", "), note].filter(Boolean).join(" · "), info);
      input.addEventListener("change", () => change(input));
      return entry;
    };
    const optionFor = (item) => {
      const grouped = !filters.individual && groupBySource.get(item.id);
      if (!grouped) return {key: item.id, item, members: [item.id]};
      const [key, group] = grouped;
      return {key, item: definitions.get(group.primary), members: group.members};
    };

    const picker = () => {
      show(tr("Geräte importieren", "Import devices"));
      const toolbar = make("div", undefined, body);
      toolbar.className = "import-toolbar";
      const searchInput = searchField(toolbar, tr("Name oder Alias suchen …", "Search name or alias …"), search, (value) => {
        search = value;
        draw(true);
      });
      const filterButton = action(tr("Filter", "Filters"), toolbar, () => {
        filtersOpen = !filtersOpen;
        filterPanel.hidden = !filtersOpen;
        filterButton.setAttribute("aria-expanded", String(filtersOpen));
      });
      filterButton.setAttribute("aria-expanded", String(filtersOpen));
      action(tr("Zur Bridge-Konfiguration", "Back to bridge configuration"), toolbar, () => this.importDialog?.close());
      link(tr("Zur Bridge-Übersicht", "Back to bridge overview"), bridgeUrl, toolbar);
      const filterPanel = make("div", undefined, body);
      filterPanel.className = "editor-card";
      filterPanel.hidden = !filtersOpen;
      const filterFields = make("div", undefined, filterPanel);
      filterFields.className = "import-filters";
      const row = (field, items, label) => {
        const dropdown = make("details", undefined, filterFields);
        const count = make("summary", label, dropdown);
        const update = () => {
          const chosen = items.filter(([id]) => filters[field].has(id)).map(([, name]) => name);
          count.textContent = [label, ...chosen].join(" · ");
        };
        for (const [id, name] of items) {
          const option = make("label", undefined, dropdown);
          option.className = "import-check";
          const checkbox = make("input", undefined, option);
          checkbox.type = "checkbox";
          checkbox.checked = filters[field].has(id);
          make("span", name, option);
          checkbox.addEventListener("change", () => {
            if (checkbox.checked) filters[field].add(id);
            else filters[field].delete(id);
            update();
            draw(true);
          });
        }
        update();
      };
      const values = (items) => [...new Set(items)].sort(compare).map((item) => [item, item]);
      row("rooms", [...values(catalog.definitions.flatMap((item) => item.rooms)),
        ["", tr("Ohne Raum", "No room")]], tr("Raum", "Room"));
      row("types", values(catalog.definitions.map((item) => item.type)), tr("FHEM-Modul", "FHEM module"));
      row("models", [...values(catalog.definitions.map((item) => item.model).filter(Boolean)),
        ["", tr("Ohne Modell", "No model")]], tr("Modell", "Model"));
      const extra = make("div", undefined, filterPanel);
      extra.className = "import-toolbar";
      for (const [field, text] of [["individual", tr("Kanäle einzeln anzeigen", "Show individual channels")],
        ["technical", tr("Technische Objekte anzeigen", "Show technical objects")]]) {
        const label = make("label", undefined, extra);
        label.className = "import-check";
        const checkbox = make("input", undefined, label);
        checkbox.type = "checkbox";
        checkbox.checked = filters[field];
        make("span", text, label);
        checkbox.addEventListener("change", () => { filters[field] = checkbox.checked; draw(true); });
      }
      const sort = make("select", undefined, make("label", tr("Sortieren nach", "Sort by"), extra));
      make("option", tr("Raum", "Room"), sort).value = "room";
      make("option", tr("Gerätetyp", "Device type"), sort).value = "type";
      sort.value = filters.sort;
      sort.addEventListener("change", () => { filters.sort = sort.value; draw(true); });
      action(tr("Filter zurücksetzen", "Reset filters"), extra, () => {
        filters = emptyFilters();
        scrollTop = 0;
        picker();
      });

      const count = make("p", "", body);
      count.setAttribute("aria-live", "polite");
      const tools = make("div", undefined, body);
      tools.className = "import-toolbar";
      const markAll = action("", tools, () => {
        const allMarked = results.every(({key}) => selected.has(key));
        for (const item of results) mark(item, !allMarked);
        draw();
      });
      const review = action(tr("Auswahl ansehen", "Review selection"), tools, () => {
        selectionOpen = !selectionOpen;
        draw(true);
      });
      const rows = make("div", undefined, body);
      rows.className = "import-list";
      rows.tabIndex = 0;
      rows.setAttribute("aria-label", tr("Geräteliste", "Device list"));
      rows.addEventListener("scroll", () => { scrollTop = rows.scrollTop; });
      const footer = make("div", undefined, body);
      footer.className = "import-footer";
      const next = action(tr("Weiter zu Bereichen und Labels →", "Continue to areas and labels →"), footer, async () => {
        next.disabled = true;
        body.inert = true;
        try {
          const result = await api("areas", payload());
          if (main.isConnected) areas(result);
        } catch (error) {
          if (main.isConnected) showError(error);
        } finally {
          body.inert = false;
          next.disabled = !selected.size;
        }
      }, true);
      let results = [];
      const mark = (item, checked) => {
        if (checked) {
          const members = new Set(item.members);
          for (const [key, current] of selected) {
            if (key !== item.key && current.members.some((member) => members.has(member))) selected.delete(key);
          }
          selected.set(item.key, {...item, roomHints: selected.get(item.key)?.roomHints ?? [...filters.rooms].filter(Boolean)});
        } else selected.delete(item.key);
      };
      const draw = (resetScroll = false) => {
        if (!selected.size) selectionOpen = false;
        const needle = search.trim().toLocaleLowerCase();
        const available = catalog.definitions.filter((item) => !item.installed &&
          (filters.technical || !item.technical) &&
          (!needle || [item.name, item.alias].some((value) => value?.toLocaleLowerCase().includes(needle))) &&
          (!filters.rooms.size || (item.rooms.length ? item.rooms : [""]).some((room) => filters.rooms.has(room))) &&
          (!filters.types.size || filters.types.has(item.type)) &&
          (!filters.models.size || filters.models.has(item.model ?? "")));
        results = [...new Map(available.map((item) => {
          const candidate = optionFor(item);
          return [candidate.key, candidate];
        })).values()].sort((a, b) => compare(
          filters.sort === "type" ? a.item.type : a.item.rooms.join(", "),
          filters.sort === "type" ? b.item.type : b.item.rooms.join(", "),
        ) || compare(deviceName(a.item), deviceName(b.item)));
        const marked = results.filter(({key}) => selected.has(key)).length;
        count.textContent = tr(
          `${results.length} verfügbare Geräte · ${selected.size} ausgewählt, davon ${marked} in der Trefferliste`,
          `${results.length} available devices · ${selected.size} selected, ${marked} in the results`,
        );
        markAll.textContent = marked && marked === results.length
          ? tr("Markierungen der Treffer aufheben", "Unmark all results")
          : tr(`Alle ${results.length} Treffer markieren`, `Mark all ${results.length} results`);
        markAll.disabled = !results.length || selectionOpen || body.inert;
        review.textContent = selectionOpen ? tr("Treffer anzeigen", "Show results") : tr("Auswahl ansehen", "Review selection");
        review.setAttribute("aria-pressed", String(selectionOpen));
        review.disabled = !selected.size;
        next.disabled = !selected.size;
        const top = resetScroll ? 0 : scrollTop;
        scrollTop = top;
        rows.replaceChildren();
        const visible = selectionOpen ? [...selected.values()] : results;
        if (!visible.length) make("p", selectionOpen
          ? tr("Keine Geräte ausgewählt.", "No devices selected.")
          : tr("Keine passenden Geräte.", "No matching devices."), rows);
        for (const option of visible) {
          const item = option.item;
          const entry = deviceRow(rows, item, selected.has(option.key), (checkbox) => {
            mark(option, checkbox.checked);
            draw();
            const focused = Array.from(rows.querySelectorAll("input")).find((node) => node.value === item.id);
            (focused ?? searchInput).focus({preventScroll: true});
          });
          if (option.members.length > 1) {
            const channels = make("details", undefined, entry);
            make("summary", tr(`${option.members.length} Kanäle`, `${option.members.length} channels`), channels);
            const list = make("ul", undefined, channels);
            for (const id of option.members) make("li", deviceName(definitions.get(id)), list);
          }
        }
        rows.scrollTop = top;
      };
      draw();
    };

    const assignmentFields = (rows) => {
      const assignmentsBox = make("div", undefined, body);
      assignmentWidgets = [];
      const remember = (recent, value) => {
        if (!value) return;
        const previous = recent.indexOf(value);
        if (previous >= 0) recent.splice(previous, 1);
        recent.unshift(value);
      };
      const suggestions = (active) => {
        for (const widget of assignmentWidgets) {
          if (widget === active) continue;
          const {item, state, area, labelRows} = widget;
          area.replaceChildren();
          for (const [id, name] of this.prioritizeImportOptions(item.areas, recentAreas, ([id]) => id)) {
            make("option", name, area).value = id;
          }
          area.value = state.area;
          for (const [, node] of this.prioritizeImportOptions([...labelRows], recentLabels, ([name]) => name)) {
            node.parentNode.append(node);
          }
        }
      };
      for (const item of rows) {
        const fieldset = make("fieldset", undefined, assignmentsBox);
        fieldset.className = "import-assignment";
        make("legend", item.name, fieldset);
        const state = assignments.get(item.key) ?? {area: item.suggested, labels: []};
        assignments.set(item.key, state);
        const area = make("select", undefined, make("label", tr("HA-Bereich", "HA area"), fieldset));
        for (const [id, name] of item.areas) make("option", name, area).value = id;
        if (!item.areas.some(([id]) => id === state.area)) state.area = item.suggested;
        area.value = state.area;
        const widget = {item, state, area, labelRows: new Map()};
        assignmentWidgets.push(widget);
        area.addEventListener("change", () => {
          state.area = area.value;
          remember(recentAreas, state.area);
          suggestions(widget);
        });
        state.labels = state.labels.filter((value) => item.labels.includes(value));
        if (item.labels.length) {
          const labels = make("details", undefined, fieldset);
          const summary = make("summary", "", labels);
          const update = () => { summary.textContent = "Labels" + (state.labels.length ? " · " + state.labels.join(", ") : ""); };
          for (const name of item.labels) {
            const label = make("label", undefined, labels);
            label.className = "import-check";
            widget.labelRows.set(name, label);
            const input = make("input", undefined, label);
            input.type = "checkbox";
            input.checked = state.labels.includes(name);
            make("span", name, label);
            input.addEventListener("change", () => {
              state.labels = input.checked ? [...state.labels, name] : state.labels.filter((value) => value !== name);
              if (input.checked) remember(recentLabels, name);
              suggestions(widget);
              update();
            });
          }
          update();
        }
      }
      suggestions(null);
    };
    const assignmentPayload = (rows) => Object.fromEntries(rows.map(({key}) => [key, assignments.get(key)]));
    const assignmentError = (error) => new Error(error === "duplicate_assignment"
      ? tr("Verwende denselben FHEM-Raum je Gerät entweder als Bereich oder als Label.",
           "Use each FHEM room either as the area or as a label for a device.")
      : tr("Die Bereichs- oder Labelauswahl hat sich geändert.", "Available areas or labels changed."));

    const areas = ({rows, devices}) => {
      show(tr("Bereiche und Labels", "Areas and labels"));
      assignmentFields(rows);
      const next = make("fieldset", undefined, body);
      next.className = "import-assignment";
      make("legend", tr("Nach dem Import öffnen", "Open after import"), next);
      const single = devices.length === 1;
      const destinations = single
        ? [["device", tr("HA-Geräteseite", "HA device page")],
           ["customize", tr("Geräteseite gestalten", "Customize device page")],
           ["group", tr("Importierte Geräte gruppieren", "Group imported devices")],
           ["more", tr("Weitere Geräte importieren", "Import more devices")],
           ["overview", tr("Bridge-Übersicht", "Bridge overview")]]
        : [["overview", tr("Bridge-Übersicht", "Bridge overview")],
           ["imported", tr("Gerade importierte Geräte anzeigen", "Show just imported devices")],
           ["group", tr("Importierte Geräte gruppieren", "Group imported devices")],
           ["more", tr("Weitere Geräte importieren", "Import more devices")]];
      if (!destinations.some(([value]) => value === destination)) destination = destinations[0][0];
      const radioName = "import-destination-" + uniqueId();
      for (const [value, name] of destinations) {
        const label = make("label", undefined, next);
        label.className = "import-check";
        const radio = make("input", undefined, label);
        radio.type = "radio";
        radio.name = radioName;
        radio.value = value;
        radio.checked = value === destination;
        radio.addEventListener("change", () => { if (radio.checked) destination = value; });
        make("span", name, label);
      }
      const footer = make("div", undefined, body);
      footer.className = "import-footer";
      action(tr("← Zur Geräteauswahl", "← Back to device selection"), footer, picker);
      action(tr("Importieren", "Import"), footer, async () => {
        body.inert = true;
        status.textContent = tr("Geräte werden importiert …", "Importing devices …");
        status.classList.remove("error");
        let result;
        try {
          result = await api("commit", {...payload(), assignments: assignmentPayload(rows)});
          if (result.error) {
            throw new Error(result.error === "duplicate_assignment"
              ? assignmentError(result.error).message
              : tr("Die Bereichs- oder Labelauswahl hat sich geändert. Gehe zur Geräteauswahl zurück.",
                   "Available areas or labels changed. Go back to device selection."));
          }
        } catch (error) {
          if (main.isConnected) showError(error);
          return;
        } finally {
          body.inert = false;
        }
        if (main.isConnected) await complete(result.devices, destination);
      }, true);
    };

    const navigate = (url) => window.location.assign(url);
    const restart = async ({retryWhileReloading = false} = {}) => {
      show(groupMode ? tr("Geräte gruppieren", "Group devices") : tr("Geräte importieren", "Import devices"));
      const loading = make("p", tr("FHEM-Katalog wird geladen …", "Loading FHEM catalog …"), body);
      loading.setAttribute("role", "status");
      try {
        for (let retries = retryWhileReloading ? 12 : 0; main.isConnected; retries--) {
          try {
            setCatalog(await api("catalog"));
            if (main.isConnected) (groupMode ? groupPicker : picker)();
            return;
          } catch (error) {
            if (!retries || !["FHEM Bridge is offline", "FHEM catalog is unavailable"].includes(error?.message)) throw error;
            await new Promise((resolve) => setTimeout(resolve, 500));
          }
        }
      } catch (error) {
        if (!main.isConnected) return;
        loading.remove();
        showError(error);
        action(tr("Erneut laden", "Retry"), body, restart);
        link(tr("Zur Bridge-Übersicht", "Back to bridge overview"), bridgeUrl, body);
      }
    };
    const complete = async (devices, target) => {
      search = "";
      filters = emptyFilters();
      filtersOpen = selectionOpen = false;
      scrollTop = 0;
      selected.clear();
      assignments.clear();
      destination = undefined;
      show(tr("Importierte Geräte", "Imported devices"));
      const keys = devices.map(({key}) => key);
      const loading = make("p", tr("HA lädt die importierten Geräte …", "HA is loading the imported devices …"), body);
      loading.setAttribute("role", "status");
      let ready = {};
      try {
        for (let attempt = 0; attempt < 60 && main.isConnected; attempt++) {
          ready = await api("devices", {keys});
          if (!main.isConnected) return;
          if (keys.every((key) => ready[key])) {
            if (target === "overview") return navigate(bridgeUrl);
            if (target === "more") return await restart();
            if (target === "device") return navigate("/config/devices/device/" + encodeURIComponent(ready[keys[0]].id));
            if (target === "customize") return navigate("/fhem-bridge-device?device=" + encodeURIComponent(ready[keys[0]].identifier));
            if (target === "group") return await openImportedGroup(devices);
            break;
          }
          await new Promise((resolve) => setTimeout(resolve, 500));
        }
      } catch (error) {
        if (main.isConnected) showError(error);
      }
      if (!main.isConnected) return;
      loading.remove();
      const list = make("ul", undefined, body);
      for (const {key, name} of devices) {
        const item = make("li", undefined, list);
        if (ready[key]) link(name, "/config/devices/device/" + encodeURIComponent(ready[key].id), item);
        else make("span", name + " · " + tr("noch nicht verfügbar", "not yet available"), item);
      }
      const actions = make("div", undefined, body);
      actions.className = "import-toolbar";
      if (keys.every((key) => ready[key])) action(tr("Importierte Geräte gruppieren", "Group imported devices"), actions,
        () => openImportedGroup(devices));
      action(tr("Weitere Geräte importieren", "Import more devices"), actions, restart, true);
      if (keys.some((key) => !ready[key])) {
        if (!status.textContent) {
          status.textContent = tr("Import gespeichert. HA hat noch nicht alle Geräte geladen.",
                                  "Import saved. HA has not finished loading all devices.");
        }
        action(tr("Erneut prüfen", "Check again"), actions, () => complete(devices, target));
      }
      link(tr("Zur Bridge-Übersicht", "Back to bridge overview"), bridgeUrl, actions);
    };

    const groupMode = this.importDialog?.mode === "group";
    let anchor, anchorChoice, previousGroup, anchorSearch = "", channelSearch = "", importChannels = true;
    let editedAnchor;
    const members = new Set();
    let showUnimported = false, importMembers = null;
    let importedBatch = null, recentOnly = true;
    const openImportedGroup = async (devices) => {
      show(tr("Geräte gruppieren", "Group devices"));
      try {
        setCatalog(await api("catalog"));
        if (!main.isConnected) return;
        resetGrouping();
        importedBatch = devices;
        recentOnly = true;
        importMembers = new Set(devices.flatMap(({key}) => catalog.groups["group:" + key]?.members ??
          catalog.saved_groups?.find((group) => group.primary === key)?.members ?? [key]));
        groupPicker();
      } catch (error) {
        if (main.isConnected) {
          showError(error);
          action(tr("Zur Importbestätigung", "Back to import confirmation"), body, () => complete(devices, "imported"));
        }
      }
    };
    const resetGrouping = () => {
      anchor = anchorChoice = previousGroup = editedAnchor = undefined;
      anchorSearch = channelSearch = "";
      importChannels = true;
      showUnimported = false;
      members.clear();
    };
    const groupSearch = (item, value) => {
      const fields = [item.name, item.alias, item.type, item.model, item.address, ...item.rooms]
        .filter(Boolean).join(" ").toLocaleLowerCase();
      return value.trim().toLocaleLowerCase().split(/\s+/).every((word) => fields.includes(word));
    };
    const channelSuggestion = (item) => {
      if (item.type !== "FS20" || anchor.type !== "FS20" || !item.address || !anchor.address) return 0;
      const [housecode, address] = item.address.split(" ");
      const [anchorCode, anchorAddress] = anchor.address.split(" ");
      if (housecode !== anchorCode || address.includes("f") || anchorAddress.includes("f")) return 0;
      const models = [anchor.model, item.model].filter(Boolean).map((model) => model.toLowerCase());
      if (models.length && models.every((model) => model === "fs20pira") &&
          [anchorAddress, address].sort().join("/") === "00/01") {
        return 2;
      }
      return 1;
    };
    const groupPicker = () => {
      show(tr("Geräte gruppieren", "Group devices"));
      const choosingChannels = !!anchor;
      make("h2", choosingChannels ? tr("Kanäle auswählen", "Select channels") :
        tr("Hauptgerät auswählen", "Select the main device"), body);
      if (choosingChannels) make("p", deviceName(anchor), body);
      const toolbar = make("div", undefined, body);
      toolbar.className = "import-toolbar";
      searchField(toolbar, tr("Name, Raum, Modell oder Adresse suchen …", "Search name, room, model or address …"),
        choosingChannels ? channelSearch : anchorSearch, (value) => {
          if (choosingChannels) channelSearch = value;
          else anchorSearch = value;
          draw(true);
        });
      action(tr("Zur Bridge-Konfiguration", "Back to bridge configuration"), toolbar, () => this.importDialog?.close());
      if (importMembers) action(tr("Zur Importbestätigung", "Back to import confirmation"), toolbar, () => {
        const batch = importedBatch;
        importMembers = null;
        importedBatch = null;
        void complete(batch, "imported");
      });
      if (importMembers && !choosingChannels) {
        const scopeLabel = make("label", tr("Hauptgeräte anzeigen", "Show main devices"), toolbar);
        const recent = make("select", undefined, scopeLabel);
        make("option", tr("Gerade importierte Geräte", "Just imported devices"), recent).value = "recent";
        make("option", tr("Alle importierten Geräte", "All imported devices"), recent).value = "all";
        recent.value = recentOnly ? "recent" : "all";
        recent.addEventListener("change", () => { recentOnly = recent.value === "recent"; draw(true); });
      }
      if (!importMembers || choosingChannels) {
        const scope = make("label", undefined, toolbar);
        scope.className = "import-check";
        const scopeCheck = make("input", undefined, scope);
        scopeCheck.type = "checkbox";
        scopeCheck.checked = showUnimported;
        scopeCheck.addEventListener("change", () => { showUnimported = scopeCheck.checked; draw(true); });
        make("span", tr("Auch nicht importierte anzeigen", "Include devices not yet imported"), scope);
      }

      const chosen = make("div", undefined, body);
      const count = make("p", "", body);
      count.setAttribute("aria-live", "polite");
      const rows = make("div", undefined, body);
      rows.className = "import-list group-list";
      rows.tabIndex = 0;
      rows.setAttribute("aria-label", tr("Geräteliste", "Device list"));
      let next, importOption, importCheck;
      if (choosingChannels && !importMembers) {
        importOption = make("label", undefined, body);
        importOption.className = "import-check";
        importCheck = make("input", undefined, importOption);
        importCheck.type = "checkbox";
        importCheck.checked = importChannels;
        importCheck.addEventListener("change", () => { importChannels = importCheck.checked; });
        make("span", tr("Gruppe beim Speichern auch importieren", "Also import the group when saving"), importOption);
      }
      const {footer, footerAction} = groupFooter();
      if (choosingChannels) {
        footerAction(tr("← Zur Hauptgeräteauswahl", "← Back to main device selection"), () => {
          anchor = undefined;
          groupPicker();
        });
        next = footerAction(tr("Gruppierung prüfen →", "Review grouping →"), async () => {
          if (next.disabled) return;
          const payload = {anchor: anchor.id, members: [...members], import_channels: !importOption || importOption.hidden || importChannels};
          const selectedAnchor = importMembers && [...selected.values()].find(({members}) => members.includes(anchor.id));
          if (selectedAnchor) payload.room_hints = {[anchor.id]: selectedAnchor.roomHints};
          footer.inert = body.inert = true;
          try {
            const review = await api("group_preview", payload);
            if (main.isConnected) showGroupReview(payload, review);
          } catch (error) {
            if (main.isConnected) showError(error);
          } finally {
            footer.inert = body.inert = false;
          }
        }, true);
      } else {
        next = footerAction(tr("Weiter zur Kanalauswahl →", "Continue to channel selection →"), () => {
          if (!anchorChoice) return;
          anchor = anchorChoice;
          if (anchor.id !== editedAnchor) {
            editedAnchor = anchor.id;
            previousGroup = (catalog.saved_groups ?? []).find((group) => group.primary === anchor.id);
            members.clear();
            for (const id of previousGroup?.members ?? []) {
              if (id !== anchor.id && definitions.has(id)) members.add(id);
            }
            for (const id of importMembers ?? []) {
              if (id !== anchor.id) members.add(id);
            }
            channelSearch = "";
            importChannels = true;
          }
          groupPicker();
        }, true);
      }
      const radioName = "fhem-group-anchor-" + uniqueId();
      const candidates = catalog.definitions.filter((item) => item.id !== anchor?.id).map((item) => ({
        item, confidence: choosingChannels ? channelSuggestion(item) : 0,
      })).sort((a, b) => b.confidence - a.confidence || compare(deviceName(a.item), deviceName(b.item)));
      const draw = (resetScroll = false) => {
        const top = resetScroll ? 0 : rows.scrollTop;
        const visible = candidates.filter(({item}) => (showUnimported || item.installed || importMembers?.has(item.id)) &&
          (choosingChannels || !importMembers || !recentOnly || importMembers.has(item.id)) &&
          (!choosingChannels || !members.has(item.id)) &&
          groupSearch(item, choosingChannels ? channelSearch : anchorSearch));
        const renderRow = (parent, item, confidence, checked) => {
          const installed = item.installed ? tr("Importiert", "Imported") : "";
          const suggestion = ["", tr("Gleicher FS20-Hauscode", "Same FS20 house code"),
            tr("Typisches PIRA-Adresspaar 00/01", "Typical PIRA address pair 00/01")][confidence];
          const note = [suggestion, installed].filter(Boolean).join(" · ");
          deviceRow(parent, item, checked, (input) => {
            if (!choosingChannels) {
              if (input.checked) anchorChoice = item;
              next.disabled = !anchorChoice;
              return;
            }
            if (input.checked) members.add(item.id);
            else members.delete(item.id);
            draw();
            [...chosen.querySelectorAll("input"), ...rows.querySelectorAll("input")]
              .find((option) => option.value === item.id)?.focus({preventScroll: true});
          }, {address: item.address, note, radio: choosingChannels ? undefined : radioName});
        };
        chosen.replaceChildren();
        if (choosingChannels && members.size) {
          make("h3", tr("Ausgewählte Kanäle", "Selected channels"), chosen);
          const selectedRows = make("div", undefined, chosen);
          selectedRows.className = "import-list group-list";
          for (const {item, confidence} of candidates) {
            if (members.has(item.id)) renderRow(selectedRows, item, confidence, true);
          }
        }
        rows.replaceChildren();
        for (const {item, confidence} of visible) renderRow(rows, item, confidence, !choosingChannels && item.id === anchorChoice?.id);
        if (!visible.length) make("p", tr("Keine passenden Geräte.", "No matching devices."), rows);
        rows.scrollTop = top;
        count.textContent = choosingChannels ? tr(`${visible.length} weitere Kanäle · ${members.size} ausgewählt`,
          `${visible.length} more channels · ${members.size} selected`) : tr(`${visible.length} Geräte`, `${visible.length} devices`);
        if (choosingChannels) {
          next.disabled = !members.size && !previousGroup;
          if (importOption) importOption.hidden = !members.size || anchor.installed ||
            [...members, ...(previousGroup?.members ?? [])].some((id) => definitions.get(id)?.installed);
          if (next.disabled) count.textContent += tr(" · Wähle mindestens einen Kanal.", " · Select at least one channel.");
        } else next.disabled = !anchorChoice;
      };
      draw();
    };
    const showGroupReview = (payload, review) => {
      const {target, moves, rows, review: confirmation} = review;
      show(tr("Gruppierung prüfen", "Review grouping"));
      const summary = make("div", undefined, body);
      summary.className = "editor-card";
      if (!payload.members.length) make("h2", tr("Gruppierung auflösen", "Dissolve grouping"), summary);
      else {
        const heading = !payload.import_channels ? tr("Gruppe für späteren Import", "Group for future import") : target.id
          ? tr("Diese HA-Geräteseite bleibt erhalten", "This HA device page is kept")
          : tr("Neue HA-Geräteseite", "New HA device page");
        make("h2", heading, summary);
      }
      make("strong", target.name, summary);
      const channels = make("ul", undefined, summary);
      for (const id of payload.members) make("li", deviceName(definitions.get(id)), channels);
      if (review.assignments?.length) {
        make("h3", tr("Bereiche und Labels vor der Gruppierung", "Areas and labels before grouping"), summary);
        make("p", tr("Die gemeinsame Geräteseite verwendet den Bereich und die Labels des Hauptgeräts.",
          "The shared device page uses the main device's area and labels."), summary);
        const list = make("ul", undefined, summary);
        for (const item of review.assignments) make("li", `${item.name} · ${item.area || tr("Kein Bereich", "No area")} · ` +
          (item.labels.join(", ") || tr("Keine Labels", "No labels")), list);
      }
      if (review.new_imports?.length) {
        const count = review.new_imports.length;
        make("p", count === 1 ? tr("Eine FHEM-Definition wird neu importiert.", "One FHEM definition will be imported.") :
          tr(`${count} FHEM-Definitionen werden neu importiert.`, `${count} FHEM definitions will be imported.`), summary);
      }
      if (moves.length) {
        make("h3", tr("Entitäten, die die Geräteseite wechseln", "Entities moving to another device page"), summary);
        for (const {name, entities} of moves) {
          const details = make("details", undefined, summary);
          details.open = true;
          make("summary", name, details);
          const list = make("ul", undefined, details);
          for (const entity of entities) make("li", entity, list);
        }
      }
      if (rows.length) {
        make("h2", tr("Bereiche und Labels", "Areas and labels"), body);
        assignmentFields(rows);
      }
      const {footer, footerAction} = groupFooter();
      footerAction(tr("← Zur Kanalauswahl", "← Back to channels"), groupPicker);
      footerAction(tr("Gruppierung speichern", "Save grouping"), async () => {
        footer.inert = body.inert = true;
        try {
          const result = await api("group_commit", {...payload, review: confirmation, assignments: assignmentPayload(rows)});
          if (result.error === "group_changed") throw new Error(tr("Die Gruppierung hat sich geändert. Prüfe die Auswahl erneut.",
            "The grouping changed. Review the selection again."));
          if (result.error) throw assignmentError(result.error);
          if (!main.isConnected) return;
          this.importDialog.saved = true;
          show(tr("Gruppierung gespeichert", "Grouping saved"));
          const actions = make("div", undefined, body);
          actions.className = "import-footer";
          action(tr("Zur Bridge-Konfiguration", "Back to bridge configuration"), actions,
            () => this.importDialog.close());
          action(tr("Zur Bridge-Übersicht", "Back to bridge overview"), actions, () => navigate(bridgeUrl));
          action(importMembers ? tr("Weitere Geräte importieren", "Import more devices") : tr("Weiteres Gerät gruppieren", "Group another device"), actions, async () => {
            resetGrouping();
            importMembers = null;
            importedBatch = null;
            selected.clear();
            search = "";
            filters = emptyFilters();
            filtersOpen = selectionOpen = false;
            scrollTop = 0;
            assignments.clear();
            this.importDialog.saved = false;
            await restart({retryWhileReloading: true});
          }, true);
        } catch (error) {
          if (main.isConnected) showError(error);
        } finally {
          footer.inert = body.inert = false;
        }
      }, true);
    };
    await restart();
  }

  deviceViews(parent, showDetails) {
    const de = this._hass.locale?.language?.startsWith("de");
    const nav = this.node("nav", undefined, parent);
    nav.className = "view-tabs";
    nav.setAttribute("aria-label", de ? "Geräteansichten" : "Device views");
    const {pathname, search} = window.location;
    for (const [details, label] of [
      [false, de ? "Geräteseite gestalten" : "Customize device page"],
      [true, de ? "Gerätebedienung" : "Device controls"],
      ["attributes", de ? "Geräteattribute" : "Device attributes"],
    ]) {
      if (details === showDetails) {
        const current = this.node("strong", label, nav);
        current.setAttribute("aria-current", "page");
        continue;
      }
      const params = new URLSearchParams(search);
      params.delete("details");
      params.delete("attributes");
      if (details) params.set(details === "attributes" ? "attributes" : "details", "1");
      if (this.data.source) params.set("reference", this.data.source);
      const link = this.node("a", label, nav);
      link.href = pathname + "?" + params;
      link.addEventListener("click", (event) => {
        if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        if (this.attributeDraftDirty && !window.confirm(this.labels.discardDraft)) return;
        this.attributeDraftDirty = false;
        window.history.replaceState(window.history.state, "", link.href);
        this._locationSearch = window.location.search;
        this.render();
        if (details === false && !this.publication) void this.load();
      });
    }
  }

  async configurationPanel(parent, entryId, compact = false) {
    const de = this._hass.locale?.language?.startsWith("de");
    const tr = (german, english) => de ? german : english;
    const call = (fields = {}) => this._hass.callWS({type: "fhem_bridge/config_status", entry_id: entryId, ...fields});
    const draw = (status, message = "") => {
      parent.replaceChildren();
      if (!status.supported) {
        if (!compact) this.node("p", tr("Das FHEM-Modul unterstützt diese Funktion noch nicht.",
          "The FHEM module does not support this feature yet."), parent);
        return;
      }
      if (compact && !status.dirty && !status.save_error && !message) return;
      const card = this.node("section", undefined, parent);
      card.className = "editor-card form";
      if (status.save_error) {
        this.node("strong", tr("Speichern fehlgeschlagen", "Could not save configuration"), card);
        this.node("pre", status.save_error, card).className = "attr-value";
      }
      this.node("strong", status.dirty ? tr("Ungespeicherte Änderungen in FHEM", "Unsaved changes in FHEM")
        : status.save_error ? tr("Speicherstand prüfen", "Check saved configuration")
          : tr("Keine ungespeicherten Änderungen gemeldet", "No unsaved changes reported"), card);
      if (message) this.node("p", message, card).setAttribute("role", "status");
      if (status.dirty) {
        const recent = this.node("details", undefined, card);
        this.node("summary", tr("Letzte Änderungen ansehen", "View recent changes"), recent);
        recent.addEventListener("toggle", async () => {
          if (!recent.open || recent.children.length > 1) return;
          try {
            const response = await call({details: true});
            const list = this.node("ul", undefined, recent);
            for (const item of response.recent ?? []) this.node("li", item, list);
            if (!list.children.length) this.node("li", tr("Keine Einträge verfügbar.", "No history entries available."), list);
          } catch (error) {
            this.node("p", error.message ?? String(error), recent);
          }
        });
      }
      if (status.can_save) this.button(tr("FHEM-Konfiguration speichern", "Save FHEM configuration"), card, async (event) => {
        if (!window.confirm(tr(
          "Gesamte FHEM-Konfiguration speichern? Das umfasst auch Änderungen an anderen Geräten und aus FHEMWEB.",
          "Save the entire FHEM configuration? This includes changes to other devices and from FHEMWEB."))) return;
        const button = event.currentTarget;
        button.disabled = true;
        try {
          const result = await call({save: true});
          draw(result, result.save_error ? "" : tr("FHEM-Konfiguration gespeichert.", "FHEM configuration saved."));
        } catch (error) {
          this.node("p", error.message ?? String(error), card).setAttribute("role", "alert");
          button.disabled = false;
        }
      }).className = "primary";
      else this.node("p", tr("Globales Speichern ist für diese Bridge nicht freigegeben.",
        "Global configuration save is disabled for this bridge."), card);
    };
    try { draw(await call()); }
    catch (error) { if (!compact) this.node("p", error.message ?? String(error), parent); }
  }

  async attributePanel(parent) {
    const de = this._hass.locale?.language?.startsWith("de");
    const tr = (german, english) => de ? german : english;
    const config = this.node("div", undefined, parent);
    const renderStatus = () => {
      config.replaceChildren();
      if (this.data?.bridge_entry_id) void this.configurationPanel(config, this.data.bridge_entry_id, true);
    };
    renderStatus();
    const heading = this.node("header", undefined, parent);
    this.node("h2", tr("Gesetzte Attribute", "Configured attributes"), heading);
    const notice = this.node("p", this.labels.loading, parent);
    notice.setAttribute("role", "status");
    const searchRow = this.node("div", undefined, parent);
    const search = this.node("input", undefined, searchRow);
    search.type = "search";
    search.placeholder = tr("Nach Attributname suchen …", "Search by attribute name …");
    search.setAttribute("aria-label", search.placeholder);
    const rows = this.node("div", undefined, parent);
    rows.className = "attr-list";
    const editor = this.node("section", undefined, parent);
    editor.className = "attribute-editor editor-card form";
    editor.hidden = true;
    editor.tabIndex = -1;
    const source = this.data.source;
    const target = this.targetKey;
    const current = () => this.targetKey === target && editor.isConnected;
    const call = (op, fields = {}) => this.request(op, {source, ...fields});
    let data;
    const showNotice = (message, error = false) => {
      notice.textContent = message;
      notice.classList.toggle("error", error);
    };
    const refresh = async () => {
      const response = await call("attribute_overview");
      if (!current()) return;
      data = response;
      drawRows();
    };
    const drawRows = () => {
      rows.replaceChildren();
      const entries = data.items.filter((item) => item.name.toLowerCase().includes(search.value.toLowerCase()));
      if (!entries.length) this.node("p", tr("Keine passenden gesetzten Attribute.", "No matching configured attributes."), rows);
      else {
        const labels = this.node("div", undefined, rows);
        labels.className = "attr-row reading-headings";
        this.node("strong", tr("Attribut", "Attribute"), labels);
        this.node("strong", tr("Wert", "Value"), labels);
      }
      for (const item of entries) {
        const row = this.node("div", undefined, rows);
        row.className = "attr-row";
        const identity = this.node("div", undefined, row);
        const name = this.button(item.name + (data.writable ? " ✎" : ""), identity, () => void open(item.name, !data.writable));
        name.className = "edit-name";
        name.setAttribute("aria-label", item.name + (data.writable ? tr(" bearbeiten", " edit") : tr(" lesen", " read")));
        const cell = this.node("div", undefined, row);
        if (item.text != null) this.node("pre", item.text, cell).className = "attr-value";
        if (!item.complete) {
          this.node("small", item.lines + tr(" Zeilen · ", " lines · ") + item.bytes.toLocaleString() + " Byte", cell);
          this.button(tr("Vollständig anzeigen", "Show full value"), cell, () => void open(item.name, true));
        }
      }
    };
    const showEditor = (title) => {
      editor.setAttribute("aria-label", title);
      editor.hidden = false;
      this.node("h3", title, editor);
      editor.focus({preventScroll: true});
      editor.scrollIntoView({block: "nearest"});
    };
    const close = () => {
      this.closeAttributeFullscreen?.();
      editor.hidden = true;
      editor.replaceChildren();
      this.attributeDraftDirty = false;
    };
    const canLeave = () => !this.attributeDraftDirty || window.confirm(this.labels.discardDraft);
    const open = async (name, readOnly = false) => {
      if (!canLeave()) return;
      close();
      showEditor(name);
      const region = this.node("div", this.labels.loading, editor);
      try {
        const loaded = await call("attribute_read", {attribute: name});
        if (!current() || !region.isConnected) return;
        region.replaceChildren();
        region.className = "form";
        const original = loaded.value ?? "";
        const binary = typeof original !== "string";
        const multiline = !binary && (original.includes("\n") || original.length > 100);
        const fields = data.catalog[name] ?? [];
        const field = fields[0];
        const actions = this.node("div", undefined, region);
        actions.className = "row";
        let getValue;
        if (binary) {
          const value = this.node("pre", original.value, region);
          value.className = "attr-value";
          this.node("p", tr("Der Wert enthält Bytes außerhalb von UTF-8. Anzeige als Base64.",
            "This value contains non-UTF-8 bytes. Displayed as Base64."), region);
        } else if (!multiline && !readOnly && field?.type === "select" && field.options) {
          const select = this.node("select", undefined, this.node("label", tr("Wert", "Value"), region));
          this.node("option", this.labels.choose, select).value = "";
          for (const option of new Set([...field.options, ...(original ? [original] : [])])) {
            this.node("option", option, select).value = option;
          }
          select.value = original;
          getValue = () => select.value;
          select.addEventListener("change", () => { this.attributeDraftDirty = select.value !== original; });
        } else {
          getValue = this.attributeTextEditor(region, original, readOnly, multiline || field?.multiline || name === "userattr", tr, editor);
        }
        region.append(actions);
        this.button(readOnly ? tr("Schließen", "Close") : tr("Abbrechen", "Cancel"), actions, () => {
          if (canLeave()) close();
        });
        const apply = async (remove = false) => {
          const value = getValue?.();
          if (!remove && value === original) {
            if (loaded.tag !== "missing") close();
            else this.node("p", tr("Gib einen Attributwert ein.", "Enter an attribute value."), region).setAttribute("role", "alert");
            return;
          }
          if (remove && !window.confirm(tr(
            'Attribut „' + name + '“ auf „' + this.data.name + '“ löschen?',
            'Delete attribute "' + name + '" on "' + this.data.name + '"?'))) return;
          const buttons = [...actions.querySelectorAll("button")];
          for (const button of buttons) button.disabled = true;
          try {
            const result = await call("attribute_update", {attribute: name, expected: loaded.tag, remove,
              ...(remove ? {} : {value})});
            if (!current()) return;
            this.attributeDraftDirty = false;
            renderStatus();
            await refresh();
            if (result.error_message || !result.exact) {
              const actual = await call("attribute_read", {attribute: name});
              close();
              showEditor(tr("Aktueller Wert in FHEM", "Current value in FHEM"));
              this.node("p", result.error_message || tr("FHEM hat den eingegebenen Wert geändert.",
                "FHEM changed the submitted value."), editor).className = "error";
              this.node("pre", typeof actual.value === "string" ? actual.value : actual.value?.value ??
                tr("Attribut nicht gesetzt", "Attribute not set"), editor).className = "attr-value";
              this.button(tr("Schließen", "Close"), editor, close);
            } else {
              close();
              showNotice(remove ? tr("Attribut gelöscht.", "Attribute deleted.") : tr("Attribut gesetzt.", "Attribute set."));
            }
          } catch (error) {
            if (current()) {
              const failure = this.node("p", error.message ?? String(error), region);
              failure.setAttribute("role", "alert");
              failure.className = "error";
            }
          } finally {
            for (const button of buttons) button.disabled = false;
          }
        };
        if (data.writable && !readOnly) {
          if (loaded.value !== null) this.button(tr("Attribut löschen", "Delete attribute"), actions, () => void apply(true));
          if (!binary) this.button(tr("Attribut setzen", "Set attribute"), actions, () => void apply()).className = "primary";
        }
      } catch (error) {
        if (current() && region.isConnected) region.textContent = error.message ?? String(error);
      }
    };
    try {
      const overview = await call("attribute_overview");
      if (!current()) return;
      if (!overview.supported) {
        const legacy = await this.request("describe", {source});
        if (!current()) return;
        this.data = {...this.data, attributes: legacy.attributes, sections: {...this.data.sections, attr: legacy.sections.attr}};
        search.hidden = true;
        showNotice(tr("Für den neuen Attributeditor und lange Werte wird HABridge 0.9.32 benötigt.",
          "HABridge 0.9.32 is required for the new attribute editor and long values."));
        this.section(parent, "attr");
        return;
      }
      data = overview;
      showNotice(data.writable ? "" : tr("Attributänderungen sind für diesen Kanal gesperrt.", "Attribute editing is disabled for this channel."));
      if (data.writable) this.button(tr("+ Attribut hinzufügen", "+ Add attribute"), heading, () => {
        if (!canLeave()) return;
        close();
        showEditor(tr("Attribut hinzufügen", "Add attribute"));
        const set = new Set(data.items.map((item) => item.name));
        const names = Object.keys(data.catalog).filter((name) => !set.has(name)).sort();
        const select = this.node("select", undefined, editor);
        select.setAttribute("aria-label", tr("Ungesetztes Attribut", "Unset attribute"));
        this.node("option", this.labels.choose, select).value = "";
        for (const name of names) this.node("option", name, select).value = name;
        if (!names.length) this.node("p", tr("Keine weiteren Attribute verfügbar.", "No further attributes available."), editor);
        select.addEventListener("change", () => { if (select.value) void open(select.value); });
        this.button(tr("Abbrechen", "Cancel"), editor, close);
        select.focus();
      });
      search.addEventListener("input", drawRows);
      drawRows();
    } catch (error) {
      if (current()) showNotice(error.message ?? String(error), true);
    }
  }

  attributeTextEditor(parent, original, readOnly, multiline, tr, section) {
    const wrapper = this.node("div", undefined, parent);
    wrapper.className = "attribute-workspace";
    const tools = this.node("div", undefined, wrapper);
    tools.className = "row attribute-tools";
    const host = this.node("div", undefined, wrapper);
    let getValue;
    const updateDirty = () => { this.attributeDraftDirty = getValue() !== original; };
    const largeEditor = (value) => {
      tools.replaceChildren();
      host.replaceChildren();
      host.className = "attribute-code";
      const field = this.node("textarea", undefined, host);
      field.value = value;
      field.readOnly = readOnly;
      field.rows = 12;
      field.wrap = "soft";
      field.spellcheck = false;
      field.setAttribute("aria-label", tr("Attributwert", "Attribute value"));
      getValue = () => field.value === value.replace(/\r\n?/g, "\n") ? value : field.value;
      field.addEventListener("input", updateDirty);
      const refreshEditor = () => requestAnimationFrame(() => cm?.refresh());
      const fullscreenLabel = tr("Vollbild", "Fullscreen");
      const fullscreen = this.button(fullscreenLabel, tools, () => {
        if (this.closeAttributeFullscreen) {
          this.closeAttributeFullscreen();
          return;
        }
        const placeholder = document.createComment("attribute editor");
        section.before(placeholder);
        const dialog = this.node("dialog", undefined, this.shadowRoot);
        dialog.className = "attribute-fullscreen";
        dialog.setAttribute("aria-label", section.getAttribute("aria-label"));
        dialog.append(section);
        this.closeAttributeFullscreen = () => {
          this.closeAttributeFullscreen = null;
          dialog.close();
          placeholder.replaceWith(section);
          dialog.remove();
          fullscreen.textContent = fullscreenLabel;
          fullscreen.setAttribute("aria-pressed", "false");
          fullscreen.focus({preventScroll: true});
          refreshEditor();
        };
        dialog.addEventListener("cancel", (event) => {
          event.preventDefault();
          this.closeAttributeFullscreen?.();
        });
        fullscreen.textContent = tr("Vollbild verlassen", "Exit fullscreen");
        fullscreen.setAttribute("aria-pressed", "true");
        dialog.showModal();
        refreshEditor();
      });
      fullscreen.setAttribute("aria-pressed", "false");
      let cm;
      // Load only when a long value is opened. Keep the original line breaks in the document.
      void loadAttributeEditor().then((CodeMirror) => {
        if (!field.isConnected) return;
        const current = getValue();
        cm = CodeMirror(host, {
          value: current, mode: "perl", lineSeparator: "\n", lineNumbers: true, lineWrapping: true,
          matchBrackets: {maxScanLineLength: 20000}, readOnly, inputStyle: "contenteditable",
          spellcheck: false, smartIndent: false, indentWithTabs: true, tabSize: 4,
          screenReaderLabel: tr("Attributwert", "Attribute value"),
        });
        field.remove();
        getValue = () => cm.getValue("\n");
        cm.on("change", updateDirty);
        const wrap = this.button(tr("Weicher Umbruch", "Soft wrap"), tools, () => {
          const enabled = !cm.getOption("lineWrapping");
          cm.setOption("lineWrapping", enabled);
          wrap.setAttribute("aria-pressed", String(enabled));
        });
        wrap.setAttribute("aria-pressed", "true");
        let markers = [];
        let showEndings = true;
        const updateEndings = () => cm.operation(() => {
          for (const marker of markers) marker.clear();
          markers = [];
          if (!showEndings) return;
          const {from, to} = cm.getViewport();
          for (let line = from; line < Math.min(to, cm.lastLine()); line++) {
            const glyph = document.createElement("span");
            glyph.className = "attribute-eol";
            glyph.textContent = "↵";
            glyph.title = tr("Echter Zeilenumbruch (LF)", "Actual line break (LF)");
            glyph.setAttribute("aria-hidden", "true");
            markers.push(cm.setBookmark({line, ch: cm.getLine(line).length}, {widget: glyph, insertLeft: false}));
          }
        });
        const endings = this.button(tr("Zeilenenden anzeigen", "Show line endings"), tools, () => {
          showEndings = !showEndings;
          endings.setAttribute("aria-pressed", String(showEndings));
          updateEndings();
        });
        endings.setAttribute("aria-pressed", "true");
        cm.on("changes", updateEndings);
        cm.on("viewportChange", () => requestAnimationFrame(() => {
          if (host.isConnected) updateEndings();
        }));
        updateEndings();
        const search = this.node("input", undefined, tools);
        search.type = "search";
        search.placeholder = tr("Im Wert suchen", "Search value");
        search.setAttribute("aria-label", search.placeholder);
        const next = () => {
          if (!search.value) return;
          let cursor = cm.getSearchCursor(search.value, cm.getCursor("to"));
          if (!cursor.findNext()) {
            cursor = cm.getSearchCursor(search.value, {line: 0, ch: 0});
            if (!cursor.findNext()) return;
          }
          cm.setSelection(cursor.from(), cursor.to());
          cm.scrollIntoView({from: cursor.from(), to: cursor.to()});
          cm.focus();
        };
        search.addEventListener("keydown", (event) => { if (event.key === "Enter") next(); });
        this.button(tr("Weitersuchen", "Find next"), tools, next);
        cm.refresh();
      }).catch(() => {
        if (field.isConnected) this.node("p", tr("Syntaxfarben und Klammeranzeige konnten nicht geladen werden.",
          "Syntax highlighting and bracket matching could not be loaded."), tools);
      });
    };
    if (multiline || readOnly) largeEditor(original);
    else {
      const input = this.node("input", undefined, host);
      input.value = original;
      input.spellcheck = false;
      input.setAttribute("aria-label", tr("Attributwert", "Attribute value"));
      getValue = () => input.value;
      input.addEventListener("input", updateDirty);
      this.button(tr("Großen Editor öffnen", "Open large editor"), tools, () => largeEditor(getValue()));
    }
    return () => getValue();
  }

  libraryLink(key, bridge = this.bridgeEntry, returnTo = null) {
    const params = new URLSearchParams({bridge});
    if (key) params.set("template", key);
    const current = new URLSearchParams(location.search);
    const device = returnTo?.device ?? current.get("return_device");
    const source = returnTo?.source ?? current.get("return_source");
    if (device) params.set("return_device", device);
    if (source) params.set("return_source", source);
    return location.pathname + "?" + params;
  }

  libraryRequest(op, fields = {}) {
    return this._hass.callWS({type: "fhem_bridge/templates", entry_id: this.bridgeEntry, op, ...fields});
  }

  async loadLibrary() {
    const route = this._locationSearch;
    try {
      const data = await this.libraryRequest("list");
      if (this._locationSearch !== route) return;
      this.libraryError = "";
      this.libraryData = data;
    } catch (error) {
      if (this._locationSearch !== route) return;
      this.libraryError = error.message ?? String(error);
    }
    this.render();
  }

  renderLibrary(main) {
    const de = this._hass.locale?.language?.startsWith("de");
    const params = new URLSearchParams(location.search);
    const nav = this.node("nav", undefined, main);
    nav.className = "row";
    const returnDevice = params.get("return_device");
    if (returnDevice) {
      const back = new URLSearchParams({device: returnDevice, tab: "template"});
      if (params.has("return_source")) back.set("reference", params.get("return_source"));
      const device = Object.values(this._hass.devices ?? {}).find((entry) =>
        entry.identifiers?.some(([domain, id]) => domain === "fhem_bridge" && id === returnDevice));
      const name = device?.name_by_user || device?.name;
      this.node("a", de ? "‹ Zurück zu " + (name || "Gerät") : "‹ Back to " + (name || "device"), nav).href =
        location.pathname + "?" + back;
    }
    this.node("a", params.has("template") ? (de ? "Alle Vorlagen" : "All templates") : this.labels.integration, nav).href =
      params.has("template") ? this.libraryLink() : "/config/integrations/integration/fhem_bridge";
    this.node("h1", de ? "FHEM Bridge · Vorlagen" : "FHEM Bridge · Templates", main);
    this.notice = this.node("p", this.libraryError, main);
    this.notice.className = "message";
    this.notice.setAttribute("role", "status");
    if (!this.libraryData) {
      if (!this.libraryError) this.show(this.labels.loading);
      return;
    }
    const {templates, references, updated, errors} = this.libraryData;
    const pending = templates.filter((item) => item.update_available).length;
    this.node("p", de ? `${updated} automatisch aktualisiert · ${pending} neue Standards verfügbar`
      : `${updated} updated automatically · ${pending} new defaults available`, main);
    if (pending) {
      const list = this.node("ul", undefined, main);
      for (const item of templates.filter((entry) => entry.update_available).sort((a, b) => a.name.localeCompare(b.name))) {
        const link = this.node("a", item.name, this.node("li", undefined, list));
        link.href = this.libraryLink(item.key);
      }
    }
    for (const [file, error] of Object.entries(errors)) this.node("p", file + " · " + error, main);
    const selected = new URLSearchParams(location.search).get("template");
    const picker = this.node("select", undefined, this.node("label", de ? "Vorlage" : "Template", main));
    this.node("option", de ? "Neue Vorlage" : "New template", picker).value = "";
    for (const item of [...templates].sort((a, b) => a.name.localeCompare(b.name))) {
      this.node("option", item.name + (item.update_available ? (de ? " · Neuer Standard" : " · New default") : ""), picker).value = item.key;
    }
    picker.value = selected ?? "";
    picker.addEventListener("change", () => location.href = this.libraryLink(picker.value));
    const doc = templates.find((item) => item.key === selected);
    if (doc) {
      const origin = de ? {working: doc.version === doc.base_version ? "Mitgeliefert" : "Bearbeiteter Standard", default: "Mitgeliefert", custom: "Eigene Vorlage"}
        : {working: "Working copy", default: "Included", custom: "Custom template"};
      this.node("p", origin[doc.origin] + " · " + doc.version, main);
      if (doc.base_version) this.node("p", (de ? "Basis · " : "Based on · ") + doc.base_version, main);
      if (doc.update_available) this.node("p", (de ? "Neuer Standard · " : "New default · ") + doc.standard, main);
      if (doc.description) this.node("p", doc.description, main);
    }
    const actions = this.node("div", undefined, main);
    actions.className = "row";
    const editor = this.node("div", undefined, main);
    const preview = this.node("div", undefined, main);
    const review = async (op, fields, validateDraft = null) => {
      preview.replaceChildren();
      try {
        const response = await this.libraryRequest(op, fields);
        this.renderPreviewRows(preview, response.rows);
        this.button(this.labels.commit, preview, async (event) => {
          if (validateDraft && !validateDraft()) {
            preview.replaceChildren();
            this.show(de ? "Der Entwurf wurde geändert. Bitte erneut prüfen." : "The draft changed. Review again.", true);
            return;
          }
          event.target.disabled = true;
          try {
            const result = await this.libraryRequest("commit", {token: response.token});
            if (!result.reloaded) this.show(this.labels.reloadFailed, true);
            else if (op === "delete") location.href = this.libraryLink();
            else if (["create", "copy", "import", "edit"].includes(op)) location.href = this.libraryLink(result.key);
            else await this.loadLibrary();
          } catch (error) {
            event.target.disabled = false;
            this.show(error.message ?? String(error), true);
          }
        }).className = "primary";
      } catch (error) {
        this.show(error.message ?? String(error), true);
      }
    };
    if (doc?.origin === "working") {
      this.button(de ? "Auf Standard zurücksetzen" : "Reset to default", actions, () => review("reset", {key: doc.key}));
    }
    if (doc?.origin === "custom") {
      this.button(de ? "Vorlage löschen" : "Delete template", actions, () => review("delete", {key: doc.key}));
    }
    const from = new URLSearchParams(location.search).get("from");
    const openEditor = async () => {
      try {
        const data = doc ? (await this.libraryRequest("document", {key: doc.key})).document
          : {name: "", automatic: false, items: [], match: []};
        editor.replaceChildren();
        this.templateForm(editor, data, doc, references, from, review);
      } catch (error) {
        this.show(error.message ?? String(error), true);
      }
    };
    this.button(doc ? (de ? "Vorlage bearbeiten" : "Edit template") : (de ? "Neue Vorlage" : "New template"),
      actions, openEditor);
    if (doc || from) void openEditor();
    this.button(de ? "YAML importieren" : "Import YAML", actions, () => {
      editor.replaceChildren();
      const input = this.node("textarea", undefined, this.node("label", de ? "Vorlage als YAML" : "Template YAML", editor));
      input.rows = 14;
      const file = this.node("input", undefined, this.node("label", de ? "YAML-Datei auswählen" : "Choose YAML file", editor));
      file.type = "file";
      file.accept = ".yaml,.yml";
      file.addEventListener("change", async () => { if (file.files[0]) input.value = await file.files[0].text(); });
      this.button(this.labels.review, editor, () => review("import", {content: input.value}));
      input.focus();
    });
    if (doc) this.button(de ? "YAML öffnen" : "Open YAML", actions, async () => {
      try {
        const result = await this.libraryRequest("document", {key: doc.key});
        editor.replaceChildren();
        const input = this.node("textarea", undefined, this.node("label", de ? "Vorlage als YAML" : "Template YAML", editor));
        input.rows = 16;
        input.value = result.content;
        this.button(this.labels.review, editor, () => review("import", {key: doc.key, content: input.value}));
        input.focus();
      } catch (error) {
        this.show(error.message ?? String(error), true);
      }
    });
  }

  templateForm(parent, draft, original, references, from, review) {
    const de = this._hass.locale?.language?.startsWith("de");
    const tr = (german, english) => de ? german : english;
    const form = this.node("div", undefined, parent);
    form.className = "form";
    const input = (label, value, change, container = form) => {
      const field = this.node("input", undefined, this.node("label", label, container));
      field.value = value ?? "";
      field.addEventListener("input", () => change(field.value));
      return field;
    };
    const check = (label, value, change, container = form) => {
      const row = this.node("label", undefined, container);
      row.className = "row";
      const field = this.node("input", undefined, row);
      field.type = "checkbox";
      field.style.width = "auto";
      field.checked = Boolean(value);
      this.node("span", label, row);
      field.addEventListener("change", () => change(field.checked));
      return field;
    };
    const selector = (label, values, value, change, container) => {
      const field = this.node("select", undefined, this.node("label", label, container));
      for (const [key, text] of values) this.node("option", text, field).value = key;
      field.value = value;
      field.addEventListener("change", () => change(field.value));
      return field;
    };
    this.node("h2", tr("Vorlageninhalt", "Template contents"), form);
    input(tr("Vorlagenname", "Template name"), draft.name, (value) => { draft.name = value; }).maxLength = 100;
    let saveAsNew = false;
    if (original) check(tr("Als neue Vorlage speichern", "Save as new template"), false, (value) => {
      saveAsNew = value;
      automatic.checked = value ? false : original.origin !== "custom" || Boolean(draft.automatic);
      automatic.disabled = !value && original.origin !== "custom";
      if (value) draft.automatic = false;
    });
    let roleId = draft.default_role || "";
    const entries = this.node("div", undefined, form);
    const roleContainer = this.node("div", undefined, entries);
    const roleName = input(tr("Name der neuen Kanalrolle", "New channel role name"), "", () => {}, entries);
    this.button(tr("Kanalrolle hinzufügen", "Add channel role"), entries, () => {
      const name = roleName.value.trim();
      if (!name) return;
      draft.roles ??= {};
      const stem = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "role";
      let key = stem;
      for (let suffix = 2; key in draft.roles; suffix++) key = stem + "-" + suffix;
      draft.roles[key] = {name};
      draft.default_role ??= key;
      roleId = key;
      roleName.value = "";
      redrawRoles();
      redraw();
      drawRules();
    });
    const body = this.node("div", undefined, entries);
    const redrawRoles = () => {
      roleContainer.replaceChildren();
      const roles = Object.entries(draft.roles || {});
      if (!roles.length) return;
      selector(tr("Kanalrolle", "Channel role"),
        [["", tr("Alle Kanäle", "All channels")], ...roles.map(([key, role]) => [key, role.name])],
        roleId, (value) => { roleId = value; redraw(); }, roleContainer);
    };
    const redraw = () => {
      body.replaceChildren();
      const target = draft.roles?.[roleId] ?? draft;
      const modes = ["sensor", "binary", "diagnostic", "hidden", "internal", "off"].map((mode) => [mode, this.labels[mode]]);
      this.node("h3", "Readings", body);
      const readingRows = [];
      for (const [field, suffix] of [["readings", false], ["reading_suffixes", true]]) {
        for (const [name, setting] of Object.entries(target[field] ?? {})) {
          const data = typeof setting === "string" ? {mode: setting} : setting;
          const update = (values) => { target[field][name] = Object.assign(data, values); };
          readingRows.push({name: suffix ? "*" + name : name, data, update,
            remove: () => { delete target[field][name]; }});
        }
      }
      for (const item of (target.items ?? []).filter((entry) => entry.kind === "reading")) {
        readingRows.push({name: item.name, data: item, update: (values) => Object.assign(item, values),
          remove: () => { target.items = target.items.filter((entry) => entry !== item); }});
      }
      for (const row of readingRows) {
        const container = this.node("div", undefined, body);
        container.className = "row";
        selector(row.name, modes, row.data.mode, (mode) => { row.update({mode}); redraw(); }, container);
        this.button(this.labels.remove, container, () => { row.remove(); redraw(); });
        if (row.data.mode !== "binary") {
          this.readingMetadata(body, row.data.sensor_metadata, (metadata) => {
            delete row.data.unit_from;
            row.update({sensor_metadata: metadata});
          }, this.libraryData);
        }
      }
      if (roleId) {
        selector(tr("Übrige Readings", "Remaining readings"),
          [["", tr("Automatisch", "Automatic")], ...modes], target.remaining_readings ?? "", (value) => {
            if (value) target.remaining_readings = value;
            else delete target.remaining_readings;
          }, body);
      }
      if (target.binary?.length) this.node("p", tr("Binärsensor aus: ", "Binary sensor from: ") + target.binary.join(", "), body);
      if (target.electrical_readings) this.node("p", tr("Elektrische Messwerte automatisch erkennen", "Detect electrical readings automatically"), body);
      const newReading = input(tr("Reading-Name", "Reading name"), "", () => {}, body);
      this.button(tr("Reading hinzufügen", "Add reading"), body, () => {
        if (!newReading.value.trim()) return;
        target.items ??= [];
        const name = newReading.value.trim();
        const existing = target.items.some((item) => item.kind === "reading" && item.name === name);
        if (!existing && !(name in (target.readings ?? {}))) target.items.push({kind: "reading", name, mode: "sensor"});
        redraw();
      });
      this.node("h3", tr("Bedienelemente", "Controls"), body);
      if (roleId) {
        const layouts = {cover: "Rollladen", awning: "Markise", thermostat: "Thermostat",
          outlet: "Steckdose", switch: "Schaltaktor", dimmer: "Dimmer", level: "Analoger Ausgang",
          motion: "Bewegungsmelder", contact: "Kontakt", smoke: "Rauchmelder", remote: "Taster",
          weather: "Wettersensor", temperature: "Temperatur", meter: "Zähler", illuminance: "Helligkeit",
          display: "Display", metadata: "Gerätedaten", threshold: "Schwellenwerte"};
        selector(tr("Gerätedarstellung", "Device layout"),
          [["", tr("Ohne Vorgabe", "No override")], ...Object.entries(layouts).map(([key, label]) => [key, de ? label : key])],
          target.layout ?? "", (value) => { if (value) target.layout = value; else delete target.layout; }, body);
      }
      const controls = [
        ...(target.controls ?? []).map((item) => [item, "controls"]),
        ...(target.items ?? []).filter((item) => ["set", "get"].includes(item.kind)).map((item) => [item, "items"]),
      ];
      for (const [item, collection] of controls) {
        const box = this.node("details", undefined, body);
        this.node("summary", (item.label || item.name) + " · " + (item.kind ?? "set") + " " + item.name, box);
        input(tr("Anzeige", "Label"), item.label, (value) => { item.label = value; }, box);
        if (collection === "items") selector(tr("Bedienung", "Control"),
          ["button", "direct", "form", "select", "number", "number_slider", "text", "off"]
            .map((mode) => [mode, this.labels[mode] ?? mode]), item.mode, (mode) => { item.mode = mode; }, box);
        const property = collection === "controls" ? "modes" : "input_modes";
        input(tr("Eingaben (select, box, slider, text)", "Inputs (select, box, slider, text)"),
          (item[property] ?? []).join(", "), (value) => { item[property] = value.split(",").map((part) => part.trim()).filter(Boolean); }, box);
        input(tr("Reading für Rückmeldung", "Feedback reading"), item.reading, (value) => {
          if (value.trim()) item.reading = value.trim(); else delete item.reading;
        }, box);
        this.button(this.labels.remove, box, () => {
          target[collection] = target[collection].filter((entry) => entry !== item);
          redraw();
        });
      }
      const command = input(tr("FHEM-Befehlsname", "FHEM command name"), "", () => {}, body);
      const kind = selector(tr("Befehlsart", "Command kind"), [["set", "Set"], ["get", "Get"]], "set", () => {}, body);
      this.button(tr("Bedienelement hinzufügen", "Add control"), body, () => {
        const name = command.value.trim();
        if (!name || (target.items ?? []).some((item) => item.kind === kind.value && item.name === name)) return;
        target.items ??= [];
        target.items.push({kind: kind.value, name, label: name, mode: "button"});
        redraw();
      });
    };
    redrawRoles();
    redraw();

    const sourceSection = this.node("details", undefined, form);
    this.node("summary", tr("Einträge aus Gerät übernehmen", "Copy items from device"), sourceSection);
    sourceSection.open = Boolean(from);
    const compatible = references.filter((item) => !original || !(draft.match ?? []).length || item.compatible.includes(original.key));
    const formatSource = (item) => [item.name, item.channel, item.customizations.length
      ? tr("Anpassungen: ", "Customizations: ") + [...new Set(item.customizations)].join(", ") : null].filter(Boolean).join(" · ");
    const source = selector(tr("Passendes Gerät oder Kanal", "Compatible device or channel"),
      [["", tr("Auswählen", "Select")], ...[...compatible].sort((a, b) => a.name.localeCompare(b.name))
        .map((item) => [item.id, formatSource(item)])],
      compatible.some((item) => item.id === from) ? from : "", () => sourceResult.replaceChildren(), sourceSection);
    if (!compatible.length) this.node("p", tr("Kein passendes Gerät importiert.", "No compatible device imported."), sourceSection);
    const sourceResult = this.node("div", undefined, sourceSection);
    const chooseSource = async () => {
      sourceResult.replaceChildren();
      const item = compatible.find((entry) => entry.id === source.value);
      if (!item) return;
      try {
        const response = await this.libraryRequest("source", {source: item.id, ...(original ? {key: original.key} : {})});
        if (source.value !== item.id) return;
        const ruleId = new URLSearchParams(location.search).get("rule");
        const rule = response.rules.find((entry) => entry.id === ruleId);
        const items = {...(rule?.items ?? response.items)};
        if (!rule) {
          for (const [name, mode] of Object.entries(response.readings)) {
            items["reading:" + name] ??= {kind: "reading", name, mode};
          }
          if (response.layout && !["metadata", "threshold"].includes(response.layout) &&
              (!["cover", "awning"].includes(response.layout) || response.cover)) {
            items["layout:device"] = {kind: "layout", name: "device", mode: response.layout, arguments: response.cover ?? []};
          }
          for (const [kind, commands] of Object.entries(response.sections)) {
            for (const cmd of commands.filter((entry) => !entry.technical)) {
              const fields = cmd.fields;
              if (fields?.some((field) => !field.modes?.length)) continue;
              const input_modes = fields?.map((field) => field.modes[0]) ?? ["text"];
              items[kind + ":" + cmd.name + ":default"] ??= {kind, name: cmd.name, label: cmd.name,
                mode: !input_modes.length ? "button" : kind === "set" && input_modes.length === 1 ? "direct" : "form", input_modes};
            }
          }
        }
        const entries = Object.entries(items);
        this.node("p", item.name + " · " + entries.length + tr(" Einträge", " items"), sourceResult);
        if (!entries.length) this.node("p", tr("Dieses Gerät liefert keine übernehmbaren Einträge.", "This device has no items to copy."), sourceResult);
        const selected = entries.map(([key, entry]) => [key, entry,
          check(entry.kind + " · " + (entry.label || entry.name), Boolean(rule || (from && key in response.items)), () => {}, sourceResult)]);
        this.button(tr("Auswahl übernehmen", "Copy selection"), sourceResult, () => {
          if (response.role_id && draft.roles?.[response.role_id]) roleId = response.role_id;
          const target = draft.roles?.[roleId] ?? draft;
          target.items ??= [];
          const id = (entry) => entry.key ?? (entry.kind === "layout" ? "layout:device"
            : entry.kind + ":" + entry.name + (entry.kind === "reading" ? "" : ":" + (entry.variant ?? "default")));
          const imported = selected.filter(([, , box]) => box.checked);
          for (const [key, entry] of imported) {
            target.items = target.items.filter((previous) => id(previous) !== key);
            if (entry.kind === "reading" && target.readings) delete target.readings[entry.name];
            target.items.push(entry);
          }
          if (!original && !(draft.match ?? []).length) {
            draft.match = [{type: item.type, ...(item.model ? {models: [item.model]} : {}),
              ...(item.channel ? {channel: item.channel} : {})}];
            drawRules();
          }
          redrawRoles();
          redraw();
          this.show(imported.length + tr(" Einträge übernommen", " items copied"));
        });
      } catch (error) {
        this.show(error.message ?? String(error), true);
      }
    };
    this.button(tr("Gerät anzeigen", "Show device"), sourceSection, chooseSource);
    if (from && source.value) void chooseSource();

    this.node("h2", tr("Zuordnungsregeln", "Matching rules"), form);
    const automatic = check(tr("Als automatischen Standard verwenden", "Use as automatic default"),
      draft.automatic ?? Boolean(original && original.origin !== "custom"), (value) => { draft.automatic = value; });
    automatic.disabled = Boolean(original && original.origin !== "custom");
    const rules = this.node("div", undefined, form);
    const drawRules = () => {
      rules.replaceChildren();
      draft.match ??= [];
      for (const rule of draft.match) {
        const row = this.node("fieldset", undefined, rules);
        const field = (name, label) => input(label, rule[name], (value) => {
          if (value.trim()) rule[name] = value.trim(); else delete rule[name];
        }, row);
        field("type", "FHEM TYPE");
        input(tr("Modelle (Kommaliste)", "Models (comma separated)"), (rule.models ?? []).join(", "), (value) => {
          const models = value.split(",").map((name) => name.trim()).filter(Boolean);
          if (models.length) rule.models = models; else delete rule.models;
        }, row);
        field("channel", tr("Kanal", "Channel"));
        field("device", tr("Einzelne Geräte-ID (optional)", "Single device ID (optional)"));
        if (rule.readings?.length) this.node("p", "Readings · " + rule.readings.join(", "), row);
        if (rule.actions?.length) this.node("p", "Set · " + rule.actions.join(", "), row);
        const roleOptions = [["", tr("Standardrolle", "Default role")],
          ...Object.entries(draft.roles ?? {}).map(([key, role]) => [key, role.name])];
        if (roleOptions.length > 1) {
          selector(tr("Rolle für diese Regel", "Role for this rule"), roleOptions, rule.role ?? "", (value) => {
            if (value) rule.role = value; else delete rule.role;
          }, row);
          for (const [channel, role] of Object.entries(rule.channels ?? {})) {
            selector(tr("Kanal ", "Channel ") + channel, roleOptions, role, (value) => {
              if (value) rule.channels[channel] = value; else delete rule.channels[channel];
            }, row);
          }
          const channel = input(tr("Kanalnummer für Zuordnung", "Channel number to map"), "", () => {}, row);
          this.button(tr("Kanalrolle zuordnen", "Map channel role"), row, () => {
            if (!channel.value.trim()) return;
            rule.channels ??= {};
            rule.channels[channel.value.trim().padStart(2, "0")] = draft.default_role;
            drawRules();
          });
        }
        this.button(this.labels.remove, row, () => {
          draft.match = draft.match.filter((entry) => entry !== rule);
          drawRules();
        });
      }
    };
    drawRules();
    this.button(tr("Zuordnungsregel hinzufügen", "Add matching rule"), form, () => { draft.match.push({}); drawRules(); });
    this.button(this.labels.review, form, () => {
      const payload = () => {
        const data = {...draft, name: draft.name.trim(), match: draft.match.filter((rule) => Object.keys(rule).length)};
        if (!original || original.origin === "custom" || saveAsNew) data.automatic = automatic.checked;
        else if (!("automatic" in draft)) delete data.automatic;
        if (!data.match.length && !original) delete data.match;
        return data;
      };
      const snapshot = JSON.stringify(payload());
      const key = !saveAsNew && original ? original.key : null;
      review("edit", {draft: JSON.parse(snapshot), ...(key ? {key} : {})},
        () => JSON.stringify(payload()) === snapshot && (!saveAsNew && original ? original.key : null) === key);
    }).className = "primary";
  }

  renderPreviewRows(parent, rows) {
    const t = this.labels;
    const de = this._hass.locale?.language?.startsWith("de");
    const list = this.node("ul", undefined, parent);
    if (!rows.length) this.node("li", de ? "Keine aktuell zugewiesenen Geräte betroffen." : "No currently assigned devices affected.", list);
    for (const row of rows) {
      const item = this.node("li", row.name + " · " + row.changes + " " + t.changes, list);
      const skipped = Object.entries(row.skipped).map(([key, reason]) => key + " (" + reason + ")");
      const exceptions = row.customizations?.length
        ? [(de ? "Anpassungen haben Vorrang: " : "Customizations take precedence: ") + row.customizations.join(", ")] : [];
      if (row.samples?.length) {
        const samples = this.node("ul", undefined, item);
        samples.setAttribute("aria-label", de ? "Wertvorschau" : "Value preview");
        for (const sample of row.samples) {
          let value = sample.value ?? (de ? "Noch kein Wert empfangen" : "No value received yet");
          if (sample.value != null && sample.device_class === "temperature" && String(sample.value).trim() !== "" &&
              Number.isFinite(Number(sample.value))) {
            value = new Intl.NumberFormat(this._hass.locale?.language, {maximumFractionDigits: 1}).format(Number(sample.value));
          }
          this.node("li", sample.name + ": " + value + (sample.unit && sample.value != null ? " " + sample.unit : ""), samples);
        }
      }
      if (row.details.length || skipped.length || exceptions.length) {
        const details = this.node("ul", undefined, item);
        for (const description of [...row.details, ...skipped, ...exceptions]) this.node("li", description, details);
      }
    }
  }

  schedulePanel(main) {
    const t = this.labels;
    const detail = this.node("details", undefined, main);
    detail.open = true;
    this.node("summary", t.week, detail);
    const sources = this.data.sources.filter((source) => source.schedule);
    const bar = this.node("div", undefined, detail);
    bar.className = "row";
    const source = this.node("select", undefined, this.node("label", t.channel, bar));
    for (const item of sources) this.node("option", item.name, source).value = item.id;
    source.value = this.schedule?.source ?? sources.find((item) => item.id === this.data.source)?.id ?? sources[0].id;
    source.parentNode.hidden = sources.length === 1;
    const target = this.deviceId;
    const bridgeIdentifier = this.identifier;
    const call = (op, id, fields = {}) => this._hass.callWS({
      type: "fhem_bridge/thermostat", device_id: target, bridge_identifier: bridgeIdentifier, source: id, op, ...fields,
    });
    const status = this.node("p", "", detail);
    status.setAttribute("role", "status");
    const body = this.node("div", undefined, detail);
    const dirty = () => this.schedule && JSON.stringify(this.schedule.draft) !== this.schedule.original;
    const renderDraft = () => {
      body.replaceChildren();
      const state = this.schedule;
      if (!state) return;
      const {plan, draft} = state;
      const editable = plan.writable && !state.submitted;
      const fht = plan.family === "fht";
      this.node("p", plan.draft ? t.scheduleDraft : t.scheduleReported, body);
      this.node("p", fht ? t.scheduleFht : t.scheduleHm, body);
      if (state.submitted) this.node("p", t.scheduleAccepted, body);
      else if (plan.pending) this.node("p", t.schedulePending, body);
      else if (!editable) this.node("p", t.scheduleReadOnly, body);
      const field = (parent, label, value, options, onChange) => {
        const input = this.node("input", undefined, this.node("label", label, parent));
        Object.assign(input, options, {value, disabled: !editable || options.disabled});
        input.addEventListener("change", () => onChange(input));
        return input;
      };
      const number = {type: "number", step: 0.5, min: fht ? 5.5 : 5, max: fht ? 30.5 : 30};
      if (fht) {
        const row = this.node("div", undefined, body);
        row.className = "week-row";
        [t.dayTemp, t.nightTemp].forEach((label, index) => {
          field(row, label + " (°C)", draft.temperatures[index], number,
            (input) => { draft.temperatures[index] = input.value; });
        });
      }
      const dayNames = new Intl.DateTimeFormat(this._hass.locale?.language || "en", {
        weekday: "long", timeZone: "UTC",
      });
      const nameOf = (day) => dayNames.format(new Date(Date.UTC(2024, 0, 1 + weekDays.indexOf(day))));
      const timeToMinutes = (value) => {
        if (!/^\d{2}:\d{2}$/.test(value)) return NaN;
        const [hour, minute] = value.split(":").map(Number);
        return hour * 60 + minute;
      };
      for (const day of weekDays) {
        const card = this.node("details", undefined, body);
        card.open = state.open.has(day);
        card.addEventListener("toggle", () => card.open ? state.open.add(day) : state.open.delete(day));
        this.node("summary", nameOf(day), card);
        const intervals = draft.days[day];
        const timeline = this.node("div", undefined, card);
        timeline.className = "timeline";
        const draw = () => {
          timeline.replaceChildren();
          let start = 0;
          intervals.forEach(([first, second]) => {
            const from = fht ? timeToMinutes(first) : start;
            const to = timeToMinutes(fht ? second : first);
            if (!fht) start = to;
            if (!(to > from) || to > 1440 || (fht && to === 1440)) return;
            const block = this.node("span", undefined, timeline);
            block.style.flex = String(to - from);
            if (fht) {
              block.style.position = "absolute";
              block.style.insetInlineStart = `${from / 14.4}%`;
              block.style.width = `${(to - from) / 14.4}%`;
              block.style.height = "100%";
            }
            block.title = fht ? `${first}–${second}` : `${first} · ${second} °C`;
          });
        };
        if (fht) timeline.style.position = "relative";
        draw();
        for (const [index, interval] of intervals.entries()) {
          const row = this.node("div", undefined, card);
          row.className = "week-row";
          const end = index === intervals.length - 1;
          field(row, fht ? t.startTime : t.endTime, interval[0], {disabled: !fht && end}, (input) => {
            interval[0] = input.value;
            draw();
          });
          field(row, fht ? t.endTime : t.temperature, interval[1], fht ? {} : number, (input) => {
            interval[1] = input.value;
            draw();
          });
          if (editable && (fht || intervals.length > 1)) {
            this.button(fht ? t.disableWindow : t.remove, row, () => {
              if (fht) intervals[index] = ["24:00", "24:00"];
              else {
                intervals.splice(index, 1);
                if (end) intervals.at(-1)[0] = "24:00";
              }
              renderDraft();
            });
          }
        }
        if (!editable) continue;
        if (!fht && intervals.length < 13) {
          const start = intervals.length > 1 ? timeToMinutes(intervals.at(-2)[0]) : 0;
          const middle = Math.floor((start + 1440) / 10) * 5;
          if (middle > start && middle < 1440) this.button(t.addInterval, card, () => {
            const hour = String(Math.floor(middle / 60)).padStart(2, "0");
            const minute = String(middle % 60).padStart(2, "0");
            intervals.splice(-1, 0, [`${hour}:${minute}`, intervals.at(-1)[1]]);
            renderDraft();
          });
        }
        const copy = this.node("select", undefined, this.node("label", t.copyDay, card));
        this.node("option", t.choose, copy).value = "";
        for (const other of weekDays.filter((other) => other !== day)) {
          this.node("option", nameOf(other), copy).value = other;
        }
        copy.addEventListener("change", () => {
          if (!copy.value) return;
          draft.days[copy.value] = structuredClone(intervals);
          renderDraft();
        });
      }
      if (editable) this.button(t.saveWeek, body, async (event) => {
        if (plan.draft && !window.confirm(t.scheduleReplace)) return;
        const button = event.currentTarget;
        button.disabled = true;
        body.inert = true;
        load.disabled = source.disabled = true;
        status.textContent = "";
        status.classList.remove("error");
        try {
          const result = await call("write", state.source, {...draft, revision: plan.revision});
          if (this.schedule !== state) return;
          if (result.accepted.length) {
            state.submitted = true;
            state.original = JSON.stringify(draft);
            renderDraft();
          } else status.textContent = t.scheduleUnchanged;
        } catch (error) {
          status.textContent = error.message ?? String(error);
          status.classList.add("error");
        } finally {
          body.inert = false;
          button.disabled = load.disabled = source.disabled = false;
        }
      });
    };
    const load = this.button(t.loadWeek, bar, async () => {
      if (dirty() && !window.confirm(t.scheduleReload)) return;
      const id = source.value;
      load.disabled = source.disabled = true;
      status.textContent = "";
      status.classList.remove("error");
      try {
        const request = this.scheduleRequest?.source === id
          ? this.scheduleRequest
          : {source: id, promise: call("read", id)};
        this.scheduleRequest = request;
        let plan;
        try {
          plan = await request.promise;
        } finally {
          if (this.scheduleRequest === request) this.scheduleRequest = null;
        }
        if (this.deviceId !== target) return;
        const draft = {days: structuredClone(plan.days), temperatures: structuredClone(plan.temperatures)};
        this.schedule = {source: id, plan, draft, original: JSON.stringify(draft), open: new Set()};
        renderDraft();
      } catch (error) {
        status.textContent = error.message ?? String(error);
        status.classList.add("error");
      } finally {
        load.disabled = source.disabled = false;
      }
    });
    source.addEventListener("change", () => {
      if (dirty() && !window.confirm(t.scheduleReload)) {
        source.value = this.schedule.source;
        return;
      }
      this.schedule = null;
      body.replaceChildren();
      status.textContent = "";
    });
    renderDraft();
    if (!this.schedule) load.click();
  }

  section(main, kind, publicationOnly = false) {
    const t = this.labels;
    const detail = this.node("details", undefined, main);
    detail.open = kind === "set" || Boolean(this.selection[kind]);
    this.node("summary", t[kind], detail);
    const body = this.node("div", undefined, detail);
    body.className = "form";
    if (kind === "attr") this.node("p", t.attributeHelp, body);
    const entries = this.data.sections[kind];
    if (!entries.length) {
      this.node("p", t.noItems, body);
      return;
    }
    const search = this.node("input", undefined, body);
    search.type = "search";
    search.placeholder = t.search;
    search.setAttribute("aria-label", t[kind] + " " + t.search);
    const select = this.node("select", undefined, body);
    select.setAttribute("aria-label", t[kind]);
    const form = this.node("div", undefined, body);
    form.className = "form";
    const update = () => {
      const items = entries.filter((entry) => entry.name.toLowerCase().includes(search.value.toLowerCase()));
      select.replaceChildren();
      this.node("option", t.choose, select).value = "";
      if (kind === "attr") {
        for (const [label, configured] of [[t.used, true], [t.unused, false]]) {
          const matches = items.filter((item) => Object.hasOwn(this.data.attributes, item.name) === configured);
          if (!matches.length) continue;
          const group = this.node("optgroup", undefined, select);
          group.label = label;
          for (const item of matches) this.node("option", item.name, group).value = item.name;
        }
      } else {
        const favorites = kind === "set" ? this.data.favorites : [];
        const rank = (name) => favorites.includes(name) ? favorites.indexOf(name) : favorites.length;
        items.sort((a, b) => rank(a.name) - rank(b.name) || a.name.localeCompare(b.name));
        for (const item of items) this.node("option", item.name, select).value = item.name;
      }
      select.value = this.selection[kind] ?? "";
      if (select.selectedIndex < 0) select.value = "";
      draw();
    };
    const draw = () => {
      form.replaceChildren();
      const entry = entries.find((item) => item.name === select.value);
      if (entry) this.commandForm(form, kind, entry, publicationOnly);
    };
    search.addEventListener("input", update);
    select.addEventListener("change", () => {
      this.selection[kind] = select.value;
      draw();
    });
    update();
  }

  input(parent, field, value, index) {
    const t = this.labels;
    const label = this.node("label", t[field.label] ?? (t.arg + " " + (index + 1)), parent);
    let input;
    if (field.options && !field.custom && field.display !== "text") {
      input = this.node("select", undefined, label);
      input.multiple = field.type === "multiple";
      if (!input.multiple) this.node("option", t.choose, input).value = "";
      for (const option of field.options) this.node("option", option, input).value = option;
      if (input.multiple) {
        for (const option of input.options) option.selected = String(value ?? "").split(",").includes(option.value);
      } else if (value != null) {
        if (!field.options.includes(value)) this.node("option", value, input).value = value;
        input.value = value;
      }
    } else {
      input = this.node(field.multiline ? "textarea" : "input", undefined, label);
      if (!field.multiline) input.type = field.display !== "text" && ["number", "time", "date"].includes(field.type) ?
        field.type : "text";
      for (const key of ["min", "max", "step"]) if (field[key] !== undefined) input[key] = field[key];
      input.value = value ?? "";
      if (field.modes?.includes("slider") && field.display !== "text") {
        const slider = this.node("input", undefined, label);
        slider.type = "range";
        slider.setAttribute("aria-label", label.textContent + " · " + t.slider);
        for (const key of ["min", "max", "step"]) slider[key] = field[key];
        slider.value = input.value || field.min;
        slider.addEventListener("input", () => { input.value = slider.value; });
        input.addEventListener("input", () => { slider.value = input.value || field.min; });
      }
      if (field.options) {
        const list = this.node("datalist", undefined, label);
        list.id = "choices-" + uniqueId();
        input.setAttribute("list", list.id);
        for (const option of field.options) this.node("option", undefined, list).value = option;
      }
    }
    input.required = !field.optional;
    return input;
  }

  commandForm(parent, kind, entry, publicationOnly = false) {
    const t = this.labels;
    const configured = Object.hasOwn(this.data.attributes, entry.name);
    const previous = publicationOnly?.item;
    const value = kind === "attr" && configured ? this.data.attributes[entry.name] : undefined;
    const options = this.node("div", undefined, parent);
    options.className = "form";
    let raw;
    if (kind !== "attr" && entry.fields?.length) {
      raw = this.node("input", undefined, this.node("label", t.rawArgs, parent));
      raw.type = "checkbox";
      raw.checked = Boolean(previous?.arguments?.length && !previous.typed);
    }
    const inputs = [];
    const drawInputs = () => {
      options.replaceChildren();
      inputs.length = 0;
      if (!raw?.checked && entry.fields !== null) {
        entry.fields.forEach((field, index) => inputs.push(this.input(options, field,
          previous?.arguments?.[index] ?? (typeof value === "string" ? value : undefined), index)));
        return;
      }
      const addArgument = (initial = "", focus = true) => {
        const row = this.node("div", undefined, options);
        const input = this.input(row, {type: "text", optional: true}, initial, inputs.length);
        inputs.push(input);
        this.button("−", row, () => {
          inputs.splice(inputs.indexOf(input), 1);
          row.remove();
        }).setAttribute("aria-label", t.remove);
        if (focus) input.focus();
      };
      for (const argument of previous?.arguments ?? []) addArgument(argument, false);
      this.button(t.add, options, () => addArgument());
    };
    raw?.addEventListener("change", drawInputs);
    drawInputs();
    if (kind === "attr" && configured && typeof value !== "string") {
      this.node("p", t.current + ": " + JSON.stringify(value), parent);
    }
    const controls = this.node("div", undefined, parent);
    controls.className = "row";
    const allowed = this.data[{set: "writable", get: "query", attr: "edit_attributes"}[kind]];
    const needsTechnical = entry.technical && !this.data.technical;
    const usesRaw = () => Boolean(raw?.checked);
    const argumentsFor = (report = true) => {
      for (const input of inputs) if (!(report ? input.reportValidity() : input.checkValidity())) return null;
      const args = inputs.map((input) => input.multiple ?
        Array.from(input.selectedOptions, (option) => option.value).join(",") : input.value);
      return {key: kind === "attr" || usesRaw() ? "arguments" : "inputs", args};
    };
    if (publicationOnly) {
      this.pinForm(parent, kind, entry, argumentsFor, publicationOnly, options, raw);
      return;
    }
    const run = async (remove = false) => {
      const values = remove ? {args: []} : argumentsFor();
      if (!values) return;
      const target = this.targetKey;
      const channel = this.data.name;
      const request = Symbol();
      if (kind !== "attr") this.commandRequest = request;
      const showResult = (message, error = false) => {
        if (target !== this.targetKey) return;
        if (kind === "attr") {
          this.show(message, error);
        } else if (!this.bridgeEntry && this.commandRequest === request) {
          const label = kind === "get" ? t.getOutput : t.setOutput;
          this.commandResult = {target, title: [label, channel, entry.name].join(" · "), message, error};
          this.renderCommandResult();
        }
      };
      const buttons = controls.querySelectorAll("button:not(:disabled)");
      buttons.forEach((button) => button.disabled = true);
      try {
        const result = kind === "attr" ?
          await this.request("attribute", {attribute: entry.name, value: values.args[0] ?? "", remove}) :
          await this.request(kind, {command: entry.name, [values.key]: values.args});
        if (target !== this.targetKey) return;
        if (kind === "attr") await this.load(true);
        const fallback = kind === "get" ? t.noGetOutput : t.accepted;
        showResult((result.result ?? fallback) + (result.truncated ? "\n" + t.truncated : ""));
      } catch (error) {
        showResult(error.message ?? String(error), true);
      } finally {
        buttons.forEach((button) => button.disabled = false);
      }
    };
    const primary = this.button(kind === "attr" ? t.save : t.run, controls, () => run());
    primary.className = "primary";
    primary.disabled = !allowed || needsTechnical;
    if (kind === "attr" && configured) {
      this.button(t.remove, controls, () => {
        if (window.confirm(t.confirm)) void run(true);
      }).disabled = !allowed;
    }
    if (!allowed || needsTechnical) {
      this.node("small", needsTechnical ? t.technical : t.denied, parent);

    }
    if (kind === "attr" && !allowed) inputs.forEach((input) => input.disabled = true);
    if (kind !== "attr") {
      const output = this.node("div", undefined, parent);
      this.button(t.automation, controls, () => {
        this.automation(output, kind, entry, argumentsFor(false));
      });
    }
  }

  publishRequest(op, fields = {}) {
    return this._hass.callWS({type: "fhem_bridge/publications", ...this.deviceTarget, op, ...fields});
  }

  stage(...items) {
    for (const item of items) {
      const key = ["reading", "layout"].includes(item.kind) ? item.kind + ":" + item.name :
        [item.kind, item.name, item.variant ?? "default"].join(":");
      this.draft.set(key, item);
    }
    this.invalidatePreview();
  }

  invalidatePreview() {
    this.previewVersion = (this.previewVersion ?? 0) + 1;
    this.previewResult?.replaceChildren();
    this.updatePending();
  }

  updatePending() {
    const count = this.draft.size + Number(Boolean(this.templateDraft));
    if (this.pendingText?.isConnected) {
      const de = this._hass.locale?.language?.startsWith("de");
      this.pendingText.textContent = count ? (de ? (count === 1 ? "1 Änderung offen" : count + " Änderungen offen")
        : (count === 1 ? "1 pending change" : count + " pending changes"))
        : (de ? "Keine ausstehenden Änderungen" : "No pending changes");
      this.changeFooter.toggleAttribute("data-pending", count > 0);
      this.reviewButton.disabled = !count;
      this.discardButton.hidden = !count;
    }
    for (const marker of this.shadowRoot.querySelectorAll("[data-publication-key]")) {
      this.updatePendingItem(marker);
    }
  }

  updatePendingItem(marker) {
    const item = this.draft.get(marker.dataset.publicationKey);
    marker.hidden = !item;
    marker.textContent = item?.mode === "off" ? this.labels.pendingRemoval : this.labels.pendingItem;
  }

  pendingItem(parent, key) {
    const marker = this.node("small", undefined, parent);
    marker.className = "pending-item";
    marker.dataset.publicationKey = key;
    this.updatePendingItem(marker);
  }

  customInputs(parent, previous) {
    const t = this.labels;
    const countLabel = this.node("label", t.inputCount, parent);
    const count = this.node("input", undefined, countLabel);
    count.type = "number";
    count.min = 1;
    count.max = 32;
    count.value = previous?.input_modes?.length || 1;
    count.required = true;
    const rows = [];
    const draw = () => {
      if (!count.checkValidity()) return;
      while (rows.length > count.valueAsNumber) rows.pop().row.remove();
      while (rows.length < count.valueAsNumber) {
        const old = previous?.input_fields?.[rows.length];
        const row = this.node("fieldset", undefined, parent);
        this.node("legend", t.arg + " " + (rows.length + 1), row);
        const label = this.node("input", undefined, this.node("label", t.label, row));
        label.maxLength = 80;
        label.value = old?.label ?? "";
        const mode = this.node("select", undefined, row);
        mode.setAttribute("aria-label", t.arg + " " + (rows.length + 1));
        for (const option of ["text", "select", "box", "slider"]) this.node("option", t[option], mode).value = option;
        mode.value = previous?.input_modes?.[rows.length] ?? "text";
        const choices = this.node("label", t.optionValues, row);
        const options = this.node("textarea", undefined, choices);
        options.value = old?.options?.join("\n") ?? "";
        const bounds = this.node("div", undefined, row);
        const numbers = Object.fromEntries([["min", t.minValue], ["max", t.maxValue], ["step", t.stepValue]].map(
          ([key, caption]) => {
            const input = this.node("input", undefined, this.node("label", caption, bounds));
            input.type = "number";
            input.step = "any";
            input.value = old?.[key] ?? "";
            return [key, input];
          }
        ));
        const show = () => {
          choices.hidden = mode.value !== "select";
          bounds.hidden = !["box", "slider"].includes(mode.value);
        };
        mode.addEventListener("change", show);
        show();
        rows.push({row, label, mode, options, numbers});
      }
    };
    count.addEventListener("input", draw);
    draw();
    const read = () => {
      if (!count.reportValidity()) return null;
      const fields = [];
      for (const row of rows) {
        const mode = row.mode.value;
        const field = {type: mode === "select" || mode === "text" ? mode : "number", label: row.label.value.trim()};
        if (mode === "select") field.options = row.options.value.split("\n").map((value) => value.trim()).filter(Boolean);
        if (field.type === "number") {
          for (const [key, input] of Object.entries(row.numbers)) {
            input.required = true;
            if (!input.reportValidity()) return null;
            field[key] = input.valueAsNumber;
          }
        }
        fields.push(field);
      }
      return {input_fields: fields, input_modes: rows.map((row) => row.mode.value)};
    };
    return {
      read,
      single(enabled) {
        countLabel.hidden = enabled;
        if (enabled) {
          count.value = 1;
          draw();
        }
        for (const row of rows) row.label.parentElement.hidden = enabled;
      },
    };
  }

  pinForm(parent, kind, entry, argumentsFor, context, fixedFields, raw) {
    const t = this.labels;
    const choices = this.publication.sections[kind].find((item) => item.name === entry.name)?.modes ?? ["button"];
    const key = [kind, entry.name, "default"].join(":");
    const previous = context.item;
    const de = this._hass.locale?.language?.startsWith("de");
    const form = this.node("div", undefined, parent);
    form.className = "form";
    const name = this.node("input", undefined, this.node("label", t.label, form));
    name.value = previous?.label || entry.name;
    name.required = true;
    name.maxLength = 100;
    const mode = this.node("select", undefined, this.node("label", de ? "Darstellung" : "Presentation", form));
    for (const option of choices) this.node("option", t[option], mode).value = option;
    if (choices.includes(previous?.mode)) mode.value = previous.mode;
    const feedbackLabel = this.node("label", kind === "get" ? t.observeReading : t.feedback, form);
    const feedback = this.node("select", undefined, feedbackLabel);
    this.node("option", t.choose, feedback).value = "";
    for (const reading of Object.keys(this.publication.readings).sort()) {
      this.node("option", reading, feedback).value = reading;
    }
    feedback.value = previous?.reading ??
      (kind === "set" && Object.hasOwn(this.publication.readings, entry.name) ? entry.name : "");
    const useFeedback = () => ["select", "number", "number_slider", "text"].includes(mode.value);
    const inputs = this.node("div", undefined, form);
    const inputHelp = this.node("small", t.localInputs, inputs);
    const inputModes = [];
    const custom = entry.fields === null ? this.customInputs(inputs, previous) : null;
    for (const [index, field] of (entry.fields ?? []).entries()) {
      const select = this.node("select", undefined,
        this.node("label", t[field.label] ?? (t.arg + " " + (index + 1)), inputs));
      for (const option of field.modes) this.node("option", t[option], select).value = option;
      const preferred = previous?.input_modes?.[index] ?? field.display;
      if (field.modes.includes(preferred)) select.value = preferred;
      inputModes.push(select);
    }
    const fixed = this.node("div", undefined, form);
    if (raw) fixed.append(raw.parentElement);
    fixed.append(fixedFields);
    const showMode = () => {
      fixed.hidden = mode.value !== "button";
      const direct = mode.value === "direct";
      feedbackLabel.hidden = kind !== "get" && !useFeedback();
      inputs.hidden = mode.value !== "form" && !direct;
      inputHelp.textContent = direct ? t.directInput : t.localInputs;
      custom?.single(direct);
    };
    mode.addEventListener("change", showMode);
    showMode();
    const visibility = this.node("select", undefined, this.node("label", de ? "Sichtbarkeit" : "Visibility", form));
    this.node("option", de ? "Auf der HA-Geräteseite" : "On HA device page", visibility).value = "shown";
    this.node("option", de ? "Ausgeblendet · für Automationen verfügbar" : "Hidden · available for automations", visibility).value = "hidden";
    visibility.value = previous?.hidden ? "hidden" : "shown";
    this.button(previous ? (de ? "Änderung übernehmen" : "Update draft") : (de ? "Hinzufügen" : "Add"), form, () => {
      if (!name.reportValidity()) return;
      const values = mode.value === "button" ? argumentsFor() : {args: []};
      if (!values) return;
      const usesInputs = mode.value === "form" || mode.value === "direct";
      const formInputs = !usesInputs ? {} : custom ? custom.read() : {
        input_modes: inputModes.map((select) => select.value),
      };
      if (!formInputs) return;
      if (useFeedback() && !feedback.value) {
        this.show(t.feedback + " – " + t.choose, true);
        return;
      }
      this.stage({kind, name: entry.name, mode: mode.value, label: name.value,
        arguments: values.args, typed: values.key === "inputs",
        hidden: visibility.value === "hidden",
        variant: previous?.variant ?? ((this.publication.choices[key] || this.draft.has(key)) ? uniqueId() : "default"),
        ...formInputs,
        ...(useFeedback() || (kind === "get" && feedback.value) ? {reading: feedback.value} : {})});
      context.close();
    }).className = "primary";
  }

  matchingPublicationRules(publication = this.publication) {
    return publication.rules.filter((rule) => rule.scope === this.scope &&
      Boolean(rule.assignment) === (this.publicationMode === "assignment"));
  }

  publicationPanel(main) {
    const de = this._hass.locale?.language?.startsWith("de");
    const tr = (german, english) => de ? german : english;
    const tab = this.deviceTab ?? "template";
    this.node("h2", tr("Geräteseite gestalten", "Customize device page"), main);
    const [module, model] = this.publication.class;
    const className = this.publication.templates[this.publication.automatic_template]?.name ?? module;
    this.node("p", tr("Geräteklasse: ", "Device class: ") + [className, model].filter(Boolean).join(" · "), main);
    const tabs = this.node("nav", undefined, main);
    tabs.className = "view-tabs";
    tabs.setAttribute("aria-label", tr("Konfigurationsbereiche", "Configuration sections"));
    for (const [key, name] of [["template", tr("Vorlage", "Template")], ["readings", "Readings"],
      ["commands", tr("Bedienelemente", "Controls")]]) {
      const button = this.button(name, tabs, () => {
        this.deviceTab = key;
        this.render();
        this.shadowRoot.querySelector('[data-device-tab="' + key + '"]')?.focus();
      });
      button.dataset.deviceTab = key;
      button.setAttribute("aria-pressed", String(tab === key));
    }
    if (tab === "template") {
      this.templateTab(main, tr);
      return;
    }
    if (tab === "readings") this.readingPanel(main);
    else this.commandTab(main, tr);

  }

  templateTab(parent, tr) {
    const {assignment, effective_template, automatic_template, templates, template_disabled} = this.publication;
    const automatic = tr("Automatisch", "Automatic");
    const none = tr("Keine Vorlage", "No template");
    const inferred = templates[automatic_template]?.name ?? tr("Keine passende Vorlage", "No matching template");
    const legacy = assignment?.items["layout:device"];
    const actual = template_disabled ? none : assignment?.template
      ? templates[assignment.template]?.name ?? none
      : legacy ? this.publication.role ?? this.publication.layout
      : automatic + " · " + inferred;
    const section = this.node("section", undefined, parent);
    section.className = "editor-card form";
    this.node("h3", tr("Aktuell verwendet", "Currently applied"), section);
    this.node("p", actual + (assignment?.template || legacy ? tr(" · manuell gewählt", " · selected manually") : ""), section);
    const select = this.node("select", undefined, this.node("label", tr("Vorlage für ", "Template for ") + this.data.name, section));
    this.node("option", automatic + " · " + inferred, select).value = "auto";
    this.node("option", none, select).value = "none";
    for (const [key, item] of Object.entries(templates).sort(([, a], [, b]) => a.name.localeCompare(b.name))) {
      this.node("option", item.name, select).value = "template:" + key;
    }
    const travel = this.node("optgroup", undefined, select);
    travel.label = tr("Erweiterte Fahrbefehle", "Advanced travel commands");
    this.node("option", tr("Rollladen · Fahrbefehle anpassen", "Shutter · Custom commands"), travel).value = "cover";
    this.node("option", tr("Markise · Fahrbefehle anpassen", "Awning · Custom commands"), travel).value = "awning";
    if (legacy && !["cover", "awning"].includes(legacy.mode)) {
      this.node("option", tr("Bisherige Auswahl · ", "Previous selection · ") + (this.publication.role ?? legacy.mode), select).value = legacy.mode;
    }
    const saved = template_disabled ? "none" : assignment?.template ? "template:" + assignment.template : legacy?.mode ?? "auto";
    select.value = this.templateDraft?.key ? "template:" + this.templateDraft.key
      : this.templateDraft?.disabled ? "none" : this.templateDraft?.layout?.mode ?? (this.templateDraft ? "auto" : saved);
    const mapping = this.node("div", undefined, section);
    const drawMapping = (stored = []) => {
      mapping.replaceChildren();
      if (!["cover", "awning"].includes(select.value)) return [];
      const available = this.publication.sections.set.filter((item) => !item.technical && item.fields?.every((field) => field.optional));
      const awning = select.value === "awning";
      const candidates = awning ? [["open", "extend", "down"], ["close", "retract", "up"], ["stop"]]
        : [["open", "up"], ["close", "down"], ["stop"]];
      if (this.data.type === "FS20") {
        candidates[0].push(awning ? "off" : "on");
        candidates[1].push(awning ? "on" : "off");
      }
      return [tr("Öffnen", "Open"), tr("Schließen", "Close"), tr("Stopp (optional)", "Stop (optional)")].map((label, index) => {
        const field = this.node("select", undefined, this.node("label", label, mapping));
        this.node("option", "–", field).value = "";
        for (const item of available) this.node("option", item.name, field).value = item.name;
        field.value = stored[index] ?? candidates[index].find((name) => available.some((item) => item.name === name)) ?? "";
        field.addEventListener("change", stage);
        return field;
      });
    };
    let fields;
    const stage = () => {
      const mode = select.value;
      const args = fields.map((field) => field.value);
      this.templateDraft = mode === saved && (!args.length || args.every((value, index) => value === legacy?.arguments?.[index]))
        ? null : {disabled: mode === "none", ...(mode.startsWith("template:") ? {key: mode.slice(9)} : {}),
          ...(args.length ? {layout: {kind: "layout", name: "device", mode, arguments: args}} : {})};
      this.invalidatePreview();
    };
    fields = drawMapping(this.templateDraft?.layout?.arguments ?? (select.value === legacy?.mode ? legacy.arguments : []));
    select.addEventListener("change", () => {
      fields = drawMapping(select.value === legacy?.mode ? legacy.arguments : []);
      stage();
    });
    if (effective_template) {
      const link = this.node("a", tr("Gemeinsame Vorlage im Vorlageneditor öffnen ↗", "Open shared template in editor ↗"), section);
      link.href = this.libraryLink(effective_template, this.publication.bridge_entry_id,
        {device: this.identifier, source: this.data.source});
    }
  }

  commandTab(parent, tr) {
    const header = this.node("div", undefined, parent);
    header.className = "section-heading";
    this.node("h3", tr("Veröffentlichte Befehle", "Published commands"), header);
    this.button(tr("+ Bedienelement hinzufügen", "+ Add control"), header, () => {
      this.commandEditor = {adding: true};
      this.render();
      this.shadowRoot.querySelector("#control-editor")?.focus();
    });
    const commands = {...this.publication.choices};
    for (const [key, item] of this.draft) if (["set", "get"].includes(item.kind)) commands[key] = {...commands[key], ...item};
    const rows = Object.entries(commands).filter(([key, item]) =>
      ["set", "get"].includes(item.kind) && (item.mode !== "off" || this.draft.has(key)));
    if (!rows.length) this.node("p", tr("Für diesen Kanal sind keine Befehle veröffentlicht.", "No commands are published for this channel."), parent);
    if (rows.length) {
      const table = this.node("table", undefined, parent);
      table.className = "commands-table";
      table.setAttribute("aria-label", tr("Veröffentlichte Befehle", "Published commands"));
      const head = this.node("tr", undefined, this.node("thead", undefined, table));
      const labels = [tr("Name", "Name"), tr("FHEM-Befehl", "FHEM command"), tr("Darstellung", "Presentation"),
        tr("Sichtbarkeit", "Visibility"), tr("Herkunft", "Source")];
      for (const label of labels) this.node("th", label, head).scope = "col";
      const body = this.node("tbody", undefined, table);
      for (const [key, item] of rows) {
        const saved = this.publication.choices[key];
        const current = ["inherit", "off"].includes(item.mode) ? saved ?? item : item;
        if (!current) continue;
        const row = this.node("tr", undefined, body);
        const label = current.label || current.name;
        const nameCell = this.node("td", undefined, row);
        const edit = this.button(label, nameCell, () => {
          this.commandEditor = {key};
          this.render();
          this.shadowRoot.querySelector("#control-editor")?.focus();
        });
        edit.className = "edit-name";
        edit.setAttribute("aria-label", tr("Bearbeiten: ", "Edit: ") + label);
        this.node("span", " ✎", edit).setAttribute("aria-hidden", "true");
        if (this.publication.skipped[key] || this.publication.blocked?.[key]) {
          const reason = this.publication.skipped[key] || this.labels.locked;
          this.node("small", reason, nameCell);
        }
        if (this.draft.has(key)) {
          const text = item.mode === "off" ? tr("Entfernt", "Removed") : saved ? tr("Geändert", "Changed") : tr("Neu", "New");
          this.node("span", text, nameCell).className = "draft-badge";
        }
        const visibility = current.hidden ? tr("Ausgeblendet", "Hidden") : tr("HA-Geräteseite", "HA device page");
        for (const [index, value] of [
          current.kind + " " + current.name, this.labels[current.mode] ?? current.mode, visibility,
        ].entries()) {
          const cell = this.node("td", value, row);
          cell.dataset.label = labels[index + 1];
          if (!index) cell.className = "command-code";
        }
        const provenance = this.node("td", undefined, row);
        provenance.dataset.label = labels[4];
        this.settingOrigin(provenance, key, label);
      }
    }
    if (!this.commandEditor) return;
    const editor = this.node("section", undefined, parent);
    editor.className = "editor-card form";
    editor.id = "control-editor";
    editor.tabIndex = -1;
    const close = () => { this.commandEditor = null; this.render(); };
    const editing = this.commandEditor.key ? commands[this.commandEditor.key] : null;
    this.node("h3", editing ? tr("Bedienelement ändern", "Edit control") : tr("Bedienelement hinzufügen", "Add control"), editor);
    const form = this.node("div", undefined, editor);
    form.className = "form";
    const showCommand = (kind, name, item = null) => {
      form.replaceChildren();
      const entry = this.publication.sections[kind].find((command) => command.name === name);
      if (entry) this.commandForm(form, kind, entry, {item, close});
      else if (item) this.node("p", tr("Dieser FHEM-Befehl ist derzeit nicht verfügbar.", "This FHEM command is currently unavailable."), form);
    };
    if (editing) {
      const item = editing.mode === "inherit" ? this.publication.choices[this.commandEditor.key] : editing;
      this.node("p", item.kind + " " + item.name, editor);
      showCommand(item.kind, item.name, item);
      const actions = this.node("div", undefined, editor);
      actions.className = "row";
      const key = this.commandEditor.key;
      const change = (mode) => {
        const {kind, name, variant} = item;
        if (mode === "off" && !this.publication.choices[key]) {
          this.draft.delete(key);
          this.invalidatePreview();
        } else this.stage({kind, name, variant, mode});
        close();
      };
      this.button(tr("Entfernen", "Remove"), actions, () => change("off"));
      if (this.publication.rules.some((rule) => rule.applies && !rule.assignment && rule.scope === "device" && key in rule.items)) {
        this.button(tr("Vorlagenwert wiederherstellen", "Restore template value"), actions, () => change("inherit"));
      }
    } else {
      const type = this.node("select", undefined, this.node("label", tr("Befehlsart", "Command type"), editor));
      this.node("option", "Set", type).value = "set";
      this.node("option", "Get", type).value = "get";
      const pick = this.node("select", undefined, this.node("label", tr("FHEM-Befehl", "FHEM command"), editor));
      editor.append(form);
      const fill = () => {
        pick.replaceChildren();
        this.node("option", this.labels.choose, pick).value = "";
        for (const item of [...this.publication.sections[type.value]].sort((a, b) => a.name.localeCompare(b.name))) {
          this.node("option", item.name, pick).value = item.name;
        }
        form.replaceChildren();
      };
      type.addEventListener("change", fill);
      pick.addEventListener("change", () => showCommand(type.value, pick.value));
      fill();
    }
    this.button(tr("Abbrechen", "Cancel"), editor, close);
  }

  readingPanel(parent) {
    const t = this.labels;
    const de = this._hass.locale?.language?.startsWith("de");
    const detail = this.node("section", undefined, parent);
    const heading = this.node("div", undefined, detail);
    heading.className = "section-heading";
    this.node("h3", de ? "Readings auf der HA-Geräteseite" : "Readings on the HA device page", heading);
    const search = this.node("input", undefined, detail);
    search.type = "search";
    search.placeholder = t.search;
    search.setAttribute("aria-label", t.reading);
    const modes = ["sensor", "binary", "diagnostic", "hidden", "internal", "off", "inherit"];
    const filter = this.node("select", undefined, this.node("label", t.readingFilter, detail));
    this.node("option", t.allModes, filter).value = "";
    for (const option of modes.slice(0, -1)) this.node("option", t[option], filter).value = option;
    const choose = (parent, value) => {
      const select = this.node("select", undefined, parent);
      for (const option of modes) this.node("option", option === "inherit" ? t.reset : t[option], select).value = option;
      select.value = value;
      return select;
    };
    const bulk = this.node("div", undefined, detail);
    const rows = this.node("div", undefined, detail);
    bulk.className = "row";
    const bulkMode = choose(bulk, "sensor");
    const readingMode = (name) => this.draft.get("reading:" + name)?.mode ||
      this.publication.readings[name];
    let includeInactive = false;
    const toggle = this.button(de ? "+ Reading hinzufügen" : "+ Add reading", heading, () => {
      includeInactive = !includeInactive;
      toggle.textContent = includeInactive ? (de ? "Nur veröffentlichte Readings" : "Published readings only")
        : (de ? "+ Reading hinzufügen" : "+ Add reading");
      draw();
      if (includeInactive) search.focus();
    });
    const headings = this.node("div", undefined, detail);
    headings.className = "reading-row reading-headings";
    for (const label of ["Reading", de ? "Anzeige" : "Display", de ? "Einstellung stammt aus" : "Setting source"]) {
      this.node("strong", label, headings);
    }
    detail.append(rows);
    const active = ["sensor", "binary", "diagnostic"];
    const visible = () => Object.keys(this.publication.readings).filter((name) =>
      (includeInactive || search.value || filter.value || active.includes(readingMode(name)) || this.draft.has("reading:" + name)) &&
      name.toLowerCase().includes(search.value.toLowerCase()) && (!filter.value || filter.value === readingMode(name))
    ).sort();
    const draw = () => {
      rows.replaceChildren();
      for (const name of visible()) {
        const value = this.publication.values[name];
        const feedback = this.publication.required.includes(name) ? " · " + t.requiredReading : "";
        const key = "reading:" + name;
        const row = this.node("div", undefined, rows);
        row.className = "reading-row";
        const identity = this.node("div", undefined, row);
        this.node("strong", name, identity);
        if (value != null || feedback) this.node("small", (value == null ? "" : String(value)) + feedback, identity);
        const select = choose(row, readingMode(name));
        select.setAttribute("aria-label", name + " · " + (de ? "Anzeige" : "Display"));
        this.settingOrigin(row, key, name);
        if (readingMode(name) === "inherit") this.node("small", de ? "Wird zurückgesetzt" : "Reset pending", identity);
        this.pendingItem(row, key);
        if (readingMode(name) !== "binary" && readingMode(name) !== "inherit") {
          const metadata = this.draft.get(key)?.sensor_metadata ?? this.publication.choices[key]?.sensor_metadata;
          this.readingMetadata(row, metadata, (sensor_metadata) => {
            this.stage({kind: "reading", name, mode: select.value, sensor_metadata});
          }, this.publication);
        }
        select.addEventListener("change", () => {
          const metadata = this.draft.get(key)?.sensor_metadata;
          this.stage({kind: "reading", name, mode: select.value,
            ...(select.value !== "inherit" && metadata ? {sensor_metadata: metadata} : {})});
          draw();
          [...rows.querySelectorAll("select")].find((field) => field.getAttribute("aria-label") === select.getAttribute("aria-label"))?.focus();
        });
      }
    };
    this.button(t.allFiltered, bulk, () => {
      this.stage(...visible().map((name) => {
        const metadata = this.draft.get("reading:" + name)?.sensor_metadata;
        return {kind: "reading", name, mode: bulkMode.value,
          ...(bulkMode.value !== "inherit" && metadata ? {sensor_metadata: metadata} : {})};
      }));
      draw();
    });
    search.addEventListener("input", draw);
    filter.addEventListener("change", draw);
    draw();
  }

  readingMetadata(parent, metadata, update, catalog) {
    if (!catalog?.sensor_classes) return;
    const de = this._hass.locale?.language?.startsWith("de");
    const tr = (deText, enText) => de ? deText : enText;
    const details = this.node("details", undefined, parent);
    details.className = "reading-metadata";
    const summary = this.node("summary", undefined, details);
    const body = this.node("div", undefined, details);
    body.className = "row";
    let data = {...metadata};
    const summarize = () => {
      const fields = [data.device_class, data.state_class, data.unit_of_measurement].filter(Boolean);
      summary.textContent = tr("Sensordaten", "Sensor metadata") + (fields.length ? " · " + fields.join(" · ") : "");
    };
    const select = (title, options, value, change, labelFor = (option) => option) => {
      const field = this.node("select", undefined, this.node("label", title, body));
      this.node("option", tr("Ohne", "None"), field).value = "";
      for (const option of options) this.node("option", labelFor(option), field).value = option;
      field.value = value ?? "";
      field.addEventListener("change", () => change(field.value));
    };
    const save = (key, value) => {
      if (value) data[key] = value;
      else delete data[key];
      summarize();
      update({...data});
    };
    const render = () => {
      body.replaceChildren();
      select(tr("Geräteklasse", "Device class"), Object.keys(catalog.sensor_classes).sort(), data.device_class, (value) => {
        const {unit_of_measurement: unit, state_class: stateClass} = data;
        const limits = catalog.sensor_classes[value];
        data = {};
        if (stateClass && (!limits || limits.state_classes.includes(stateClass))) data.state_class = stateClass;
        if (unit && (!limits || limits.units.includes(unit) || value === "monetary" && /^[A-Z]{3}$/.test(unit))) {
          data.unit_of_measurement = unit;
        }
        save("device_class", value);
        render();
        body.querySelector("select")?.focus();
      }, (option) => this._hass.localize(`component.sensor.entity_component.${option}.name`) || option);
      const limits = catalog.sensor_classes[data.device_class];
      select(tr("Zustandsklasse", "State class"), limits?.state_classes ?? catalog.sensor_state_classes,
        data.state_class, (value) => save("state_class", value));
      if (limits?.units.length) {
        select(tr("Quelleinheit", "Source unit"), limits.units, data.unit_of_measurement,
          (value) => save("unit_of_measurement", value));
      } else if (!limits || data.device_class === "monetary") {
        const unit = this.node("input", undefined, this.node("label", tr("Quelleinheit", "Source unit"), body));
        unit.value = data.unit_of_measurement ?? "";
        unit.maxLength = data.device_class === "monetary" ? 3 : 64;
        unit.addEventListener("change", () => {
          const value = unit.value.trim();
          save("unit_of_measurement", data.device_class === "monetary" ? value.toUpperCase() : value);
        });
      }
    };
    summarize();
    render();
  }

  settingOrigin(parent, key, label) {
    const de = this._hass.locale?.language?.startsWith("de");
    const rank = {type: 0, class: 1, selected: 2, device: 3};
    const rule = this.publication.rules.filter((entry) => entry.applies && !entry.assignment && key in entry.items)
      .sort((a, b) => rank[b.scope] - rank[a.scope] || Number(a.future) - Number(b.future))[0];
    const block = this.node("div", undefined, parent);
    block.className = "setting-origin";
    if (rule?.scope === "device") {
      this.node("span", de ? "Einzelanpassung für " + this.data.name : "Customized for " + this.data.name, block);
      if (key.startsWith("reading:")) this.button(de ? "Zurücksetzen" : "Reset", block, () => {
        this.stage({kind: "reading", name: key.slice(8), mode: "inherit"});
        this.render();
      });
    } else if (rule) {
      this.node("span", (de ? "Gemeinsame Anpassung" : "Shared customization") + " · " +
        rule.affected.length + (de ? " Geräte" : " devices"), block);
      this.button("Details", block, () => this.sharedDetails(rule, label));
    } else {
      this.node("span", key in this.publication.choices ? (de ? "Aus Vorlage" : "From template")
        : (de ? "Bridge-Standardeinstellung" : "Bridge default"), block);
    }
  }

  sharedDetails(rule, label) {
    const de = this._hass.locale?.language?.startsWith("de");
    const dialog = this.node("dialog", undefined, this.shadowRoot);
    this.node("h3", (de ? "Gemeinsame Anpassung · " : "Shared customization · ") + label, dialog);
    this.node("p", (de ? "Gilt aktuell für " : "Currently applies to ") + rule.affected.length + (de ? " Geräte" : " devices") +
      (rule.future ? (de ? " sowie künftig importierte passende Geräte." : " and future matching imports.") : "."), dialog);
    this.node("p", rule.affected.join(", "), dialog);
    this.node("p", (de ? "Enthaltene Einstellungen: " : "Included settings: ") +
      Object.values(rule.items).map((item) => item.label || item.name).join(", "), dialog);
    const actions = this.node("div", undefined, dialog);
    actions.className = "row";
    this.button(de ? "Schließen" : "Close", actions, () => dialog.close());
    this.button(de ? "Geltungsbereich ändern" : "Change scope", actions, () => {
      dialog.close();
      this.previewPublication(rule);
    }).className = "primary";
    dialog.addEventListener("close", () => dialog.remove(), {once: true});
    dialog.showModal();
  }

  changeBar(main) {
    const t = this.labels;
    this.changeFooter = this.node("footer", undefined, main);
    this.changeFooter.className = "change-bar";
    const actions = this.node("div", undefined, this.changeFooter);
    actions.className = "row";
    this.pendingText = this.node("strong", undefined, actions);
    this.pendingText.setAttribute("role", "status");
    this.reviewButton = this.button(t.review, actions, () => this.previewPublication());
    this.reviewButton.className = "primary";
    this.discardButton = this.button(t.discard, actions, () => {
      this.draft.clear();
      this.templateDraft = null;
      this.commandEditor = null;
      this.future = this.publication.rules.find((rule) => rule.id === this.ruleId)?.future ?? (this.scope !== "device");
      this.render();
    });
    this.previewResult = this.node("div", undefined, this.changeFooter);
    this.previewResult.className = "change-preview";
    this.updatePending();
  }

  previewPublication(shared = null) {
    if (!this.draft.size && !this.templateDraft && !shared) return;
    const t = this.labels;
    const de = this._hass.locale?.language?.startsWith("de");
    const travel = this.templateDraft?.layout?.arguments;
    if (!shared && travel && (!travel[0] || !travel[1] || travel[0] === travel[1])) {
      this.show(de ? "Wähle verschiedene Befehle für Öffnen und Schließen." : "Choose distinct commands for opening and closing.", true);
      return;
    }
    const output = this.previewResult;
    output.replaceChildren();
    this.node("h3", (de ? "Änderungen prüfen · " : "Review changes · ") + this.data.name, output);
    const group = this.node("fieldset", undefined, output);
    this.node("legend", de ? "Für welche Geräte?" : "Which devices?", group);
    const scopes = [["device", (de ? "Nur " : "Only ") + this.data.name],
      ["selected", de ? "Geräte auswählen …" : "Choose devices …"]];
    if (this.publication.shareable_class) {
      scopes.push(["class", (de ? "Aktuell importierte Geräte derselben Klasse · " : "Currently imported devices in the same class · ") +
        this.publication.class_count]);
      scopes.push(["future", de ? "Geräte derselben Klasse · aktuelle und künftige" : "Current and future devices in the same class"]);
    }
    if (shared) scopes.push(["remove", de ? "Gemeinsame Anpassung entfernen" : "Remove shared customization"]);
    let scope = shared?.scope === "class" && this.publication.shareable_class ? (shared.future ? "future" : "class")
      : shared ? "selected" : "device";
    const radios = scopes.map(([value, title]) => {
      const label = this.node("label", undefined, group);
      label.className = "row";
      const input = this.node("input", undefined, label);
      input.type = "radio";
      input.name = "device-change-scope";
      input.checked = value === scope;
      input.addEventListener("change", () => { scope = value; void refresh(); });
      this.node("span", title, label);
      return input;
    });
    const picker = this.node("div", undefined, group);
    const chosen = new Set(shared?.affected_ids ?? [this.data.source]);
    const selected = [];
    for (const [id, name] of Object.entries(this.publication.targets).sort(([, a], [, b]) => a.localeCompare(b))) {
      const label = this.node("label", undefined, picker);
      label.className = "row";
      const input = this.node("input", undefined, label);
      input.type = "checkbox";
      input.checked = chosen.has(id);
      input.addEventListener("change", () => void refresh());
      this.node("span", name, label);
      selected.push([id, input]);
    }
    const results = this.node("div", undefined, output);
    results.setAttribute("aria-live", "polite");
    const actions = this.node("div", undefined, output);
    actions.className = "row";
    this.button(de ? "Weiter bearbeiten" : "Continue editing", actions, () => this.invalidatePreview());
    const refresh = async () => {
      const version = this.previewVersion = (this.previewVersion ?? 0) + 1;
      const target = this.targetKey;
      const valid = () => this.targetKey === target && output === this.previewResult && version === this.previewVersion;
      if (actions.lastChild === apply) apply.remove();
      results.replaceChildren();
      const value = scope;
      picker.hidden = value !== "selected";
      const devices = selected.filter(([, input]) => input.checked).map(([id]) => id);
      if (value === "selected" && !devices.length) {
        this.node("p", de ? "Wähle mindestens ein Gerät aus." : "Select at least one device.", results);
        return;
      }
      this.node("p", t.loading, results);
      try {
        const response = value === "remove" ? await this.publishRequest("preview", {
          scope: shared.scope, future: shared.future, rule_id: shared.id, remove_rule: true,
          ...(shared.scope === "selected" ? {devices: shared.match} : {}),
        }) : await this.publishRequest("preview_device", {
          scope: value === "future" ? "class" : value, future: value === "future", devices,
          items: shared ? [] : [...this.draft.values()],
          ...(shared ? {shared_id: shared.id} : this.templateDraft ? {template_choice: this.templateDraft} : {}),
        });
        if (!valid()) return;
        results.replaceChildren();
        this.renderPreviewRows(results, response.rows);
        if (response.affected?.length) this.node("p", (de ? "Betroffen: " : "Affected: ") + response.affected.join(", "), results);
        apply.onclick = async () => {
          if (!valid()) return;
          apply.disabled = true;
          for (const radio of radios) radio.disabled = true;
          for (const [, input] of selected) input.disabled = true;
          this.show(t.applying);
          try {
            const result = await this.publishRequest("commit", {token: response.token});
            if (this.targetKey !== target) return;
            if (!shared) {
              this.draft.clear();
              this.templateDraft = null;
              this.commandEditor = null;
            }
            if (!result.reloaded || !await this.load(true)) {
              this.invalidatePreview();
              this.show(result.reloaded ? t.refreshFailed : t.reloadFailed, true);
              return;
            }
            this.show(t.applyDone);
          } catch (error) {
            apply.disabled = false;
            for (const radio of radios) radio.disabled = false;
            for (const [, input] of selected) input.disabled = false;
            this.show(error.message ?? String(error), true);
          }
        };
        apply.disabled = false;
        actions.append(apply);
      } catch (error) {
        if (valid()) results.textContent = error.message ?? String(error);
      }
    };
    const apply = this.node("button", de ? "Änderungen anwenden" : "Apply changes");
    apply.type = "button";
    apply.className = "primary";
    void refresh();
    radios.find((radio) => radio.checked)?.focus();
  }

  commandScripts(parent) {
    const t = this.labels;
    const scripts = this.node("section", undefined, parent);
    scripts.className = "command-scripts";
    this.node("h2", t.existingScripts, scripts);
    const scriptList = this.node("div", undefined, scripts);
    const target = this.deviceTarget;
    let currentLoad;
    const loadScripts = async (savedId = null) => {
      if (!scripts.isConnected) return;
      const load = currentLoad = Symbol();
      const current = () => scripts.isConnected && currentLoad === load;
      scriptList.replaceChildren();
      this.node("small", t.loadingScripts, scriptList).setAttribute("role", "status");
      try {
        const request = () => this._hass.callWS({
          type: "fhem_bridge/command_scripts", ...target,
        });
        let items = await request();
        for (const delay of [250, 750, 1500]) {
          if (!current() || !savedId || items.some((item) => item.id === savedId)) break;
          // HA acknowledges the config write before its scheduled script reload finishes.
          await new Promise((resolve) => setTimeout(resolve, delay));
          if (!current()) return;
          items = await request();
        }
        if (!current()) return;
        scriptList.replaceChildren();
        if (!items.length) {
          this.node("small", t.noScripts, scriptList);
          return;
        }
        const list = this.node("ul", undefined, scriptList);
        list.className = "command-scripts-list";
        for (const item of items) {
          const row = this.node("li", undefined, list);
          const link = this.node("a", item.name, row);
          link.href = "/config/script/edit/" + encodeURIComponent(item.id);
          this.node("small", item.entity_id, row);
          for (const action of item.commands) {
            const detail = action.variable ? t.variableScript : action.arguments.length ?
              t.fixedScript + " " + action.arguments.map((arg) => JSON.stringify(arg)).join(", ") : t.noScriptArgs;
            this.node("small", [action.channel, action.kind + " " + action.command, detail].join(" · "), row);
          }
        }
      } catch {
        if (!current()) return;
        scriptList.replaceChildren();
        this.node("small", t.scriptsFailed, scriptList).setAttribute("role", "alert");
        this.button(t.refresh, scriptList, () => loadScripts());
      }
    };
    this.refreshCommandScripts = loadScripts;
    void loadScripts();
  }

  automation(parent, kind, entry, values) {
    const t = this.labels;
    parent.replaceChildren();
    const target = {...this.deviceTarget, source: this.data.source};
    const step = {
      action: "fhem_bridge.execute",
      data: {...target, kind, command: entry.name,
        ...(values ? {[values.key]: values.args} : {})},
      ...(kind === "get" ? {response_variable: "fhem_result"} : {}),
    };
    const refreshScripts = this.refreshCommandScripts;
    const yaml = this.node("textarea", undefined, parent);
    yaml.readOnly = true;
    yaml.value = "action: " + step.action + "\ndata:\n" +
      Object.entries(step.data).map(([key, value]) => "  " + key + ": " + JSON.stringify(value)).join("\n") +
      (step.response_variable ? "\nresponse_variable: " + step.response_variable : "");
    const copy = this.button(t.copy, parent, async () => {
      try {
        await navigator.clipboard.writeText(yaml.value);
        this.show(t.copied);
      } catch {
        yaml.focus();
        yaml.select();
      }
    });
    yaml.hidden = copy.hidden = !values;
    const label = this.node("label", t.scriptName, parent);
    const name = this.node("input", undefined, label);
    name.value = this.data.name + " – " + entry.name;
    name.required = true;
    const save = this.button(t.script, parent, async () => {
      await saveScript(save, step);
    });
    save.hidden = !values;
    const saveScript = async (button, action, fields) => {
      if (!name.reportValidity() || !name.value.trim()) return;
      button.disabled = true;
      try {
        const id = "fhem_" + uniqueId();
        await this._hass.callApi("POST", "config/script/config/" + id, {
          alias: name.value.trim(), mode: "single",
          ...(fields ? {fields} : {}),
          sequence: kind === "get" ? [action, {stop: "FHEM response", response_variable: "fhem_result"}] : [action],
        });
        this.show(t.saved);
        await refreshScripts?.(id);
      } catch (error) {
        button.disabled = false;
        this.show(error.body?.message ?? error.message ?? String(error), true);
      }
    };
    if (entry.fields === null || entry.fields.length) {
      const dynamic = this.button(t.scriptInputs, parent, () => {
        if (entry.fields === null) {
          const fields = {arguments: {name: t.rawArgs, required: true, selector: {object: {}}}};
          return saveScript(dynamic, {...step, data: {
            ...target, kind, command: entry.name, inputs: "{{ arguments }}",
          }}, fields);
        }
        const fields = {};
        const variables = [];
        for (const [index, field] of entry.fields.entries()) {
          const key = "argument_" + (index + 1);
          let selector = {text: {}};
          if (field.type === "select") selector = {select: {options: field.options}};
          else if (field.modes.includes("box")) {
            selector = {number: {min: field.min, max: field.max, step: field.step, mode: "box"}};
          } else if (field.type === "date") selector = {date: {}};
          fields[key] = {
            name: t[field.label] ?? (t.arg + " " + (index + 1)),
            required: !field.optional, selector,
          };
          variables.push(key + " | default(none)");
        }
        const data = {...target, kind, command: entry.name,
          inputs: "{{ [" + variables.join(", ") + "] }}"};
        return saveScript(dynamic, {...step, data}, fields);
      });
    }
  }
}

const bridgeImportDialogs = new WeakMap();
const bridgeReturning = new WeakSet();

function handleBridgeBack(event) {
  const path = event.composedPath();
  const dialog = path.find((node) => node.localName === "dialog-data-entry-flow");
  if (!dialog) return false;
  const step = dialog.shadowRoot?.querySelector("step-flow-menu, step-flow-form");
  const entryId = step?.step?.description_placeholders?.fhem_bridge_return_entry;
  if (!entryId || !step.hass?.user?.is_admin || !step.flowConfig) return false;
  if (event.type === "click" && !path.some((node) => node.matches?.('[slot="headerNavigationIcon"][data-dialog="close"]'))) return false;
  if (event.type === "keydown" && event.key !== "Escape") return false;
  event.preventDefault();
  event.stopImmediatePropagation();
  if (bridgeReturning.has(dialog)) return true;
  bridgeReturning.add(dialog);
  const {flowConfig, hass} = step;
  const oldFlow = step.step.flow_id;
  const previous = step.step.step_id.startsWith("connection") ? "connection" : "catalog";
  const stepPromise = flowConfig.createFlow(hass, entryId).then((result) => {
    void flowConfig.deleteFlow(hass, oldFlow).catch(() => {});
    requestAnimationFrame(() => {
      const menu = dialog.shadowRoot?.querySelector("step-flow-menu");
      if (menu?.step?.flow_id !== result.flow_id) return;
      const rows = menu.shadowRoot?.querySelectorAll("ha-list-item-button, ha-list-item");
      rows?.[result.menu_options?.indexOf(previous)]?.focus();
    });
    return result;
  }).finally(() => bridgeReturning.delete(dialog));
  step.dispatchEvent(new CustomEvent("flow-update", {bubbles: true, composed: true, detail: {stepPromise}}));
  return true;
}

function handleBridgeImportMenu(event) {
  if (handleBridgeBack(event)) return;
  // The native flow renders its menu rows but has no slot for custom content.
  // Keep that flow open under the modal and intercept only our own row.
  const path = event.composedPath();
  const rowSelector = "ha-list-item-button, ha-list-item";
  const item = path.find((node) => node.matches?.(rowSelector));
  if (!item) return;
  const menu = path.find((node) => node.localName === "step-flow-menu");
  const step = menu?.step;
  const entryId = step?.description_placeholders?.fhem_bridge_import_entry;
  if (!entryId || !step.step_id?.startsWith("init_") || !menu.hass?.user?.is_admin) return;
  const rows = Array.from(menu.shadowRoot?.querySelectorAll(rowSelector) ?? []);
  const options = step.menu_options;
  if (!Array.isArray(options) || step.sort || rows.length !== options.length) return;
  const mode = options[rows.indexOf(item)];
  if (mode !== "add_devices" && mode !== "group") return;

  // Older HA frontends render ha-list-item without a step property.
  // For this unsorted native menu the visible row order matches menu_options.
  event.preventDefault();
  event.stopImmediatePropagation();

  let element = menu;
  while (element && element.localName !== "dialog-data-entry-flow") element = element.getRootNode().host;
  const nativeDialog = element ?? menu;
  if (!bridgeImportDialogs.has(nativeDialog)) bridgeImportDialogs.set(nativeDialog, new Map());
  const dialogs = bridgeImportDialogs.get(nativeDialog);
  const existing = dialogs.get(mode);
  if (existing) {
    existing.trigger = item;
    existing.modal.open = true;
    return;
  }
  const modal = document.createElement("ha-dialog");
  modal.setAttribute("width", "large");
  modal.style.setProperty("--ha-dialog-width-lg", "920px");
  const de = menu.hass.locale?.language?.startsWith("de");
  modal.headerTitle = mode === "group" ? (de ? "Geräte gruppieren" : "Group devices") :
    (de ? "Geräte importieren" : "Import devices");
  const panel = document.createElement("fhem-bridge-device-panel");
  let footer;
  panel.tabIndex = -1;
  panel.importDialog = {
    entryId,
    mode,
    close: () => { modal.open = false; },
    setFooter: (next) => {
      footer?.remove();
      footer = next;
      if (footer) {
        footer.slot = "footer";
        footer.style.flexWrap = "wrap";
        footer.style.boxSizing = "border-box";
        modal.append(footer);
      }
    },
    resetScroll: () => { if (modal.bodyContainer) modal.bodyContainer.scrollTop = 0; },
    setTitle: (title) => {
      if (modal.headerTitle === title) return;
      modal.headerTitle = title;
      if (modal.open) panel.focus();
    },
  };
  panel.hass = menu.hass;
  modal.append(panel);
  // Mount beside the flow so the overlay's keyboard and close events stay outside it.
  (nativeDialog.parentNode ?? document.body).append(modal);
  const dialog = {modal, trigger: item};
  dialogs.set(mode, dialog);
  const lifetime = new AbortController();
  const remove = () => {
    lifetime.abort();
    modal.open = false;
    modal.remove();
    dialogs.delete(mode);
  };
  modal.addEventListener("after-show", () => {
    if (modal.open) panel.focus();
  }, {signal: lifetime.signal});
  modal.addEventListener("closed", (event) => {
    if (event.target !== modal) return;
    modal.open = false;
    if (dialog.trigger.isConnected) dialog.trigger.focus();
    if (panel.importDialog.saved) remove();
  }, {signal: lifetime.signal});
  nativeDialog.addEventListener("dialog-closed", remove, {once: true, signal: lifetime.signal});
  panel.render();
  modal.open = true;
}

if (!customElements.get("fhem-bridge-device-panel")) {
  customElements.define("fhem-bridge-device-panel", FhemBridgeDevicePanel);
  if (typeof document !== "undefined") {
    document.addEventListener("click", handleBridgeImportMenu, true);
    document.addEventListener("keydown", handleBridgeBack, true);
  }
}
