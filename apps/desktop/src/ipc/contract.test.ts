import { describe, expect, it } from 'vitest';

import {
  IPC_SCHEMA_VERSION,
  canonicalJson,
  createRequest,
  digestJson,
  failureResponse,
  isIpcRequest,
  parseResponse,
  successResponse
} from './contract';

describe('platform IPC envelope v1', () => {
  it('creates a digest-bound request with canonical payload JSON', async () => {
    const request = await createRequest('catalog.list', 'request-001', {
      scope: 'local',
      alpha: 1
    });

    expect(request).toEqual({
      schema_version: IPC_SCHEMA_VERSION,
      request_id: 'request-001',
      operation: 'catalog.list',
      payload: { scope: 'local', alpha: 1 },
      payload_digest: await digestJson({ alpha: 1, scope: 'local' })
    });
    expect(canonicalJson(request.payload)).toBe('{"alpha":1,"scope":"local"}');
    await expect(isIpcRequest(request)).resolves.toBe(true);
  });

  it('round-trips the strict success shape', () => {
    const response = successResponse('request-002', { capabilities: [] });

    expect(response).toEqual({
      schema_version: IPC_SCHEMA_VERSION,
      request_id: 'request-002',
      status: 'Ok',
      payload: { capabilities: [] },
      error: null
    });
    expect(parseResponse(response, 'request-002')).toEqual(response);
  });

  it('round-trips the strict bounded error shape', () => {
    const response = failureResponse(
      'request-003',
      'sidecar_unavailable',
      'The sidecar is not running.',
      true
    );

    expect(parseResponse(response, 'request-003')).toEqual(response);
  });

  it('rejects digest drift, unknown fields, and noncanonical response shapes', async () => {
    const request = await createRequest('replay.status', 'request-004', {});

    await expect(
      isIpcRequest({ ...request, payload: { changed: true } })
    ).resolves.toBe(false);
    await expect(
      isIpcRequest({ ...request, extra: 'not allowed' })
    ).resolves.toBe(false);
    expect(() =>
      parseResponse(
        {
          ...successResponse('request-004', {}),
          error: { code: 'unexpected', message: 'not allowed', retryable: false }
        },
        'request-004'
      )
    ).toThrow('Invalid IPC response envelope');
    expect(() => parseResponse(successResponse('other', {}), 'request-005')).toThrow(
      'request_id does not match'
    );
  });
});
