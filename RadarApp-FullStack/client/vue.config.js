module.exports = {
  publicPath: '/',
  productionSourceMap: false,
  chainWebpack: config => {
    // Ensure all URLs are relative, not absolute
    config.output.publicPath('/');
  },
  css: {
    extract: {
      ignoreOrder: true
    }
  },
  configureWebpack: {
    output: {
      publicPath: '/'
    },
    optimization: {
      minimize: false
    }
  }
}
