// LumiCap_ApplyMasterStyle.jsx — AE 2026
// Apply visual styles from "Master <Style>" layers to caption layers named "[Style] ..."

(function () {
  function getActiveComp() {
    var item = app.project && app.project.activeItem;
    if (!item || !(item instanceof CompItem)) throw new Error("Select an active composition first.");
    return item;
  }

  function parseStyleFromName(name) {
    // "[Chorus] bla" -> "Chorus"
    if (!name) return null;
    var m = name.match(/^\s*\[([^\]]+)\]/);
    return m ? m[1] : null;
  }

  function buildMasterMap(comp) {
    var map = {}; // style -> layer
    for (var i = 1; i <= comp.numLayers; i++) {
      var l = comp.layer(i);
      if (!l || !(l instanceof TextLayer)) continue;

      // Master naming: "Master Style"
      var nm = l.name || "";
      var mm = nm.match(/^\s*Master\s+(.+)\s*$/i);
      if (mm && mm[1]) {
        var style = mm[1];
        map[style] = l;
      }
    }
    return map;
  }

  function cloneTextDocumentStyle(fromLayer, toLayer) {
    var fromProp = fromLayer.property("Source Text");
    var toProp = toLayer.property("Source Text");
    var fromDoc = fromProp.value;
    var toDoc = toProp.value;

    // Copy everything style-related but keep the caption text content:
    var keepText = toDoc.text;

    // Transfer full doc then restore text
    toProp.setValue(fromDoc);
    var newDoc = toProp.value;
    newDoc.text = keepText;
    toProp.setValue(newDoc);
  }

  function clearAnimators(layer) {
    var textProps = layer.property("ADBE Text Properties");
    var animators = textProps.property("ADBE Text Animators");
    while (animators.numProperties > 0) {
      animators.property(1).remove();
    }
  }

  function copyAnimators(fromLayer, toLayer) {
    // Brutal-but-effective approach:
    // - Remove animators on target
    // - Duplicate fromLayer, steal animators by copy-paste properties isn't directly available in ExtendScript
    // So we rebuild by duplicating and swapping Source Text back.

    // Easiest reliable: copy entire layer properties by duplicating master and then moving timing/text.
    // But that changes layer order/name etc. We avoid that for MVP.

    // Alternative: use propertyMatchNames to recreate minimal structure: Animator + Fill + Range Selector.
    // We'll implement a pragmatic approach:
    // - If master has animators, we recreate the same matchNames tree shallowly.
    // - Then we copy values (not keyframes) from corresponding properties when possible.

    var fromTextProps = fromLayer.property("ADBE Text Properties");
    var toTextProps = toLayer.property("ADBE Text Properties");
    var fromAnimators = fromTextProps.property("ADBE Text Animators");
    var toAnimators = toTextProps.property("ADBE Text Animators");

    // Clear existing animators on target
    while (toAnimators.numProperties > 0) {
      toAnimators.property(1).remove();
    }

    // Recreate animator stack
    for (var ai = 1; ai <= fromAnimators.numProperties; ai++) {
      var fromAnim = fromAnimators.property(ai);
      var toAnim = toAnimators.addProperty("ADBE Text Animator");
      toAnim.name = fromAnim.name;

      // Animator Properties
      var fromAnimProps = fromAnim.property("ADBE Text Animator Properties");
      var toAnimProps = toAnim.property("ADBE Text Animator Properties");

      // Copy each animator property (fill/stroke/scale/etc.)
      for (var pi = 1; pi <= fromAnimProps.numProperties; pi++) {
        var p = fromAnimProps.property(pi);
        var newP = toAnimProps.addProperty(p.matchName);
        if (newP) {
          try {
            // copy static value if possible
            if (p.numKeys === 0) newP.setValue(p.value);
          } catch (e) {}
        }
      }

      // Selectors
      var fromSels = fromAnim.property("ADBE Text Selectors");
      var toSels = toAnim.property("ADBE Text Selectors");

      for (var si = 1; si <= fromSels.numProperties; si++) {
        var sel = fromSels.property(si);
        var newSel = toSels.addProperty(sel.matchName);
        if (newSel) {
          newSel.name = sel.name;

          // Copy selector properties (including keyframes)
          // We'll try to copy a few common ones; especially Percent Start/End with keys.
          var srcStart = sel.property("ADBE Text Percent Start");
          var srcEnd = sel.property("ADBE Text Percent End");
          var dstStart = newSel.property("ADBE Text Percent Start");
          var dstEnd = newSel.property("ADBE Text Percent End");

          if (srcStart && dstStart) {
            // clear keys
            while (dstStart.numKeys > 0) dstStart.removeKey(1);
            if (srcStart.numKeys > 0) {
              for (var k = 1; k <= srcStart.numKeys; k++) {
                var t = srcStart.keyTime(k);
                dstStart.setValueAtTime(t, srcStart.keyValue(k));
                try {
                  dstStart.setInterpolationTypeAtKey(dstStart.nearestKeyIndex(t), KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD);
                } catch (e) {}
              }
            } else {
              try { dstStart.setValue(srcStart.value); } catch (e) {}
            }
          }

          if (srcEnd && dstEnd) {
            while (dstEnd.numKeys > 0) dstEnd.removeKey(1);
            if (srcEnd.numKeys > 0) {
              for (var k2 = 1; k2 <= srcEnd.numKeys; k2++) {
                var t2 = srcEnd.keyTime(k2);
                dstEnd.setValueAtTime(t2, srcEnd.keyValue(k2));
                try {
                  dstEnd.setInterpolationTypeAtKey(dstEnd.nearestKeyIndex(t2), KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD);
                } catch (e) {}
              }
            } else {
              try { dstEnd.setValue(srcEnd.value); } catch (e) {}
            }
          }
        }
      }
    }
  }

  function applyMasterToLayer(master, layer) {
    // Copy TextDocument style
    cloneTextDocumentStyle(master, layer);
    // Copy Animators (incl. highlight settings) from master
    copyAnimators(master, layer);
  }

  // ---------- main ----------
  try {
    if (!app.project) throw new Error("Open an AE project first.");
    var comp = getActiveComp();

    var masterMap = buildMasterMap(comp);
    var applied = 0;
    var skipped = 0;

    app.beginUndoGroup("LumiCap Apply Master Styles");

    for (var i = 1; i <= comp.numLayers; i++) {
      var layer = comp.layer(i);
      if (!layer || !(layer instanceof TextLayer)) continue;

      // ignore master layers
      if ((layer.name || "").match(/^\s*Master\s+/i)) continue;

      var style = parseStyleFromName(layer.name);
      if (!style) { skipped++; continue; }

      var master = masterMap[style] || masterMap["Normal"] || null;
      if (!master) { skipped++; continue; }

      applyMasterToLayer(master, layer);
      applied++;
    }

    app.endUndoGroup();

    alert("✅ Apply Master Styles fertig!\nApplied: " + applied + "\nSkipped: " + skipped);

  } catch (err) {
    alert("❌ LumiCap Apply Error:\n" + err.toString());
  }
})();