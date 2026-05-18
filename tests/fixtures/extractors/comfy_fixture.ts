/**
 * Runs once during app setup.
 */
setup?(app: ComfyApp): Promise<void> | void

/**
 * Runs before a node definition is registered.
 */
beforeRegisterNodeDef?(
  nodeType: typeof LGraphNode,
  nodeData: ComfyNodeDef,
  app: ComfyApp
): Promise<void> | void
