/** Public-only build configuration. No protected API is used by this site. */
function publicUrl(value: string | undefined): string {
  if (!value?.trim()) return '';
  try { const url = new URL(value.trim()); return url.protocol === 'https:' && !url.username && !url.password ? url.href : ''; }
  catch { return ''; }
}
export const site = {
  apkUrl: publicUrl(import.meta.env.VITE_APK_URL || 'https://github.com/Laurenceonly/Graphiscan/releases/download/android-v1.0.1/Graphiscan.apk'),
  publicUrl: publicUrl(import.meta.env.VITE_SITE_URL),
  version: import.meta.env.VITE_APP_VERSION?.trim() || '1.0.1',
  size: import.meta.env.VITE_APK_SIZE?.trim() || '92.7 MB',
  releaseDate: import.meta.env.VITE_RELEASE_DATE?.trim() || 'November 6, 2026',
};
