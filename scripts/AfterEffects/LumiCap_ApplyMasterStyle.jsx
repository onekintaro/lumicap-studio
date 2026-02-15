// LumiCap_ApplyMasterStyle.jsx — AE 2026
// Apply ALL visual properties from "Master <Style>" to caption layers named "[Style] ..."
// Keeps ONLY:
// - layer inPoint / outPoint (timing)
// - Highlight range selector keyframes (Percent Start/End) coming from .lcap steps
//
// Also skips Variable Font Axis props that can't be addProperty()'d (ADBE Text VF Axis *)

(function () {
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

  // ---------- Safe addProperty / skip rules ----------
  function isUnsupportedProperty(matchName) {
    if (!matchName) return false;
    // Variable font axes (cannot be added via script)
    if (matchName.indexOf("ADBE Text VF Axis") === 0) return true;
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

  // ---------- Keyframe copy helper ----------
  function copyKeysAndValue(srcProp, dstProp) {
    if (!srcProp || !dstProp) return;
    try {
      // clear dst keys
      while (dstProp.numKeys > 0) dstProp.removeKey(1);

      if (srcProp.numKeys && srcProp.numKeys > 0) {
        for (var k = 1; k <= srcProp.numKeys; k++) {
          var t = srcProp.keyTime(k);
          dstProp.setValueAtTime(t, srcProp.keyValue(k));
          // Try preserve HOLD for discrete properties (safe)
          try {
            dstProp.setInterpolationTypeAtKey(
              dstProp.nearestKeyIndex(t),
              KeyframeInterpolationType.HOLD,
              KeyframeInterpolationType.HOLD
            );
          } catch (e2) {}
        }
      } else {
        // static value
        dstProp.setValue(srcProp.value);
      }
    } catch (e) {}
  }

  // ---------- TextDocument style copy (keep text) ----------
  function cloneTextDocumentStyle(fromLayer, toLayer) {
    var fromProp = fromLayer.property("Source Text");
    var toProp = toLayer.property("Source Text");
    var fromDoc = fromProp.value;
    var toDoc = toProp.value;

    var keepText = toDoc.text; // keep caption content
    toProp.setValue(fromDoc);
    var newDoc = toProp.value;
    newDoc.text = keepText;
    toProp.setValue(newDoc);
  }

  // ---------- Transform copy (keep in/out) ----------
  function copyTransform(fromLayer, toLayer) {
    var srcT = fromLayer.property("Transform");
    var dstT = toLayer.property("Transform");
    if (!srcT || !dstT) return;

    // Copy standard transform props (including keys if present)
    copyKeysAndValue(srcT.property("Anchor Point"), dstT.property("Anchor Point"));
    copyKeysAndValue(srcT.property("Position"), dstT.property("Position"));
    copyKeysAndValue(srcT.property("Scale"), dstT.property("Scale"));
    copyKeysAndValue(srcT.property("Rotation"), dstT.property("Rotation"));
    // Some layers use separate rotations in 3D; we copy if present
    copyKeysAndValue(srcT.property("X Rotation"), dstT.property("X Rotation"));
    copyKeysAndValue(srcT.property("Y Rotation"), dstT.property("Y Rotation"));
    copyKeysAndValue(srcT.property("Z Rotation"), dstT.property("Z Rotation"));
    copyKeysAndValue(srcT.property("Opacity"), dstT.property("Opacity"));
  }

  // ---------- Effects copy (values + keys where possible) ----------
  function copyEffects(fromLayer, toLayer) {
    var srcFX = fromLayer.property("ADBE Effect Parade");
    var dstFX = toLayer.property("ADBE Effect Parade");
    if (!srcFX || !dstFX) return;

    // clear dst effects
    try {
      while (dstFX.numProperties > 0) dstFX.property(1).remove();
    } catch (e) {}

    // recreate
    for (var i = 1; i <= srcFX.numProperties; i++) {
      var srcEff = srcFX.property(i);
      var newEff = safeAddProperty(dstFX, srcEff.matchName);
      if (!newEff) continue;
      newEff.name = srcEff.name;

      // copy effect params
      for (var p = 1; p <= srcEff.numProperties; p++) {
        var sp = srcEff.property(p);
        var dp = newEff.property(p);
        // Skip groups that don't map 1:1 safely
        if (!dp) continue;
        copyKeysAndValue(sp, dp);
      }
    }
  }

  // ---------- Layer Styles copy ----------
  function copyLayerStyles(fromLayer, toLayer) {
    var srcLS = fromLayer.property("ADBE Layer Styles");
    var dstLS = toLayer.property("ADBE Layer Styles");
    if (!srcLS || !dstLS) return;

    // Layer styles are sub-groups; easiest: copy known common ones if present
    // We'll try to mirror properties by matchName recursively (lightly).
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

  // ---------- Highlight keyframes preservation ----------
  function findHighlightSelector(layer) {
    var textProps = layer.property("ADBE Text Properties");
    if (!textProps) return null;
    var animators = textProps.property("ADBE Text Animators");
    if (!animators) return null;

    for (var i = 1; i <= animators.numProperties; i++) {
      var a = animators.property(i);
      if ((a.name || "") === "Highlight") {
        var sels = a.property("ADBE Text Selectors");
        if (sels && sels.numProperties >= 1) return sels.property(1);
      }
    }
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
      try { while (prop.numKeys > 0) prop.removeKey(1); } catch (e) {}
      if (cap.keys && cap.keys.length > 0) {
        for (var i = 0; i < cap.keys.length; i++) {
          prop.setValueAtTime(cap.keys[i].t, cap.keys[i].v);
          try {
            prop.setInterpolationTypeAtKey(
              prop.nearestKeyIndex(cap.keys[i].t),
              KeyframeInterpolationType.HOLD,
              KeyframeInterpolationType.HOLD
            );
          } catch (e2) {}
        }
      } else if (cap.value != null) {
        try { prop.setValue(cap.value); } catch (e3) {}
      }
    }

    restore(startProp, data.start);
    restore(endProp, data.end);
  }

  // ---------- Animators copy (skip VF axis + keep highlight keyframes) ----------
  function copyAnimators(fromLayer, toLayer) {
    var fromTextProps = fromLayer.property("ADBE Text Properties");
    var toTextProps = toLayer.property("ADBE Text Properties");
    if (!fromTextProps || !toTextProps) return;

    var fromAnimators = fromTextProps.property("ADBE Text Animators");
    var toAnimators = toTextProps.property("ADBE Text Animators");
    if (!fromAnimators || !toAnimators) return;

    // Capture highlight step keys from target BEFORE we wipe animators
    var keepHighlight = captureHighlightKeys(toLayer);

    // Clear existing animators on target
    while (toAnimators.numProperties > 0) {
      toAnimators.property(1).remove();
    }

    // Recreate animator stack from master
    for (var ai = 1; ai <= fromAnimators.numProperties; ai++) {
      var fromAnim = fromAnimators.property(ai);
      var toAnim = toAnimators.addProperty("ADBE Text Animator");
      toAnim.name = fromAnim.name;

      // Animator Properties
      var fromAnimProps = fromAnim.property("ADBE Text Animator Properties");
      var toAnimProps = toAnim.property("ADBE Text Animator Properties");

      for (var pi = 1; pi <= fromAnimProps.numProperties; pi++) {
        var p = fromAnimProps.property(pi);
        var newP = safeAddProperty(toAnimProps, p.matchName);
        if (newP) {
          // copy keys/value
          copyKeysAndValue(p, newP);
        }
      }

      // Selectors
      var fromSels = fromAnim.property("ADBE Text Selectors");
      var toSels = toAnim.property("ADBE Text Selectors");
      for (var si = 1; si <= fromSels.numProperties; si++) {
        var sel = fromSels.property(si);
        var newSel = safeAddProperty(toSels, sel.matchName);
        if (!newSel) continue;
        newSel.name = sel.name;

        // Copy selector properties recursively (but we will restore highlight start/end after)
        for (var sp = 1; sp <= sel.numProperties; sp++) {
          var sprop = sel.property(sp);
          var dprop = newSel.property(sprop.matchName);
          if (!dprop) continue;

          if (sprop.numProperties && sprop.numProperties > 0) {
            // light recursion
            // (skip deep copy of exotic groups; but most selector props are flat)
            // We'll just try copy value/keys where possible
            // If it errors, we ignore.
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

    // Restore highlight step keys (Start/End) so .lcap animation stays
    restoreHighlightKeys(toLayer, keepHighlight);
  }

  // ---------- Layer switches / misc ----------
  function copyLayerBasics(fromLayer, toLayer) {
    try { toLayer.blendingMode = fromLayer.blendingMode; } catch (e) {}
    try { toLayer.motionBlur = fromLayer.motionBlur; } catch (e) {}
    try { toLayer.threeDLayer = fromLayer.threeDLayer; } catch (e) {}
    try { toLayer.adjustmentLayer = fromLayer.adjustmentLayer; } catch (e) {}
    try { toLayer.collapseTransformation = fromLayer.collapseTransformation; } catch (e) {}
    try { toLayer.guideLayer = fromLayer.guideLayer; } catch (e) {} // usually false for captions, but "ALL" means ALL 😈
    try { toLayer.shy = fromLayer.shy; } catch (e) {}
    try { toLayer.locked = fromLayer.locked; } catch (e) {}
  }

  function applyMasterToLayer(master, layer) {
    // Keep timing
    var keepIn = layer.inPoint;
    var keepOut = layer.outPoint;

    // Copy everything visual
    copyLayerBasics(master, layer);
    copyTransform(master, layer);
    cloneTextDocumentStyle(master, layer);
    copyAnimators(master, layer);
    copyEffects(master, layer);
    copyLayerStyles(master, layer);

    // Restore timing
    layer.inPoint = keepIn;
    layer.outPoint = keepOut;
  }

  // ---------- main ----------
  try {
    if (!app.project) throw new Error("Open an AE project first.");
    var comp = getActiveComp();

    var masterMap = buildMasterMap(comp);
    var applied = 0;
    var skipped = 0;

    app.beginUndoGroup("LumiCap Apply Master Styles (ALL)");

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