// LumiCap_Importer_Update_AllInOne_UI.jsx — After Effects 2026
// .lcap (JSON) -> AE text layers with highlight steps
// Sexy UI: Mode (Create/Update), Masters, Scope, Progress + Cancel
//
// Supports optional project layout in:
// settings.layout = {
//   preset: "9:16",
//   comp: { w: 1080, h: 1920 },
//   anchor: "bottom_center" | "center" | "top_center" | "bottom_left" | "bottom_right",
//   safe: { bottom: 0.12 },
//   offset: { x: 0, y: -120 }
// }
//
// If layout missing: defaults to center (0,0 offset) for captions
// Comp sizing is only used if there's NO active comp selected.

(function () {
    // -------------------- helpers --------------------
    function readTextFile(file) {
        if (!file || !file.exists) throw new Error("File not found.");
        file.encoding = "UTF-8";
        if (!file.open("r")) throw new Error("Could not open file.");
        var content = file.read();
        file.close();
        return content;
    }

    function parseJSONSafe(str) {
        if (typeof JSON !== "undefined" && JSON.parse) return JSON.parse(str);
        return eval("(" + str + ")"); // fallback (trusted local file)
    }

    function firstTwoWords(s) {
        if (!s) return "";
        var t = ("" + s).replace(/\s+/g, " ").replace(/^\s+|\s+$/g, "");
        if (!t) return "";
        var parts = t.split(" ");
        return (parts.length === 1) ? parts[0] : (parts[0] + " " + parts[1]);
    }

    function computeDuration(groups) {
        var maxOut = 0;
        for (var i = 0; i < groups.length; i++) {
            var g = groups[i];
            if (g && g.out != null && g.out > maxOut) maxOut = g.out;
        }
        return Math.max(10, maxOut + 2);
    }

    function centerTextAnchor(layer, t) {
        try {
            var rect = layer.sourceRectAtTime(t, false);
            var ap = layer.property("Transform").property("Anchor Point");
            ap.setValue([rect.left + rect.width / 2, rect.top + rect.height / 2]);
        } catch (e) { }
    }

    function setTextJustifyCenter(layer) {
        try {
            var td = layer.property("Source Text").value;
            td.justification = ParagraphJustification.CENTER_JUSTIFY;
            layer.property("Source Text").setValue(td);
        } catch (e) { }
    }

    function getActiveComp() {
        var item = app.project && app.project.activeItem;
        if (item && (item instanceof CompItem)) return item;
        return null;
    }

    // -------------------- layout --------------------
    function getLayout(lcap) {
        var layout = (lcap.settings && lcap.settings.layout) ? lcap.settings.layout : null;

        var compW = layout && layout.comp && layout.comp.w ? layout.comp.w : null;
        var compH = layout && layout.comp && layout.comp.h ? layout.comp.h : null;

        var anchor = layout && layout.anchor ? layout.anchor : "center";
        var safeBottom = layout && layout.safe && layout.safe.bottom != null ? layout.safe.bottom : 0.0;

        var offX = layout && layout.offset && layout.offset.x != null ? layout.offset.x : 0;
        var offY = layout && layout.offset && layout.offset.y != null ? layout.offset.y : 0;

        return {
            compW: compW,
            compH: compH,
            anchor: anchor,
            safeBottom: safeBottom,
            offX: offX,
            offY: offY
        };
    }

    function anchorToNorm(anchor) {
        switch (anchor) {
            case "bottom_center": return { x: 0.5, y: 0.85 };
            case "top_center": return { x: 0.5, y: 0.15 };
            case "center": return { x: 0.5, y: 0.5 };
            case "bottom_left": return { x: 0.08, y: 0.85 };
            case "bottom_right": return { x: 0.92, y: 0.85 };
            default: return { x: 0.5, y: 0.5 };
        }
    }

    function computeCaptionPos(comp, layout) {
        var a = anchorToNorm(layout.anchor);
        var x = comp.width * a.x + layout.offX;
        var y = comp.height * a.y + layout.offY;

        if (layout.anchor && layout.anchor.indexOf("bottom") === 0) {
            y = y - (comp.height * layout.safeBottom);
        }
        return [x, y];
    }

    // -------------------- comp pick/create --------------------
    function pickActiveCompOrCreateWithLayout(defaultName, fps, duration, layout) {
        var active = getActiveComp();
        if (active) return active;

        var w = (layout && layout.compW) ? layout.compW : 1920;
        var h = (layout && layout.compH) ? layout.compH : 1080;

        return app.project.items.addComp(
            defaultName || "LumiCap_Import",
            w, h,
            1.0,
            duration || 10,
            fps || 25
        );
    }

    function setHoldInterpolation(prop, keyIndex) {
        try {
            prop.setInterpolationTypeAtKey(keyIndex, KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD);
        } catch (e) { }
    }

    function charIndexToPercentRange(text, startChar, endChar) {
        var t = text || "";
        var len = t.length;
        if (len <= 0) return { startP: 0, endP: 0 };

        var s = Math.max(0, Math.min(startChar, len));
        var e = Math.max(0, Math.min(endChar, len));
        if (e < s) e = s;

        return { startP: (s / len) * 100, endP: (e / len) * 100 };
    }

    // -------------------- LCAP layer identity (Marker) --------------------
    function setLayerGidMarker(layer, gid) {
        if (!gid) return;
        try {
            var markerProp = layer.property("Marker");
            for (var k = markerProp.numKeys; k >= 1; k--) {
                var c = markerProp.keyValue(k).comment || "";
                if (c.indexOf("LCAP id:") === 0) markerProp.removeKey(k);
            }
            var mv = new MarkerValue("LCAP id: " + gid);
            markerProp.setValueAtTime(layer.inPoint, mv);
        } catch (e) { }
    }

    function getLayerGid(layer) {
        try {
            var markerProp = layer.property("Marker");
            for (var k = 1; k <= markerProp.numKeys; k++) {
                var c = markerProp.keyValue(k).comment || "";
                var m = c.match(/^LCAP id:\s*(.+)$/);
                if (m && m[1]) return m[1];
            }
        } catch (e) { }
        return null;
    }

    function findLayerByGid(comp, gid) {
        for (var i = 1; i <= comp.numLayers; i++) {
            var l = comp.layer(i);
            if (l && (l instanceof TextLayer)) {
                if (getLayerGid(l) === gid) return l;
            }
        }
        return null;
    }

    function makeFallbackGid(group, index) {
        var style = group.style || "Normal";
        var key = group.key || "";
        var text = group.text || "";
        return "fallback_" + index + "_" + style + "_" + (firstTwoWords(key || text) || "X");
    }

    // -------------------- Highlight Animator + Steps --------------------
    function addHighlightAnimator(textLayer) {
        var textProps = textLayer.property("ADBE Text Properties");
        var animators = textProps.property("ADBE Text Animators");
        var animator = animators.addProperty("ADBE Text Animator");
        animator.name = "Highlight";

        var animProps = animator.property("ADBE Text Animator Properties");
        var fillColor = animProps.addProperty("ADBE Text Fill Color");
        fillColor.setValue([1, 1, 1]);

        var selectors = animator.property("ADBE Text Selectors");
        var rangeSel = selectors.addProperty("ADBE Text Selector");
        rangeSel.name = "Range";
        return rangeSel;
    }

    function ensureHighlightRangeSelector(textLayer) {
        var textProps = textLayer.property("ADBE Text Properties");
        var animators = textProps.property("ADBE Text Animators");

        for (var i = 1; i <= animators.numProperties; i++) {
            var a = animators.property(i);
            if ((a.name || "") === "Highlight") {
                var sels = a.property("ADBE Text Selectors");
                if (sels && sels.numProperties >= 1) return sels.property(1);
            }
        }
        return addHighlightAnimator(textLayer);
    }

    function applyStepsToRangeSelector(rangeSelector, groupText, steps) {
        if (!rangeSelector) return;

        var startProp = rangeSelector.property("ADBE Text Percent Start");
        var endProp = rangeSelector.property("ADBE Text Percent End");
        if (!startProp || !endProp) return;

        while (startProp.numKeys > 0) startProp.removeKey(1);
        while (endProp.numKeys > 0) endProp.removeKey(1);

        if (!steps || steps.length === 0) {
            startProp.setValue(0);
            endProp.setValue(0);
            return;
        }

        for (var i = 0; i < steps.length; i++) {
            var st = steps[i];
            var t = st.t;
            var pr = charIndexToPercentRange(groupText, st.start || 0, st.end || 0);

            startProp.setValueAtTime(t, pr.startP);
            endProp.setValueAtTime(t, pr.endP);

            setHoldInterpolation(startProp, startProp.nearestKeyIndex(t));
            setHoldInterpolation(endProp, endProp.nearestKeyIndex(t));
        }
    }

    // -------------------- create/update caption layer --------------------
    function nameForGroup(group, index) {
        var style = group.style || "Normal";
        var label = firstTwoWords(group.text || group.key || "");
        return "[" + style + "] " + (label || ("Group " + (index + 1)));
    }

    function createCaptionLayer(comp, group, index, layout, opts) {
        var layer = comp.layers.addText(group.text || "");
        layer.name = nameForGroup(group, index);

        var inT = (group["in"] != null) ? group["in"] : 0;
        var outT = (group.out != null) ? group.out : (inT + 1);

        layer.inPoint = inT;
        layer.outPoint = outT;

        if (opts.centerJustify) setTextJustifyCenter(layer);
        if (opts.centerAnchor) centerTextAnchor(layer, layer.inPoint);

        if (opts.positionOnCreate) {
            try {
                var pos = computeCaptionPos(comp, layout);
                layer.property("Transform").property("Position").setValue(pos);
            } catch (e) { }
        }

        var rangeSel = ensureHighlightRangeSelector(layer);
        applyStepsToRangeSelector(rangeSel, group.text || "", group.steps || []);

        var gid = group.id || makeFallbackGid(group, index);
        setLayerGidMarker(layer, gid);

        return layer;
    }

    function updateCaptionLayer(layer, group, index, opts) {
        // Keep styling & transforms by default
        layer.property("Source Text").setValue(group.text || "");

        var inT = (group["in"] != null) ? group["in"] : layer.inPoint;
        var outT = (group.out != null) ? group.out : layer.outPoint;
        layer.inPoint = inT;
        layer.outPoint = outT;

        layer.name = nameForGroup(group, index);

        if (opts.centerJustify) setTextJustifyCenter(layer);
        if (opts.centerAnchor) centerTextAnchor(layer, layer.inPoint);

        var rangeSel = ensureHighlightRangeSelector(layer);
        applyStepsToRangeSelector(rangeSel, group.text || "", group.steps || []);

        var gid = group.id || makeFallbackGid(group, index);
        setLayerGidMarker(layer, gid);
    }

    // -------------------- masters --------------------
    function collectStyles(groups, defaultStyle) {
        var set = {};
        if (defaultStyle) set[defaultStyle] = true;
        for (var i = 0; i < groups.length; i++) {
            var s = (groups[i] && groups[i].style) ? groups[i].style : null;
            if (s) set[s] = true;
        }
        return set;
    }

    function hasTextLayerNamed(comp, name) {
        for (var i = 1; i <= comp.numLayers; i++) {
            var l = comp.layer(i);
            if (l && (l instanceof TextLayer) && l.name === name) return true;
        }
        return false;
    }

    function ensureMasters(comp, stylesSet, opts) {
        for (var s in stylesSet) {
            if (!stylesSet.hasOwnProperty(s)) continue;
            var masterName = "Master " + s;

            if (!hasTextLayerNamed(comp, masterName)) {
                var ml = comp.layers.addText(masterName);
                ml.name = masterName;

                if (opts.centerJustify) setTextJustifyCenter(ml);
                if (opts.centerAnchor) centerTextAnchor(ml, ml.inPoint);

                try { ml.property("Transform").property("Position").setValue([comp.width / 2, comp.height / 2]); } catch (e) { }

                ensureHighlightRangeSelector(ml);

                try { ml.guideLayer = true; } catch (e) { }
                try { ml.shy = true; } catch (e) { }
                if (opts.hideShyLayers) {
                    try { comp.hideShyLayers = true; } catch (e) { }
                }
                try { ml.moveToBeginning(); } catch (e) { }
            }
        }
    }

    // -------------------- validate lcap --------------------
    function validateLcap(lcap) {
        if (!lcap) throw new Error("Empty file.");
        if (lcap.format !== "lcap") throw new Error("Invalid format (expected 'lcap').");
        if (!lcap.version) throw new Error("Missing version.");
    }

    // -------------------- UI --------------------
    function showUI(defaults) {
        var w = new Window("dialog", "LumiCap Import / Update 😈💜");
        w.orientation = "column";
        w.alignChildren = ["fill", "top"];

        var p1 = w.add("panel", undefined, "File");
        p1.orientation = "column";
        p1.alignChildren = ["fill", "top"];
        var fileRow = p1.add("group"); fileRow.orientation = "row";
        var filePath = fileRow.add("edittext", undefined, defaults.filePath || "");
        filePath.characters = 48;
        var btnBrowse = fileRow.add("button", undefined, "Browse…");

        var p2 = w.add("panel", undefined, "Mode");
        p2.orientation = "column";
        p2.alignChildren = ["left", "top"];
        var rbCreate = p2.add("radiobutton", undefined, "Create New Layers");
        var rbUpdate = p2.add("radiobutton", undefined, "Update Existing (by LCAP id marker)");
        rbUpdate.value = true;

        var p3 = w.add("panel", undefined, "Masters");
        p3.orientation = "column";
        p3.alignChildren = ["left", "top"];
        var cbMasters = p3.add("checkbox", undefined, "Create missing Master <Style> layers (Guide + Shy)");
        cbMasters.value = true;
        var cbHideShy = p3.add("checkbox", undefined, "Hide shy layers in comp (comp.hideShyLayers = true)");
        cbHideShy.value = false;

        var p4 = w.add("panel", undefined, "Placement / Safety");
        p4.orientation = "column";
        p4.alignChildren = ["left", "top"];
        var cbPositionOnCreate = p4.add("checkbox", undefined, "Position captions on CREATE using layout (recommended)");
        cbPositionOnCreate.value = true;
        var cbCenterAnchor = p4.add("checkbox", undefined, "Center anchor point on import");
        cbCenterAnchor.value = true;
        var cbCenterJustify = p4.add("checkbox", undefined, "Center text justification on import");
        cbCenterJustify.value = true;

        var hint = w.add("statictext", undefined, "Tip: Update mode keeps your styling/transform; only text, timing & highlight steps are updated.");
        hint.graphics.font = ScriptUI.newFont(hint.graphics.font.name, "ITALIC", hint.graphics.font.size);

        var btnRow = w.add("group");
        btnRow.orientation = "row";
        btnRow.alignment = "right";
        var btnCancel = btnRow.add("button", undefined, "Cancel");
        var btnOk = btnRow.add("button", undefined, "Go 😈", { name: "ok" });

        var res = { ok: false };

        btnBrowse.onClick = function () {
            var f = File.openDialog("Wähle eine .lcap Datei", "*.lcap;*.json");
            if (f) filePath.text = f.fsName;
        };

        btnOk.onClick = function () {
            res.ok = true;
            res.filePath = filePath.text;
            res.doUpdate = rbUpdate.value;
            res.makeMasters = cbMasters.value;
            res.hideShyLayers = cbHideShy.value;
            res.positionOnCreate = cbPositionOnCreate.value;
            res.centerAnchor = cbCenterAnchor.value;
            res.centerJustify = cbCenterJustify.value;
            w.close();
        };
        btnCancel.onClick = function () { res.ok = false; w.close(); };

        w.center();
        w.show();
        return res;
    }

    function showProgress(total) {
        var w = new Window("palette", "LumiCap Importing… 🦥");
        w.orientation = "column";
        w.alignChildren = ["fill", "top"];

        var txt = w.add("statictext", undefined, "Starting…");
        var bar = w.add("progressbar", undefined, 0, Math.max(1, total));
        bar.preferredSize = [420, 18];

        var row = w.add("group");
        row.orientation = "row";
        row.alignment = "right";

        var btnStop = row.add("button", undefined, "Stop");
        var btnClose = row.add("button", undefined, "Close");

        var state = { stop: false };

        function forceClose() {
            try { w.hide(); } catch (e) { }
            try { w.visible = false; } catch (e) { }
            try { w.close(); } catch (e) { }
        }

        btnStop.onClick = function () { state.stop = true; forceClose(); };
        btnClose.onClick = function () { state.stop = true; forceClose(); };

        w.onClose = function () { state.stop = true; return true; };

        w.show();

        return {
            state: state,
            update: function (i, label) {
                try {
                    txt.text = label || ("Group " + i + "/" + total);
                    bar.value = i;
                    w.update();
                } catch (e) { }
            },
            forceClose: forceClose
        };
    }

    // -------------------- MAIN (safe progress cleanup) --------------------
    (function () {
        var prog = null;
        var undoStarted = false;

        try {
            if (!app.project) throw new Error("Open an AE project first.");

            var ui = showUI({ filePath: "" });
            if (!ui.ok) return;

            var file = File(ui.filePath);
            if (!file || !file.exists) throw new Error("File not found: " + ui.filePath);

            var content = readTextFile(file);
            var lcap = parseJSONSafe(content);

            validateLcap(lcap);

            if (lcap.meta && lcap.meta.draft === true) {
                var ok = confirm("⚠️ DRAFT Datei\nDiese .lcap könnte unfertig sein.\n\nOK = trotzdem importieren\nCancel = abbrechen");
                if (!ok) return;
            }

            var groups = lcap.groups || [];
            var fps = (lcap.meta && lcap.meta.fps) ? lcap.meta.fps : 25;
            var duration = computeDuration(groups);
            var layout = getLayout(lcap);

            var compName = (lcap.project && lcap.project.name) ? lcap.project.name : "LumiCap_Import";
            var comp = pickActiveCompOrCreateWithLayout(compName, fps, duration, layout);

            // Set comp fps/duration gently
            try { comp.frameRate = fps; } catch (e) { }
            try { if (comp.duration < duration) comp.duration = duration; } catch (e) { }

            // Masters (optional)
            if (ui.makeMasters) {
                var defaultStyle = (lcap.settings && lcap.settings.default_style) ? lcap.settings.default_style : "Normal";
                var stylesSet = collectStyles(groups, defaultStyle);
                ensureMasters(comp, stylesSet, {
                    centerJustify: ui.centerJustify,
                    centerAnchor: ui.centerAnchor,
                    hideShyLayers: ui.hideShyLayers
                });
            }

            app.beginUndoGroup("LumiCap Import/Update (UI)");
            undoStarted = true;

            // Progress (safe)
            prog = showProgress(groups.length);

            var created = 0;
            var updated = 0;
            var skipped = 0;

            for (var i = 0; i < groups.length; i++) {
                if (prog && prog.state && prog.state.stop) break;

                var g = groups[i];
                if (!g) { skipped++; continue; }

                if (prog) {
                    prog.update(
                        i + 1,
                        (ui.doUpdate ? "Update" : "Create") + " → " +
                        (g.style || "Normal") + " / " + firstTwoWords(g.text || "")
                    );
                }

                var gid = g.id || makeFallbackGid(g, i);

                if (ui.doUpdate) {
                    var existing = findLayerByGid(comp, gid);
                    if (existing) {
                        updateCaptionLayer(existing, g, i, {
                            centerAnchor: ui.centerAnchor,
                            centerJustify: ui.centerJustify
                        });
                        updated++;
                    } else {
                        createCaptionLayer(comp, g, i, layout, {
                            positionOnCreate: ui.positionOnCreate,
                            centerAnchor: ui.centerAnchor,
                            centerJustify: ui.centerJustify
                        });
                        created++;
                    }
                } else {
                    createCaptionLayer(comp, g, i, layout, {
                        positionOnCreate: ui.positionOnCreate,
                        centerAnchor: ui.centerAnchor,
                        centerJustify: ui.centerJustify
                    });
                    created++;
                }

                // AE nicht komplett sterben lassen
                if ((i % 10) === 0) {
                    try { app.refresh(); } catch (e) { }
                }
            }

            // Result
            var stopped = (prog && prog.state && prog.state.stop);

            alert(
                (stopped ? "⛔ LumiCap abgebrochen!\n\n" : "✅ LumiCap " + (ui.doUpdate ? "Update" : "Import") + " fertig!\n\n") +
                "Created: " + created + "\n" +
                "Updated: " + updated + "\n" +
                "Skipped: " + skipped + "\n\n" +
                "Comp: " + comp.name + "\n" +
                "Layout anchor: " + layout.anchor
            );

        } catch (err) {
            alert("❌ LumiCap Import/Update Error:\n" + err.toString());
        } finally {
            // ALWAYS kill progress window (prevents stuck palette zombies)
            if (prog) {
                try {
                    if (prog.forceClose) prog.forceClose();
                    else if (prog.close) prog.close(); // fallback if you kept old API
                } catch (e) { }
            }

            // ALWAYS end undo group if started
            if (undoStarted) {
                try { app.endUndoGroup(); } catch (e2) { }
            }
        }
    })();
})();