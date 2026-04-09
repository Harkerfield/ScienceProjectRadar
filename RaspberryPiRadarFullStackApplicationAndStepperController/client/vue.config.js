module.exports = {
  publicPath: '/',
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
