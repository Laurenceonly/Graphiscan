const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');
const config = getDefaultConfig(__dirname);
config.watchFolders = [path.resolve(__dirname, '../shared')];
config.resolver.sourceExts = [...new Set([...config.resolver.sourceExts, 'mjs'])];
module.exports = config;
