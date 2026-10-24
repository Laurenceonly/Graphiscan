import type { HostedClient } from './hosted-client.mjs'
export interface StudentCreateDraft {
  full_name: string; age: number; school_id: string; grade_level: number;
  teacher_id?: string; parent_id?: string | null;
}
export function createStudentSubmission(makeKey?: () => string): {
  readonly pending: boolean;
  submit(client: Pick<HostedClient, 'request'>, draft: StudentCreateDraft): Promise<any>;
}
