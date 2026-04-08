module.exports = {
  productionSourceMap: false,
  css: {
    extract: {
      ignoreOrder: true
    }
  },
  configureWebpack: {
    optimization: {
      minimize: false
    }
  }
}
