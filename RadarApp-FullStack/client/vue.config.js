module.exports = {
  publicPath: '/',
  productionSourceMap: false,
  chainWebpack: config => {
    // Ensure all URLs are relative, not absolute
    config.output.publicPath('/');
  },
  configureWebpack: {
    output: {
      publicPath: '/'
    },
    optimization: {
      minimize: false
    }
  },
  // Ensure Bootstrap and dependencies are bundled, not CDN
  transpileDependencies: [
    'bootstrap'
  ]
}
