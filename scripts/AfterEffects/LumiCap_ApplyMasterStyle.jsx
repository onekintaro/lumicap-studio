// LumiCap_ApplyMasterStyle_UI.jsx — AE 2026
// "Hübschi" Apply Master Styles mit UI: FAST / SMART / FULL + Progress + Cancel
//
// FAST:
//  - Transform (pos/scale/rot/opacity/anchor)
//  - TextDocument Style (Font/Size/Fill/Stroke/etc.) but KEEP caption text
//  - Highlight LOOK only (Animator Properties) from master -> target (keine Animator-Rebuilds)
//  - Keine Effects / keine Layer Styles
//
// SMART (Sweet Spot):
//  - Alles aus FAST
//  - Effects: NICHT löschen. Wenn Effekt fehlt -> add + copy. Wenn vorhanden -> params updaten.
//  - Layer Styles: Werte updaten (ohne Löschen/Neuaufbau)
//  - Text Animators: KEIN Wipe. Versucht Animator Properties zu matchen & updaten (Selector Keys bleiben unangetastet)
//  - Highlight Range Keys (Start/End) bleiben IMMER erhalten.
//
// FULL (slow, nuclear):
//  - Alles aus FAST
//  - Rebuild vollständigen Animator Stack (wie vorher) + Effects neu + Layer Styles mirror
//  - Highlight Range Keys werden nach dem Rebuild restored
//
// Skips Variable Font Axis props: "ADBE Text VF Axis *" (cannot be addProperty()'d)

(function () {
    // -------------------- Core helpers --------------------
    function getActiveComp() {
        var item = app.project && app.project.activeItem;
        if (!item || !(item instanceof CompItem)) throw new Error("Select an active composition first.");
        return item;
    }

    function parseStyleFromName(name) {
        if (!name) return null;
        var m = name.match(/^\s*\[([^\]]+)\]/);
        return m ? m[1] : null;
    }

    function buildMasterMap(comp) {
        var map = {};
        for (var i = 1; i <= comp.numLayers; i++) {
            var l = comp.layer(i);
            if (!l || !(l instanceof TextLayer)) continue;
            var nm = l.name || "";
            var mm = nm.match(/^\s*Master\s+(.+)\s*$/i);
            if (mm && mm[1]) map[mm[1]] = l;
        }
        return map;
    }

    function isUnsupportedProperty(matchName) {
        if (!matchName) return false;
        if (matchName.indexOf("ADBE Text VF Axis") === 0) return true; // Variable font axes can't be added
        return false;
    }

    function safeAddProperty(group, matchName) {
        try {
            if (isUnsupportedProperty(matchName)) return null;
            return group.addProperty(matchName);
        } catch (e) {
            return null;
        }
    }

    function copyKeysAndValue(srcProp, dstProp) {
        if (!srcProp || !dstProp) return;
        try {
            while (dstProp.numKeys > 0) dstProp.removeKey(1);

            if (srcProp.numKeys && srcProp.numKeys > 0) {
                for (var k = 1; k <= srcProp.numKeys; k++) {
                    var t = srcProp.keyTime(k);
                    dstProp.setValueAtTime(t, srcProp.keyValue(k));
                    try {
                        dstProp.setInterpolationTypeAtKey(
                            dstProp.nearestKeyIndex(t),
                            KeyframeInterpolationType.HOLD,
                            KeyframeInterpolationType.HOLD
                        );
                    } catch (e2) { }
                }
            } else {
                dstProp.setValue(srcProp.value);
            }
        } catch (e) { }
    }

    function cloneTextDocumentStyle(fromLayer, toLayer) {
        var fromProp = fromLayer.property("Source Text");
        var toProp = toLayer.property("Source Text");
        var fromDoc = fromProp.value;
        var toDoc = toProp.value;

        var keepText = toDoc.text;
        toProp.setValue(fromDoc);
        var newDoc = toProp.value;
        newDoc.text = keepText;
        toProp.setValue(newDoc);
    }

    function copyTransform(fromLayer, toLayer) {
        var srcT = fromLayer.property("Transform");
        var dstT = toLayer.property("Transform");
        if (!srcT || !dstT) return;

        copyKeysAndValue(srcT.property("Anchor Point"), dstT.property("Anchor Point"));
        copyKeysAndValue(srcT.property("Position"), dstT.property("Position"));
        copyKeysAndValue(srcT.property("Scale"), dstT.property("Scale"));
        copyKeysAndValue(srcT.property("Rotation"), dstT.property("Rotation"));
        copyKeysAndValue(srcT.property("X Rotation"), dstT.property("X Rotation"));
        copyKeysAndValue(srcT.property("Y Rotation"), dstT.property("Y Rotation"));
        copyKeysAndValue(srcT.property("Z Rotation"), dstT.property("Z Rotation"));
        copyKeysAndValue(srcT.property("Opacity"), dstT.property("Opacity"));
    }

    function copyLayerBasics(fromLayer, toLayer) {
        try { toLayer.blendingMode = fromLayer.blendingMode; } catch (e) { }
        try { toLayer.motionBlur = fromLayer.motionBlur; } catch (e) { }
        try { toLayer.threeDLayer = fromLayer.threeDLayer; } catch (e) { }
        try { toLayer.adjustmentLayer = fromLayer.adjustmentLayer; } catch (e) { }
        try { toLayer.collapseTransformation = fromLayer.collapseTransformation; } catch (e) { }
        // Usually you don't want these copied, but you said ALL 😈 (masters should typically be guide/shy anyway)
        try { toLayer.guideLayer = false; } catch (e) { } // keep captions renderable
        // shy/locked: DON'T copy from master (masters often shy/locked)
        // if you truly want it: uncomment
        // try { toLayer.shy = fromLayer.shy; } catch (e) {}
        // try { toLayer.locked = fromLayer.locked; } catch (e) {}
    }

    // -------------------- Highlight helpers --------------------
    function getHighlightAnimator(layer) {
        var textProps = layer.property("ADBE Text Properties");
        if (!textProps) return null;
        var animators = textProps.property("ADBE Text Animators");
        if (!animators) return null;
        for (var i = 1; i <= animators.numProperties; i++) {
            var a = animators.property(i);
            if ((a.name || "") === "Highlight") return a;
        }
        return null;
    }

    function findHighlightSelector(layer) {
        var a = getHighlightAnimator(layer);
        if (!a) return null;
        var sels = a.property("ADBE Text Selectors");
        if (sels && sels.numProperties >= 1) return sels.property(1);
        return null;
    }

    function captureHighlightKeys(layer) {
        var sel = findHighlightSelector(layer);
        if (!sel) return null;

        var startProp = sel.property("ADBE Text Percent Start");
        var endProp = sel.property("ADBE Text Percent End");
        if (!startProp || !endProp) return null;

        function cap(prop) {
            var out = { keys: [] };
            if (prop.numKeys && prop.numKeys > 0) {
                for (var k = 1; k <= prop.numKeys; k++) {
                    out.keys.push({ t: prop.keyTime(k), v: prop.keyValue(k) });
                }
            } else {
                out.value = prop.value;
            }
            return out;
        }

        return { start: cap(startProp), end: cap(endProp) };
    }

    function restoreHighlightKeys(layer, data) {
        if (!data) return;
        var sel = findHighlightSelector(layer);
        if (!sel) return;

        var startProp = sel.property("ADBE Text Percent Start");
        var endProp = sel.property("ADBE Text Percent End");
        if (!startProp || !endProp) return;

        function restore(prop, cap) {
            try { while (prop.numKeys > 0) prop.removeKey(1); } catch (e) { }
            if (cap.keys && cap.keys.length > 0) {
                for (var i = 0; i < cap.keys.length; i++) {
                    prop.setValueAtTime(cap.keys[i].t, cap.keys[i].v);
                    try {
                        prop.setInterpolationTypeAtKey(
                            prop.nearestKeyIndex(cap.keys[i].t),
                            KeyframeInterpolationType.HOLD,
                            KeyframeInterpolationType.HOLD
                        );
                    } catch (e2) { }
                }
            } else if (cap.value != null) {
                try { prop.setValue(cap.value); } catch (e3) { }
            }
        }

        restore(startProp, data.start);
        restore(endProp, data.end);
    }

    // FAST: copy only Highlight LOOK (Animator Properties), don't touch selectors/keys
    function copyHighlightLook(masterLayer, targetLayer) {
        var ma = getHighlightAnimator(masterLayer);
        var ta = getHighlightAnimator(targetLayer);
        if (!ma || !ta) return;

        var mp = ma.property("ADBE Text Animator Properties");
        var tp = ta.property("ADBE Text Animator Properties");
        if (!mp || !tp) return;

        for (var i = 1; i <= mp.numProperties; i++) {
            var sp = mp.property(i);
            if (!sp || isUnsupportedProperty(sp.matchName)) continue;

            // Only update existing props on target in FAST/SMART
            var dp = tp.property(sp.matchName);
            if (!dp) continue;

            copyKeysAndValue(sp, dp);
        }
    }

    // -------------------- SMART: Effects update (no delete) --------------------
    function findEffectByMatchNameOrName(dstFX, srcEff) {
        // Try matchName first
        for (var i = 1; i <= dstFX.numProperties; i++) {
            var e = dstFX.property(i);
            if (!e) continue;
            if (e.matchName === srcEff.matchName) return e;
            if ((e.name || "") === (srcEff.name || "")) return e;
        }
        return null;
    }

    function copyEffectsSMART(fromLayer, toLayer) {
        var srcFX = fromLayer.property("ADBE Effect Parade");
        var dstFX = toLayer.property("ADBE Effect Parade");
        if (!srcFX || !dstFX) return;

        for (var i = 1; i <= srcFX.numProperties; i++) {
            var srcEff = srcFX.property(i);
            if (!srcEff) continue;

            var dstEff = findEffectByMatchNameOrName(dstFX, srcEff);
            if (!dstEff) {
                dstEff = safeAddProperty(dstFX, srcEff.matchName);
                if (!dstEff) continue;
                dstEff.name = srcEff.name;
            } else {
                // keep existing name
            }

            // copy params
            for (var p = 1; p <= srcEff.numProperties; p++) {
                var sp = srcEff.property(p);
                var dp = dstEff.property(p);
                if (!dp) continue;
                copyKeysAndValue(sp, dp);
            }
        }
    }

    // -------------------- SMART: Layer Styles update (values only) --------------------
    function copyLayerStylesSMART(fromLayer, toLayer) {
        var srcLS = fromLayer.property("ADBE Layer Styles");
        var dstLS = toLayer.property("ADBE Layer Styles");
        if (!srcLS || !dstLS) return;

        function recurseCopy(srcGroup, dstGroup) {
            if (!srcGroup || !dstGroup) return;
            for (var i = 1; i <= srcGroup.numProperties; i++) {
                var sp = srcGroup.property(i);
                var dp = dstGroup.property(sp.matchName);
                if (!dp) continue;

                if (sp.numProperties && sp.numProperties > 0) {
                    recurseCopy(sp, dp);
                } else {
                    copyKeysAndValue(sp, dp);
                }
            }
        }
        recurseCopy(srcLS, dstLS);
    }

    // -------------------- SMART: Animator update (no wipe) --------------------
    function findAnimatorByName(animatorsGroup, name) {
        for (var i = 1; i <= animatorsGroup.numProperties; i++) {
            var a = animatorsGroup.property(i);
            if ((a.name || "") === name) return a;
        }
        return null;
    }

    function copyAnimatorPropsSMART(fromAnim, toAnim) {
        var fromAnimProps = fromAnim.property("ADBE Text Animator Properties");
        var toAnimProps = toAnim.property("ADBE Text Animator Properties");
        if (!fromAnimProps || !toAnimProps) return;

        for (var pi = 1; pi <= fromAnimProps.numProperties; pi++) {
            var sp = fromAnimProps.property(pi);
            if (!sp || isUnsupportedProperty(sp.matchName)) continue;

            var dp = toAnimProps.property(sp.matchName);
            if (!dp) {
                // add missing prop (best effort)
                dp = safeAddProperty(toAnimProps, sp.matchName);
            }
            if (!dp) continue;

            copyKeysAndValue(sp, dp);
        }
    }

    function copyAnimatorsSMART(fromLayer, toLayer) {
        var fromTextProps = fromLayer.property("ADBE Text Properties");
        var toTextProps = toLayer.property("ADBE Text Properties");
        if (!fromTextProps || !toTextProps) return;

        var fromAnimators = fromTextProps.property("ADBE Text Animators");
        var toAnimators = toTextProps.property("ADBE Text Animators");
        if (!fromAnimators || !toAnimators) return;

        // Always preserve highlight Start/End keys
        var keepHighlight = captureHighlightKeys(toLayer);

        for (var ai = 1; ai <= fromAnimators.numProperties; ai++) {
            var fromAnim = fromAnimators.property(ai);
            if (!fromAnim) continue;

            var name = fromAnim.name || ("Animator " + ai);
            var toAnim = findAnimatorByName(toAnimators, name);
            if (!toAnim) {
                // add missing animator
                try {
                    toAnim = toAnimators.addProperty("ADBE Text Animator");
                    toAnim.name = name;
                } catch (e) {
                    toAnim = null;
                }
            }
            if (!toAnim) continue;

            // Copy animator properties (selectors left mostly untouched to avoid nuking range keys)
            copyAnimatorPropsSMART(fromAnim, toAnim);
        }

        // Ensure Highlight LOOK is copied (even if we didn't find it in loop)
        copyHighlightLook(fromLayer, toLayer);

        // Restore highlight range keys after any changes
        restoreHighlightKeys(toLayer, keepHighlight);
    }

    // -------------------- FULL (slow): rebuild animators + effects + layer styles --------------------
    function copyAnimatorsFULL(fromLayer, toLayer) {
        var fromTextProps = fromLayer.property("ADBE Text Properties");
        var toTextProps = toLayer.property("ADBE Text Properties");
        if (!fromTextProps || !toTextProps) return;

        var fromAnimators = fromTextProps.property("ADBE Text Animators");
        var toAnimators = toTextProps.property("ADBE Text Animators");
        if (!fromAnimators || !toAnimators) return;

        var keepHighlight = captureHighlightKeys(toLayer);

        while (toAnimators.numProperties > 0) {
            toAnimators.property(1).remove();
        }

        for (var ai = 1; ai <= fromAnimators.numProperties; ai++) {
            var fromAnim = fromAnimators.property(ai);
            var toAnim = toAnimators.addProperty("ADBE Text Animator");
            toAnim.name = fromAnim.name;

            var fromAnimProps = fromAnim.property("ADBE Text Animator Properties");
            var toAnimProps = toAnim.property("ADBE Text Animator Properties");

            for (var pi = 1; pi <= fromAnimProps.numProperties; pi++) {
                var p = fromAnimProps.property(pi);
                var newP = safeAddProperty(toAnimProps, p.matchName);
                if (newP) copyKeysAndValue(p, newP);
            }

            var fromSels = fromAnim.property("ADBE Text Selectors");
            var toSels = toAnim.property("ADBE Text Selectors");
            for (var si = 1; si <= fromSels.numProperties; si++) {
                var sel = fromSels.property(si);
                var newSel = safeAddProperty(toSels, sel.matchName);
                if (!newSel) continue;
                newSel.name = sel.name;

                for (var sp = 1; sp <= sel.numProperties; sp++) {
                    var sprop = sel.property(sp);
                    var dprop = newSel.property(sprop.matchName);
                    if (!dprop) continue;

                    if (sprop.numProperties && sprop.numProperties > 0) {
                        for (var sp2 = 1; sp2 <= sprop.numProperties; sp2++) {
                            var ss = sprop.property(sp2);
                            var dd = dprop.property(ss.matchName);
                            if (!dd) continue;
                            copyKeysAndValue(ss, dd);
                        }
                    } else {
                        copyKeysAndValue(sprop, dprop);
                    }
                }
            }
        }

        restoreHighlightKeys(toLayer, keepHighlight);
    }

    function copyEffectsFULL(fromLayer, toLayer) {
        var srcFX = fromLayer.property("ADBE Effect Parade");
        var dstFX = toLayer.property("ADBE Effect Parade");
        if (!srcFX || !dstFX) return;

        try {
            while (dstFX.numProperties > 0) dstFX.property(1).remove();
        } catch (e) { }

        for (var i = 1; i <= srcFX.numProperties; i++) {
            var srcEff = srcFX.property(i);
            var newEff = safeAddProperty(dstFX, srcEff.matchName);
            if (!newEff) continue;
            newEff.name = srcEff.name;

            for (var p = 1; p <= srcEff.numProperties; p++) {
                var sp = srcEff.property(p);
                var dp = newEff.property(p);
                if (!dp) continue;
                copyKeysAndValue(sp, dp);
            }
        }
    }

    function copyLayerStylesFULL(fromLayer, toLayer) {
        var srcLS = fromLayer.property("ADBE Layer Styles");
        var dstLS = toLayer.property("ADBE Layer Styles");
        if (!srcLS || !dstLS) return;

        function recurseCopy(srcGroup, dstGroup) {
            if (!srcGroup || !dstGroup) return;
            for (var i = 1; i <= srcGroup.numProperties; i++) {
                var sp = srcGroup.property(i);
                var dp = dstGroup.property(sp.matchName);
                if (!dp) continue;

                if (sp.numProperties && sp.numProperties > 0) recurseCopy(sp, dp);
                else copyKeysAndValue(sp, dp);
            }
        }

        recurseCopy(srcLS, dstLS);
    }

    // -------------------- Apply modes --------------------
    function applyFAST(master, layer) {
        var keepIn = layer.inPoint;
        var keepOut = layer.outPoint;

        copyLayerBasics(master, layer);
        copyTransform(master, layer);
        cloneTextDocumentStyle(master, layer);
        copyHighlightLook(master, layer);

        layer.inPoint = keepIn;
        layer.outPoint = keepOut;
    }

    function applySMART(master, layer) {
        var keepIn = layer.inPoint;
        var keepOut = layer.outPoint;

        copyLayerBasics(master, layer);
        copyTransform(master, layer);
        cloneTextDocumentStyle(master, layer);

        // Keep highlight keys; update highlight look; update other animator properties without wiping
        copyAnimatorsSMART(master, layer);

        // Update FX / Layer Styles without delete
        copyEffectsSMART(master, layer);
        copyLayerStylesSMART(master, layer);

        layer.inPoint = keepIn;
        layer.outPoint = keepOut;
    }

    function applyFULL(master, layer) {
        var keepIn = layer.inPoint;
        var keepOut = layer.outPoint;

        copyLayerBasics(master, layer);
        copyTransform(master, layer);
        cloneTextDocumentStyle(master, layer);

        copyAnimatorsFULL(master, layer);
        copyEffectsFULL(master, layer);
        copyLayerStylesFULL(master, layer);

        layer.inPoint = keepIn;
        layer.outPoint = keepOut;
    }

    // -------------------- UI (hübschi) --------------------
    function showUI() {
        var w = new Window("dialog", "LumiCap Apply Master Styles 😈💜");
        w.orientation = "column";
        w.alignChildren = ["fill", "top"];

        var modePanel = w.add("panel", undefined, "Mode");
        modePanel.orientation = "column";
        modePanel.alignChildren = ["left", "top"];

        var rbFast = modePanel.add("radiobutton", undefined, "FAST  — Text + Transform + Highlight Look (sehr schnell)");
        var rbSmart = modePanel.add("radiobutton", undefined, "SMART — FAST + Effects/LayerStyles + Animator-Props (Sweet Spot)");
        var rbFull = modePanel.add("radiobutton", undefined, "FULL  — Rebuild alles (langsam, aber maximal)");

        rbFast.value = true;

        var scopePanel = w.add("panel", undefined, "Scope");
        scopePanel.orientation = "column";
        scopePanel.alignChildren = ["left", "top"];
        var cbSelectedOnly = scopePanel.add("checkbox", undefined, "Nur ausgewählte Layers (sonst alle Captions im Comp)");
        cbSelectedOnly.value = false;

        var infoTxt = w.add("statictext", undefined, "Hinweis: Timings bleiben immer. Highlight-Range-Keys bleiben immer.");
        infoTxt.graphics.font = ScriptUI.newFont(infoTxt.graphics.font.name, "ITALIC", infoTxt.graphics.font.size);

        var btnRow = w.add("group");
        btnRow.orientation = "row";
        btnRow.alignment = "right";

        var btnCancel = btnRow.add("button", undefined, "Abbrechen");
        var btnOk = btnRow.add("button", undefined, "Apply 😈", { name: "ok" });

        var res = { ok: false, mode: "FAST", selectedOnly: false };
        btnOk.onClick = function () {
            res.ok = true;
            res.mode = rbFast.value ? "FAST" : (rbSmart.value ? "SMART" : "FULL");
            res.selectedOnly = cbSelectedOnly.value;
            w.close();
        };
        btnCancel.onClick = function () {
            res.ok = false;
            w.close();
        };

        w.center();
        w.show();
        return res;
    }

    function showProgress(total) {
        var w = new Window("palette", "Applying… 😈");
        w.orientation = "column";
        w.alignChildren = ["fill", "top"];

        var txt = w.add("statictext", undefined, "Starting…");
        var bar = w.add("progressbar", undefined, 0, Math.max(1, total));
        bar.preferredSize = [420, 18];

        var row = w.add("group");
        row.orientation = "row";
        row.alignment = "right";

        var btnStop = row.add("button", undefined, "Stop");
        var btnClose = row.add("button", undefined, "Close"); // 👈 neu

        var state = { stop: false };

        function forceClose() {
            try { w.hide(); } catch (e) { }
            try { w.visible = false; } catch (e) { }
            try { w.close(); } catch (e2) { }
        }

        btnStop.onClick = function () { state.stop = true; forceClose(); };
        btnClose.onClick = function () { state.stop = true; forceClose(); };

        // Falls User aufs ✖️ klickt: wenigstens stoppen + close versuchen
        w.onClose = function () { state.stop = true; return true; };

        w.show();

        return {
            state: state,
            update: function (i, label) {
                try {
                    txt.text = label || ("Layer " + i + "/" + total);
                    bar.value = i;
                    w.update();
                } catch (e) { }
            },
            forceClose: forceClose
        };
    }

    // -------------------- Layer iteration --------------------
    function collectTargetLayers(comp, selectedOnly) {
        var out = [];

        if (selectedOnly) {
            var sel = comp.selectedLayers;
            for (var i = 0; i < sel.length; i++) {
                if (sel[i] && (sel[i] instanceof TextLayer)) out.push(sel[i]);
            }
            return out;
        }

        for (var j = 1; j <= comp.numLayers; j++) {
            var layer = comp.layer(j);
            if (!layer || !(layer instanceof TextLayer)) continue;
            if ((layer.name || "").match(/^\s*Master\s+/i)) continue; // skip masters
            // only caption layers with [Style]
            if (!parseStyleFromName(layer.name)) continue;
            out.push(layer);
        }
        return out;
    }

    // -------------------- MAIN --------------------
    var prog = null;

    try {
        if (!app.project) throw new Error("Open an AE project first.");
        var comp = getActiveComp();

        var ui = showUI();
        if (!ui.ok) return;

        var masterMap = buildMasterMap(comp);
        var targets = collectTargetLayers(comp, ui.selectedOnly);

        if (targets.length === 0) {
            alert("Keine Caption Layers gefunden 😅\n(Tipp: Layer müssen mit [Style] beginnen.)");
            return;
        }

        prog = showProgress(targets.length); // 👈 KEIN var

        var applied = 0;
        var skipped = 0;

        app.beginUndoGroup("LumiCap Apply Master Styles (" + ui.mode + ")");

        for (var i = 0; i < targets.length; i++) {
            if (prog.state.stop) break;

            var layer = targets[i];
            var style = parseStyleFromName(layer.name);
            if (!style) { skipped++; continue; }

            var master = masterMap[style] || masterMap["Normal"] || null;
            if (!master) { skipped++; continue; }

            prog.update(i + 1, ui.mode + " → " + layer.name);

            if (ui.mode === "FAST") applyFAST(master, layer);
            else if (ui.mode === "SMART") applySMART(master, layer);
            else applyFULL(master, layer);

            applied++;

            // AE nicht komplett sterben lassen
            if ((i % 10) === 0) {
                try { app.refresh(); } catch (e) { }
            }
        }

        app.endUndoGroup();

        if (prog.state.stop) {
            alert("⛔ Apply gestoppt.\nApplied: " + applied + "\nSkipped: " + skipped);
        } else {
            alert("✅ Apply fertig! (" + ui.mode + ")\nApplied: " + applied + "\nSkipped: " + skipped);
        }

    } catch (err) {
        try { alert("❌ LumiCap Apply Error:\n" + err.toString()); } catch (e) { }
    } finally {
        if (prog) prog.forceClose(); // 👈 IMMER
    }
})();