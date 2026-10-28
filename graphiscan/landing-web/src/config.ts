/** Public-only build configuration. No protected API is used by this site. */
function publicUrl(value: string | undefined): string {
  if (!value?.trim()) return '';
  try { const url = new URL(value.trim()); return url.protocol === 'https:' && !url.username && !url.password ? url.href : ''; }
  catch { return ''; }
}
export const site = {
  adminUrl: publicUrl(import.meta.env.VITE_ADMIN_URL) || (import.meta.env.DEV ? 'https://graphiscan-admin.vercel.app/login' : ''),
  apkUrl: publicUrl(import.meta.env.VITE_APK_URL),
  publicUrl: publicUrl(import.meta.env.VITE_SITE_URL),
  version: import.meta.env.VITE_APP_VERSION?.trim() || '',
  size: import.meta.env.VITE_APK_SIZE?.trim() || '',
  releaseDate: import.meta.env.VITE_RELEASE_DATE?.trim() || '',
};
