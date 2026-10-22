// Engineering browser preview; no public/native environment file is rewritten.
const path = require('node:path');
const { spawn } = require('node:child_process');
const cli = path.join(path.dirname(require.resolve('expo/package.json')), 'bin', 'cli');
const child = spawn(process.execPath, [cli, 'start', '--web', '--localhost', '--port', '5174'], {
  cwd: path.resolve(__dirname, '..'), stdio: 'inherit',
  env: { ...process.env, GRAPHISCAN_EXPO_PREVIEW_PROXY: '1', EXPO_PUBLIC_API_MODE: 'hosted',
    EXPO_PUBLIC_HOSTED_API_ORIGIN: 'http://localhost:5174' }
});
child.on('error', () => { process.stderr.write('Unable to start the Expo preview.\n'); process.exitCode = 1; });
child.on('exit', code => { process.exitCode = code ?? 1; });
