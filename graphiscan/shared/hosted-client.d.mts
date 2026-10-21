export interface HostedClient {
  login(email: string, password: string): Promise<void>;
  logout(): Promise<void>;
  clear(): void;
  request(path: string, options?: { method?: string; body?: unknown; form?: FormData; image?: boolean; timeout?: number; envelope?: boolean; idempotencyKey?: string }): Promise<any>;
}
export function createHostedClient(origin: string, options?: { fetchImpl?: typeof fetch; now?: () => number }): HostedClient;
