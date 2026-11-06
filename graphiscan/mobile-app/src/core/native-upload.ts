// Send Android file URIs through Expo's native multipart uploader instead of
// React Native fetch's URI-to-request-body conversion. Other requests use fetch.
import type {FileSystemUploadOptions, FileSystemUploadResult} from 'expo-file-system/legacy'

type UploadTask = {uploadAsync(): Promise<FileSystemUploadResult | null | undefined>; cancelAsync(): Promise<void>}
type CreateTask = (url: string, uri: string, options: FileSystemUploadOptions) => UploadTask
type Part = {fieldName: string; string?: string; uri?: string; type?: string}

export function createNativeUploadFetch(fetchImpl: typeof fetch, createTask: CreateTask, multipart: number): typeof fetch {
  return (async (input: RequestInfo | URL, options?: RequestInit) => {
    const form = options?.body as unknown as {getParts?: () => Part[]} | undefined
    if (options?.method !== 'POST' || !String(input).endsWith('/api/v1/screenings') || !form?.getParts) return fetchImpl(input, options)
    const parts = form.getParts(), files = parts.filter(part => part.uri !== undefined)
    if (files.length !== 1 || files[0].fieldName !== 'handwriting_image' || parts.some(part => !part.uri && typeof part.string !== 'string')) {
      throw Object.assign(new Error('Select one valid handwriting image.'), {status:422})
    }
    const signal = options?.signal
    if (signal?.aborted) throw new Error('Upload cancelled.')
    const headers: Record<string,string> = {}, parameters: Record<string,string> = {}
    new Headers(options?.headers).forEach((value,key) => {if(key !== 'content-type') headers[key] = value})
    for (const part of parts) if (part.uri === undefined) parameters[part.fieldName] = part.string!
    const file = files[0]
    const task = createTask(String(input), file.uri!, {
      httpMethod:'POST', uploadType:multipart, fieldName:file.fieldName,
      mimeType:file.type || 'image/jpeg', parameters, headers,
    })
    let abort = () => {}
    const cancelled = new Promise<never>((_,reject) => {
      abort = () => {void task.cancelAsync().catch(() => {}); reject(new Error('Upload cancelled.'))}
      signal?.addEventListener('abort',abort,{once:true})
    })
    try {
      const result = await Promise.race([task.uploadAsync(),cancelled])
      if (!result) throw new Error('Upload cancelled.')
      return new Response(result.body,{status:result.status,headers:result.headers})
    } finally {signal?.removeEventListener('abort',abort)}
  }) as typeof fetch
}
