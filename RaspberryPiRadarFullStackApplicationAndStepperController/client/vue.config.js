module.exports = {
  productionSourceMap: false,
  configureWebpack: {
    optimization: {
      minimize: true,
      minimizer: [
        new (require('terser-webpack-plugin'))()
      ]
    }
  }
}
