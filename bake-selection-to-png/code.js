figma.showUI(__html__, {
  width: 440,
  height: 620,
  themeColors: true
});

const ROOT_TYPES = new Set(["FRAME", "GROUP", "COMPONENT", "COMPONENT_SET", "SECTION"]);
const CONTAINER_TYPES = new Set([
  "FRAME",
  "GROUP",
  "COMPONENT",
  "COMPONENT_SET",
  "INSTANCE",
  "SECTION",
  "BOOLEAN_OPERATION",
  "VECTOR"
]);

function hasChildren(node) {
  return node && "children" in node;
}

function isSupportedRoot(node) {
  return node && ROOT_TYPES.has(node.type) && hasChildren(node);
}

function isSceneNode(node) {
  return node && "x" in node && "y" in node && "width" in node && "height" in node;
}

function isContainerNode(node) {
  return hasChildren(node) || CONTAINER_TYPES.has(node.type);
}

function getRenderBounds(node) {
  return node.absoluteRenderBounds || node.absoluteBoundingBox;
}

function getLayoutBounds(node) {
  return node.absoluteBoundingBox || node.absoluteRenderBounds;
}

function collectDescendants(root, depth = 0, result = []) {
  if (!hasChildren(root)) return result;

  root.children.forEach((child) => {
    const canExpand = hasChildren(child) && child.children.length > 0 && child.type !== "INSTANCE";

    result.push({
      id: child.id,
      parentId: root.id,
      name: child.name,
      type: child.type,
      depth,
      visible: child.visible,
      locked: child.locked,
      hasChildren: canExpand
    });

    if (canExpand) {
      collectDescendants(child, depth + 1, result);
    }
  });

  return result;
}

function getRootState() {
  const selection = figma.currentPage.selection;

  if (selection.length !== 1) {
    return {
      type: "root",
      valid: false,
      reason: selection.length === 0 ? "请先选中一个组或 Frame。" : "一次只选择一个组或 Frame。"
    };
  }

  const root = selection[0];
  if (!isSupportedRoot(root)) {
    return {
      type: "root",
      valid: false,
      reason: "当前选区没有子图层，请选择一个组或 Frame。"
    };
  }

  const descendants = collectDescendants(root);

  if (descendants.length === 0) {
    return {
      type: "root",
      valid: false,
      reason: "这个组里没有可选择的子图层。"
    };
  }

  return {
    type: "root",
    valid: true,
    rootId: root.id,
    rootName: root.name,
    rootType: root.type,
    children: descendants,
    defaultSelectedIds: descendants
      .filter((child) => child.visible && child.type !== "TEXT" && !child.hasChildren)
      .map((child) => child.id)
  };
}

function postRootState() {
  figma.ui.postMessage(getRootState());
}

function getNodeById(id) {
  const node = figma.getNodeById(id);
  if (!node) throw new Error("找不到选中的图层，请重新选择后再试。");
  return node;
}

function assertRoot(rootId) {
  const root = getNodeById(rootId);
  if (!isSupportedRoot(root)) {
    throw new Error("请选择一个包含子图层的组或 Frame。");
  }
  return root;
}

function isDescendantOf(node, ancestor) {
  let current = node.parent;
  while (current) {
    if (current === ancestor) return true;
    current = current.parent;
  }
  return false;
}

function filterNestedNodes(nodes, root) {
  const selectedIds = new Set(nodes.map((node) => node.id));

  return nodes.filter((node) => {
    let current = node.parent;
    while (current && current !== root) {
      if (selectedIds.has(current.id)) return false;
      current = current.parent;
    }
    return true;
  });
}

function compareNumberArrays(first, second) {
  const length = Math.min(first.length, second.length);

  for (let index = 0; index < length; index += 1) {
    if (first[index] !== second[index]) return first[index] - second[index];
  }

  return first.length - second.length;
}

function sortByDocumentOrder(nodes, root) {
  return nodes.slice().sort((first, second) => {
    const firstPath = getPathFromAncestor(root, first) || [];
    const secondPath = getPathFromAncestor(root, second) || [];
    return compareNumberArrays(firstPath, secondPath);
  });
}

function getSelectedDescendants(root, childIds) {
  if (!Array.isArray(childIds) || childIds.length === 0) {
    throw new Error("请至少勾选一个要打进 PNG 的块。");
  }

  const nodes = childIds.map((id) => getNodeById(id));

  nodes.forEach((node) => {
    if (!isSceneNode(node) || !isDescendantOf(node, root)) {
      throw new Error("勾选的图层不在当前组内，请刷新选择后再试。");
    }

    if (!getRenderBounds(node)) {
      throw new Error(`“${node.name}” 没有可导出的可见区域。`);
    }
  });

  return sortByDocumentOrder(filterNestedNodes(nodes, root), root);
}

function assertPreviewNode(rootId, nodeId) {
  const root = assertRoot(rootId);
  const node = getNodeById(nodeId);

  if (!isSceneNode(node) || !isDescendantOf(node, root)) {
    throw new Error("这个图层不在当前组内，请刷新后再试。");
  }

  if (!getRenderBounds(node)) {
    throw new Error(`“${node.name}” 没有可预览的可见区域。`);
  }

  return node;
}

function getUnionBounds(nodes) {
  const bounds = nodes.map(getRenderBounds).filter(Boolean);
  const left = Math.min(...bounds.map((bound) => bound.x));
  const top = Math.min(...bounds.map((bound) => bound.y));
  const right = Math.max(...bounds.map((bound) => bound.x + bound.width));
  const bottom = Math.max(...bounds.map((bound) => bound.y + bound.height));

  return {
    x: left,
    y: top,
    width: right - left,
    height: bottom - top
  };
}

function hasVisiblePaint(paints) {
  return Array.isArray(paints) && paints.some((paint) => paint.visible !== false);
}

function hasVisibleEffects(effects) {
  return Array.isArray(effects) && effects.some((effect) => effect.visible !== false);
}

function hasRoundedCorners(node) {
  const isPositiveRadius = (value) => typeof value === "number" && value > 0;

  return (
    "cornerRadius" in node &&
    (isPositiveRadius(node.cornerRadius) ||
      isPositiveRadius(node.topLeftRadius) ||
      isPositiveRadius(node.topRightRadius) ||
      isPositiveRadius(node.bottomLeftRadius) ||
      isPositiveRadius(node.bottomRightRadius))
  );
}

function hasVisualShell(node) {
  return (
    isSceneNode(node) &&
    (hasVisiblePaint(node.fills) ||
      hasVisiblePaint(node.strokes) ||
      hasVisibleEffects(node.effects) ||
      hasRoundedCorners(node) ||
      Boolean(node.clipsContent))
  );
}

function getAncestorShells(node, stopNode) {
  const shells = [];
  let current = node.parent;

  while (current) {
    if (isSceneNode(current) && hasVisualShell(current)) {
      shells.push(current);
    }

    if (current === stopNode) break;
    current = current.parent;
  }

  return shells;
}

function getExportBounds(nodes, targetParent) {
  const boundsNodes = [...nodes];

  nodes.forEach((node) => {
    getAncestorShells(node, targetParent).forEach((shell) => {
      if (!boundsNodes.includes(shell)) boundsNodes.push(shell);
    });
  });

  return getUnionBounds(boundsNodes);
}

function multiplyTransform(a, b) {
  return [
    [
      a[0][0] * b[0][0] + a[0][1] * b[1][0],
      a[0][0] * b[0][1] + a[0][1] * b[1][1],
      a[0][0] * b[0][2] + a[0][1] * b[1][2] + a[0][2]
    ],
    [
      a[1][0] * b[0][0] + a[1][1] * b[1][0],
      a[1][0] * b[0][1] + a[1][1] * b[1][1],
      a[1][0] * b[0][2] + a[1][1] * b[1][2] + a[1][2]
    ]
  ];
}

function invertTransform(transform) {
  const [[a, c, e], [b, d, f]] = transform;
  const determinant = a * d - b * c;

  if (Math.abs(determinant) < 0.000001) {
    throw new Error("当前图层变换过于复杂，无法稳定放回 PNG。");
  }

  return [
    [d / determinant, -c / determinant, (c * f - d * e) / determinant],
    [-b / determinant, a / determinant, (b * e - a * f) / determinant]
  ];
}

function getRelativeTransformForParent(parent, absoluteTransform) {
  if (parent && "absoluteTransform" in parent) {
    return multiplyTransform(invertTransform(parent.absoluteTransform), absoluteTransform);
  }

  return absoluteTransform;
}

function getBoundsTransform(bounds) {
  return [
    [1, 0, bounds.x],
    [0, 1, bounds.y]
  ];
}

function setAbsoluteTransform(node, absoluteTransform) {
  node.relativeTransform = getRelativeTransformForParent(node.parent, absoluteTransform);
}

function getStableOutputParent(targetParent) {
  let outputParent = targetParent;

  while (
    outputParent &&
    outputParent.type === "GROUP" &&
    outputParent.parent &&
    hasChildren(outputParent.parent)
  ) {
    outputParent = outputParent.parent;
  }

  return hasChildren(outputParent) ? outputParent : targetParent;
}

function getAncestorChain(node, root) {
  const chain = [];
  let current = node;

  while (current) {
    chain.unshift(current);
    if (current === root) return chain;
    current = current.parent;
  }

  return [];
}

function getLowestCommonParent(nodes, root) {
  const parentChains = nodes.map((node) => getAncestorChain(node.parent, root));
  let common = root;

  for (let index = 0; ; index += 1) {
    const candidate = parentChains[0][index];
    if (!candidate || !parentChains.every((chain) => chain[index] === candidate)) break;
    common = candidate;
  }

  return hasChildren(common) ? common : root;
}

function getDirectChildUnder(parent, node) {
  let current = node;

  while (current.parent && current.parent !== parent) {
    current = current.parent;
  }

  return current.parent === parent ? current : null;
}

function containsBounds(outer, inner) {
  const tolerance = 1;

  return (
    outer.x <= inner.x + tolerance &&
    outer.y <= inner.y + tolerance &&
    outer.x + outer.width >= inner.x + inner.width - tolerance &&
    outer.y + outer.height >= inner.y + inner.height - tolerance
  );
}

function getContextBackgroundNodes(parent, nodes) {
  if (!hasChildren(parent)) return [];

  const sourceBounds = getUnionBounds(nodes);
  const originalChildren = parent.children.slice();
  const affectedChildren = nodes
    .map((node) => getDirectChildUnder(parent, node))
    .filter(Boolean);
  const affectedIds = new Set(affectedChildren.map((child) => child.id));
  const affectedIndexes = affectedChildren.map((child) => originalChildren.indexOf(child));
  const minIndex = Math.min(...affectedIndexes);

  return originalChildren.filter((child, index) => {
    if (index >= minIndex || affectedIds.has(child.id)) return false;
    if (!child.visible || child.type === "TEXT" || !isSceneNode(child)) return false;

    const bounds = getRenderBounds(child);
    if (!bounds || !containsBounds(bounds, sourceBounds)) return false;

    return hasVisualShell(child) || hasChildren(child);
  });
}

function getInsertionIndex(parent, nodes, placement) {
  const originalChildren = parent.children.slice();
  const affectedChildren = nodes
    .map((node) => getDirectChildUnder(parent, node))
    .filter(Boolean);
  const affectedIndexes = affectedChildren.map((child) => originalChildren.indexOf(child));
  const removedDirectIds = new Set(
    nodes.filter((node) => node.parent === parent).map((node) => node.id)
  );
  const minIndex = Math.min(...affectedIndexes);
  const maxIndex = Math.max(...affectedIndexes);

  if (placement === "top") {
    return originalChildren.filter(
      (child, index) => index <= maxIndex && !removedDirectIds.has(child.id)
    ).length;
  }

  return originalChildren.filter(
    (child, index) => index < minIndex && !removedDirectIds.has(child.id)
  ).length;
}

function getOutputInsertionIndex(outputParent, targetParent, nodes, placement) {
  if (outputParent === targetParent) {
    return getInsertionIndex(targetParent, nodes, placement);
  }

  const anchor = getDirectChildUnder(outputParent, targetParent);
  const anchorIndex = anchor ? outputParent.children.indexOf(anchor) : outputParent.children.length;

  if (placement === "top") {
    return Math.min(anchorIndex + 1, outputParent.children.length);
  }

  return Math.max(anchorIndex, 0);
}

function getSourceName(nodes) {
  if (nodes.length === 1) return nodes[0].name;
  return `${nodes.length} selected blocks`;
}

function coversAllVisibleDirectChildren(parent, nodes) {
  if (!hasChildren(parent)) return false;

  const selectedIds = new Set(nodes.map((node) => node.id));
  const visibleChildren = parent.children.filter((child) => child.visible);

  return (
    visibleChildren.length > 0 &&
    visibleChildren.every((child) => selectedIds.has(child.id))
  );
}

function hasVisualShellBetween(node, stopNode) {
  let current = node.parent;

  while (current) {
    if (isSceneNode(current) && hasVisualShell(current)) return true;
    if (current === stopNode) break;
    current = current.parent;
  }

  return false;
}

function shouldNativeExportSingleNode(node, root) {
  return hasChildren(node) || !hasVisualShellBetween(node, root);
}

function getNativeExportNode(targetParent, nodes, root) {
  if (nodes.length === 1 && shouldNativeExportSingleNode(nodes[0], root)) return nodes[0];
  if (coversAllVisibleDirectChildren(targetParent, nodes)) return targetParent;
  return null;
}

function shouldUseStableOutputParent(targetParent, nativeExportNode) {
  return targetParent.type === "GROUP" && nativeExportNode === targetParent;
}

function shouldReplaceGroupWithFrame(targetParent, nativeExportNode) {
  return targetParent.type === "GROUP" && nativeExportNode !== targetParent;
}

function getExportContextParent(root, targetParent, nativeExportNode) {
  if (nativeExportNode) return targetParent;

  let current = targetParent;

  while (current) {
    if (isSceneNode(current) && hasVisualShell(current)) return current;
    if (current === root) break;
    current = current.parent;
  }

  return targetParent;
}

function getContextNodesForExport(exportContextParent, targetParent, nodes) {
  const contextNodes = [];
  let current = targetParent;

  while (current) {
    getContextBackgroundNodes(current, nodes).forEach((node) => {
      if (!contextNodes.includes(node)) contextNodes.push(node);
    });

    if (current === exportContextParent) break;
    current = current.parent;
  }

  return contextNodes;
}

function getPathFromAncestor(ancestor, node) {
  const path = [];
  let current = node;

  while (current && current !== ancestor) {
    const parent = current.parent;
    if (!parent || !hasChildren(parent)) return null;

    path.unshift(parent.children.indexOf(current));
    current = parent;
  }

  return current === ancestor ? path : null;
}

function pathsEqual(first, second) {
  return first.length === second.length && first.every((value, index) => value === second[index]);
}

function isPathPrefix(prefix, path) {
  return prefix.length <= path.length && prefix.every((value, index) => value === path[index]);
}

function pruneCloneByPaths(clone, selectedPaths, currentPath = []) {
  if (selectedPaths.some((path) => path.length === 0)) return;
  if (!hasChildren(clone)) return;

  clone.children.slice().forEach((child, index) => {
    const childPath = [...currentPath, index];
    const shouldKeepWholeNode = selectedPaths.some((path) => pathsEqual(path, childPath));
    const shouldKeepShell = selectedPaths.some((path) => isPathPrefix(childPath, path));

    if (shouldKeepWholeNode) return;

    if (shouldKeepShell) {
      pruneCloneByPaths(child, selectedPaths, childPath);
      return;
    }

    child.remove();
  });
}

function createEmptyExportFrame(bounds) {
  const frame = figma.createFrame();
  frame.name = "__Group to PNG export__";
  frame.fills = [];
  frame.strokes = [];
  frame.clipsContent = true;
  frame.resizeWithoutConstraints(bounds.width, bounds.height);
  frame.x = bounds.x;
  frame.y = bounds.y;

  return frame;
}

function applyAbsoluteLayoutPositioningIfNeeded(node, parent) {
  if (
    "layoutPositioning" in node &&
    "layoutMode" in parent &&
    parent.layoutMode !== "NONE"
  ) {
    node.layoutPositioning = "ABSOLUTE";
  }
}

function createFrameFromGroup(group) {
  const parent = group.parent;
  const bounds = getLayoutBounds(group) || getRenderBounds(group);

  if (!parent || !hasChildren(parent) || !bounds) {
    throw new Error("当前 Group 无法转换成稳定 Frame，请把它放在普通页面或 Frame 内再试。");
  }

  const index = parent.children.indexOf(group);
  const frame = figma.createFrame();
  frame.name = group.name;
  frame.fills = [];
  frame.strokes = [];
  frame.effects = [];
  frame.clipsContent = false;
  frame.resizeWithoutConstraints(bounds.width, bounds.height);
  parent.insertChild(Math.max(index, 0), frame);
  applyAbsoluteLayoutPositioningIfNeeded(frame, parent);
  setAbsoluteTransform(frame, getBoundsTransform(bounds));

  group.children.slice().forEach((child) => {
    const childAbsoluteTransform = child.absoluteTransform;
    frame.appendChild(child);
    setAbsoluteTransform(child, childAbsoluteTransform);
  });

  group.remove();
  return frame;
}

function removeChildren(node) {
  if (!hasChildren(node)) return;
  node.children.slice().forEach((child) => child.remove());
}

function appendAbsoluteClone(frame, node) {
  const inverseFrameTransform = invertTransform(frame.absoluteTransform);
  const clone = node.clone();
  frame.appendChild(clone);
  clone.relativeTransform = multiplyTransform(inverseFrameTransform, node.absoluteTransform);
  return clone;
}

function createPrunedExportFrame(targetParent, nodes, bounds) {
  const frame = createEmptyExportFrame(bounds);

  const inverseFrameTransform = invertTransform(frame.absoluteTransform);
  const clone = targetParent.clone();
  const selectedPaths = nodes
    .map((node) => getPathFromAncestor(targetParent, node))
    .filter((path) => path);

  frame.appendChild(clone);
  clone.relativeTransform = multiplyTransform(inverseFrameTransform, targetParent.absoluteTransform);
  pruneCloneByPaths(clone, selectedPaths);

  return frame;
}

function createDirectExportFrame(targetParent, nodes, bounds) {
  const frame = createEmptyExportFrame(bounds);
  const shells = [];

  nodes.forEach((node) => {
    getAncestorShells(node, targetParent).forEach((shell) => {
      if (!shells.includes(shell)) shells.push(shell);
    });
  });

  shells.reverse().forEach((shell) => {
    if (shell.type === "GROUP") return;

    const clone = appendAbsoluteClone(frame, shell);
    removeChildren(clone);
  });

  nodes.forEach((node) => {
    appendAbsoluteClone(frame, node);
  });

  return frame;
}

function shouldUseDirectExport(targetParent, nodes) {
  return targetParent.type === "GROUP" || (nodes.length === 1 && nodes[0].type === "GROUP");
}

function createTemporaryExportFrame(targetParent, nodes, bounds) {
  if (shouldUseDirectExport(targetParent, nodes)) {
    return createDirectExportFrame(targetParent, nodes, bounds);
  }

  return createPrunedExportFrame(targetParent, nodes, bounds);
}

function collectAncestorGroups(nodes, stopParent) {
  const groups = [];

  nodes.forEach((node) => {
    let current = node.parent;

    while (current && current !== stopParent) {
      if (current.type === "GROUP" && !groups.includes(current)) {
        groups.push(current);
      }
      current = current.parent;
    }
  });

  return groups.sort((first, second) => getAncestorChain(second, stopParent).length - getAncestorChain(first, stopParent).length);
}

function removeEmptyGroups(groups) {
  groups.forEach((group) => {
    if (!group.removed && hasChildren(group) && group.children.length === 0) {
      group.remove();
    }
  });
}

async function bakeChildren(options) {
  const root = assertRoot(options.rootId);
  const nodes = getSelectedDescendants(root, options.childIds);
  const scale = Number(options.scale) || 2;
  const placement = options.placement === "top" ? "top" : "bottom";
  const sourceName = getSourceName(nodes);
  const targetParent = getLowestCommonParent(nodes, root);
  const nativeExportNode = getNativeExportNode(targetParent, nodes, root);
  const exportContextParent = getExportContextParent(root, targetParent, nativeExportNode);
  const replaceGroupWithFrame =
    exportContextParent === targetParent &&
    shouldReplaceGroupWithFrame(targetParent, nativeExportNode);
  const outputParent = shouldUseStableOutputParent(exportContextParent, nativeExportNode)
    ? getStableOutputParent(exportContextParent)
    : exportContextParent;
  const contextNodes = nativeExportNode
    ? []
    : getContextNodesForExport(exportContextParent, targetParent, nodes);
  const exportNodes = nativeExportNode
    ? nodes
    : sortByDocumentOrder([...contextNodes, ...nodes], exportContextParent);
  const bounds = nativeExportNode
    ? getLayoutBounds(nativeExportNode)
    : getExportBounds(exportNodes, exportContextParent);
  if (!bounds) {
    throw new Error("选中的图层没有可导出的区域。");
  }
  const desiredPngAbsoluteTransform = getBoundsTransform(bounds);
  const targetParentAbsoluteTransform = exportContextParent.absoluteTransform;
  const outputInsertionIndex = getOutputInsertionIndex(
    outputParent,
    exportContextParent,
    nodes,
    placement
  );
  const groupsToMaybeRemove = collectAncestorGroups(
    nodes,
    replaceGroupWithFrame ? targetParent : outputParent
  );

  let exportFrame = null;
  let pngNode = null;
  let sourceRemoved = false;

  try {
    if (!nativeExportNode) {
      exportFrame = createTemporaryExportFrame(exportContextParent, exportNodes, bounds);
    }

    const bytes = await (nativeExportNode || exportFrame).exportAsync({
      format: "PNG",
      constraint: {
        type: "SCALE",
        value: scale
      }
    });

    const image = figma.createImage(bytes);
    const finalOutputParent = replaceGroupWithFrame
      ? createFrameFromGroup(exportContextParent)
      : outputParent;

    pngNode = figma.createRectangle();
    pngNode.name = `${sourceName} PNG`;
    finalOutputParent.insertChild(
      Math.min(outputInsertionIndex, finalOutputParent.children.length),
      pngNode
    );
    applyAbsoluteLayoutPositioningIfNeeded(pngNode, finalOutputParent);
    pngNode.resizeWithoutConstraints(bounds.width, bounds.height);
    setAbsoluteTransform(pngNode, desiredPngAbsoluteTransform);
    pngNode.fills = [
      {
        type: "IMAGE",
        scaleMode: "FILL",
        imageHash: image.hash
      }
    ];

    nodes.forEach((node) => {
      if (!node.removed) node.remove();
    });
    sourceRemoved = true;
    removeEmptyGroups(groupsToMaybeRemove);

    if (
      !replaceGroupWithFrame &&
      outputParent === exportContextParent &&
      exportContextParent.type === "GROUP" &&
      !exportContextParent.removed
    ) {
      setAbsoluteTransform(exportContextParent, targetParentAbsoluteTransform);
    }
    if (!pngNode.removed) {
      setAbsoluteTransform(pngNode, desiredPngAbsoluteTransform);
    }

    figma.currentPage.selection = [pngNode];
    figma.viewport.scrollAndZoomIntoView([pngNode]);
    figma.notify(`已生成 ${scale}x PNG，并删除所选源图层。`);
    figma.ui.postMessage({ type: "done", pngNodeId: pngNode.id });
  } catch (error) {
    if (!sourceRemoved && pngNode && !pngNode.removed) {
      pngNode.remove();
    }
    throw error;
  } finally {
    if (exportFrame && !exportFrame.removed) {
      exportFrame.remove();
    }
    postRootState();
  }
}

async function previewChild(message) {
  const node = assertPreviewNode(message.rootId, message.nodeId);
  const bytes = await node.exportAsync({
    format: "PNG",
    constraint: {
      type: "SCALE",
      value: 1
    }
  });

  figma.viewport.scrollAndZoomIntoView([node]);
  figma.ui.postMessage({
    type: "preview",
    nodeId: node.id,
    nodeName: node.name,
    nodeType: node.type,
    bytes
  });
}

figma.ui.onmessage = async (message) => {
  if (message.type === "ready" || message.type === "refresh") {
    postRootState();
    return;
  }

  if (message.type === "cancel") {
    figma.closePlugin();
    return;
  }

  if (message.type === "bake") {
    try {
      await bakeChildren(message);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      figma.notify(messageText, { error: true });
      figma.ui.postMessage({ type: "error", message: messageText });
    }
  }

  if (message.type === "preview") {
    try {
      await previewChild(message);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      figma.notify(messageText, { error: true });
      figma.ui.postMessage({ type: "preview-error", message: messageText });
    }
  }
};

figma.on("selectionchange", postRootState);
