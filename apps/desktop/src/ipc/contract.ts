export const IPC_SCHEMA_VERSION = 'platform-ipc.v1' as const;
export const IPC_CHANNEL = 'desktop:request' as const;

const MAX_REQUEST_ID_LENGTH = 128;
const MAX_OPERATION_LENGTH = 128;
const MAX_ERROR_CODE_LENGTH = 128;
const MAX_ERROR_MESSAGE_LENGTH = 1024;

export type IpcJsonValue =
  | null
  | boolean
  | number
  | string
  | IpcJsonValue[]
  | { [key: string]: IpcJsonValue };

export type DesktopOperation = 'catalog.list' | 'replay.status';

export interface IpcRequest {
  schema_version: typeof IPC_SCHEMA_VERSION;
  request_id: string;
  operation: string;
  payload: IpcJsonValue;
  payload_digest: string;
}

export interface Capability {
  id: string;
  label: string;
  status: 'available' | 'unavailable' | 'planned';
  description: string;
}

export interface CapabilityCatalog {
  schemaVersion: 'capability-catalog.v1';
  capabilities: readonly Capability[];
}

export interface LocalReplayStatus {
  schemaVersion: 'local-replay-status.v1';
  adapterId: 'rust-sidecar';
  state: 'unavailable';
  message: string;
}

export type IpcResponseStatus = 'Ok' | 'Error';

export interface IpcError {
  code: string;
  message: string;
  retryable: boolean;
}

export interface IpcSuccessResponse<T> {
  schema_version: typeof IPC_SCHEMA_VERSION;
  request_id: string;
  status: 'Ok';
  payload: T;
  error: null;
}

export interface IpcFailureResponse {
  schema_version: typeof IPC_SCHEMA_VERSION;
  request_id: string;
  status: 'Error';
  payload: null;
  error: IpcError;
}

export type IpcResponse<T> = IpcSuccessResponse<T> | IpcFailureResponse;

export interface DesktopApi {
  getCapabilityCatalog(): Promise<CapabilityCatalog>;
  getLocalReplayStatus(): Promise<LocalReplayStatus>;
}

export async function createRequest(
  operation: DesktopOperation,
  requestId: string,
  payload: IpcJsonValue = {}
): Promise<IpcRequest> {
  assertBoundedIdentifier('request_id', requestId, MAX_REQUEST_ID_LENGTH);
  assertBoundedIdentifier('operation', operation, MAX_OPERATION_LENGTH);

  return {
    schema_version: IPC_SCHEMA_VERSION,
    request_id: requestId,
    operation,
    payload,
    payload_digest: await digestJson(payload)
  };
}

export function successResponse<T>(requestId: string, payload: T): IpcSuccessResponse<T> {
  return {
    schema_version: IPC_SCHEMA_VERSION,
    request_id: requestId,
    status: 'Ok',
    payload,
    error: null
  };
}

export function failureResponse(
  requestId: string,
  code: string,
  message: string,
  retryable: boolean
): IpcFailureResponse {
  return {
    schema_version: IPC_SCHEMA_VERSION,
    request_id: requestId,
    status: 'Error',
    payload: null,
    error: { code, message, retryable }
  };
}

export function canonicalJson(value: IpcJsonValue): string {
  assertJsonValue(value);
  const serialized = JSON.stringify(canonicalizeJson(value));
  if (serialized === undefined) {
    throw new Error('IPC payload could not be serialized as canonical JSON.');
  }
  return serialized;
}

export async function digestJson(value: IpcJsonValue): Promise<string> {
  const bytes = new TextEncoder().encode(canonicalJson(value));
  const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actualKeys = Object.keys(value).sort();
  const expectedKeys = [...keys].sort();
  return actualKeys.length === expectedKeys.length && actualKeys.every((key, index) => key === expectedKeys[index]);
}

function isJsonValue(value: unknown): value is IpcJsonValue {
  if (value === null || typeof value === 'boolean' || typeof value === 'string') {
    return true;
  }

  if (typeof value === 'number') {
    return Number.isFinite(value);
  }

  if (Array.isArray(value)) {
    return value.every(isJsonValue);
  }

  return isRecord(value) && Object.values(value).every(isJsonValue);
}

function assertJsonValue(value: unknown): asserts value is IpcJsonValue {
  if (!isJsonValue(value)) {
    throw new Error('IPC payload must be valid JSON.');
  }
}

function canonicalizeJson(value: IpcJsonValue): IpcJsonValue {
  if (Array.isArray(value)) {
    return value.map(canonicalizeJson);
  }

  if (isRecord(value)) {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonicalizeJson(value[key])])
    );
  }

  return value;
}

function isBoundedIdentifier(value: unknown, maxLength: number): value is string {
  return (
    typeof value === 'string' &&
    value.trim().length > 0 &&
    [...value].length <= maxLength &&
    ![...value].some((character) => character.charCodeAt(0) <= 0x1f || character.charCodeAt(0) === 0x7f)
  );
}

function assertBoundedIdentifier(field: string, value: string, maxLength: number): void {
  if (!isBoundedIdentifier(value, maxLength)) {
    throw new Error(`${field} must be non-empty, control-free, and at most ${maxLength} characters.`);
  }
}

function isIpcError(value: unknown): value is IpcError {
  return (
    isRecord(value) &&
    hasExactKeys(value, ['code', 'message', 'retryable']) &&
    isBoundedIdentifier(value.code, MAX_ERROR_CODE_LENGTH) &&
    typeof value.message === 'string' &&
    value.message.trim().length > 0 &&
    value.message.length <= MAX_ERROR_MESSAGE_LENGTH &&
    typeof value.retryable === 'boolean'
  );
}

export async function isIpcRequest(value: unknown): Promise<boolean> {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, ['schema_version', 'request_id', 'operation', 'payload', 'payload_digest']) ||
    value.schema_version !== IPC_SCHEMA_VERSION ||
    !isBoundedIdentifier(value.request_id, MAX_REQUEST_ID_LENGTH) ||
    !isBoundedIdentifier(value.operation, MAX_OPERATION_LENGTH) ||
    !isJsonValue(value.payload) ||
    !isBoundedIdentifier(value.payload_digest, 64) ||
    !/^[0-9a-f]{64}$/.test(value.payload_digest)
  ) {
    return false;
  }

  return (await digestJson(value.payload)) === value.payload_digest;
}

export function parseResponse<T>(value: unknown, expectedRequestId: string): IpcResponse<T> {
  if (!isRecord(value) || value.schema_version !== IPC_SCHEMA_VERSION) {
    throw new Error('Invalid IPC response schema version.');
  }

  if (value.request_id !== expectedRequestId) {
    throw new Error('IPC response request_id does not match the request.');
  }

  if (
    value.status === 'Ok' &&
    value.error === null &&
    isJsonValue(value.payload) &&
    'payload' in value &&
    hasExactKeys(value, ['schema_version', 'request_id', 'status', 'payload', 'error'])
  ) {
    return value as unknown as IpcSuccessResponse<T>;
  }

  if (
    value.status === 'Error' &&
    value.payload === null &&
    isIpcError(value.error) &&
    hasExactKeys(value, ['schema_version', 'request_id', 'status', 'payload', 'error'])
  ) {
    return value as unknown as IpcFailureResponse;
  }

  throw new Error('Invalid IPC response envelope.');
}
