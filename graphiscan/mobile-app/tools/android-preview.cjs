// Native development preview. Android's adb reverse connects to IPv4 loopback.
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const cli = path.join(path.dirname(require.resolve('expo/package.json')), 'bin', 'cli');
const env = { ...process.env, EXPO_PUBLIC_API_MODE: 'hosted' };
if (!env.ANDROID_HOME && process.platform === 'win32' && env.LOCALAPPDATA) {
  const sdk = path.join(env.LOCALAPPDATA, 'Android', 'Sdk');
  if (fs.existsSync(sdk)) env.ANDROID_HOME = sdk;
}
const child = spawn(process.execPath, ['--dns-result-order=ipv4first', cli,
  'start', '--android', '--localhost', '--port', '8081'], {
  cwd: path.resolve(__dirname, '..'), stdio: 'inherit', env
});
child.on('error', () => { process.stderr.write('Unable to start the Android preview.\n'); process.exitCode = 1; });
child.on('exit', code => { process.exitCode = code ?? 1; });
