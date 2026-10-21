import type { HostedClient } from './hosted-client.mjs';
export function createReviewSubmission(makeKey: () => string): { readonly pending: boolean; discard(): void; submit(client: Pick<HostedClient,'request'>, id: string, body: unknown): Promise<any> };
