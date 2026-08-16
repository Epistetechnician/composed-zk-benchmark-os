import { contextBridge, ipcRenderer } from 'electron';

import {
  IPC_CHANNEL,
  createRequest,
  parseResponse,
  type CapabilityCatalog,
  type DesktopApi,
  type DesktopOperation,
  type LocalReplayStatus
} from './ipc/contract';

async function invoke<T>(operation: DesktopOperation): Promise<T> {
  const request = await createRequest(operation, crypto.randomUUID(), {});
  const response = parseResponse<T>(await ipcRenderer.invoke(IPC_CHANNEL, request), request.request_id);

  if (response.status === 'Error') {
    throw new Error(`${response.error.code}: ${response.error.message}`);
  }

  return response.payload;
}

const desktopApi: DesktopApi = {
  getCapabilityCatalog: () => invoke<CapabilityCatalog>('catalog.list'),
  getLocalReplayStatus: () => invoke<LocalReplayStatus>('replay.status')
};

contextBridge.exposeInMainWorld('desktopApi', desktopApi);
