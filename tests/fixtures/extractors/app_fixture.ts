invokeExtensionsAsync("setup")
invokeExtensionsAsync("beforeRegisterNodeDef", nodeType, nodeData, app)

app.registerExtension({
  async init() {},
  async nodeCreated(node) {},
})
