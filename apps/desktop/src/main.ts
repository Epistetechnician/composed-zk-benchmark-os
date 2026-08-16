import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'node:path';

import { createLocalReplayAdapter } from './adapters/local-replay';
import {
  IPC_CHANNEL,
  failureResponse,
  isIpcRequest,
  successResponse,
  type CapabilityCatalog,
  type IpcResponse
} from './ipc/contract';

const localReplayAdapter = createLocalReplayAdapter();

const capabilityCatalog: CapabilityCatalog = {
  schemaVersion: 'capability-catalog.v1',
  capabilities: [
    {
      id: 'capability.catalog',
      label: 'Capability catalog',
      status: 'available',
      description: 'Read-only catalog data is available from the Electron main process.'
    },
    {
      id: 'local.replay',
      label: 'Local replay',
      status: 'unavailable',
      description: 'Reserved for a future Rust sidecar integration; no native execution is enabled.'
    },
    {
      id: 'rust.sidecar',
      label: 'Rust sidecar',
      status: 'planned',
      description: 'The adapter seam is explicit, but process custody and lifecycle are out of scope.'
    }
  ]
};

async function handleIpcRequest(value: unknown): Promise<IpcResponse<unknown>> {
  if (!(await isIpcRequest(value))) {
    return failureResponse('unknown', 'invalid_request', 'The IPC request envelope is invalid.', false);
  }

  switch (value.operation) {
    case 'catalog.list':
      return successResponse(value.request_id, capabilityCatalog);
    case 'replay.status':
      return successResponse(value.request_id, localReplayAdapter.getStatus());
    default:
      return failureResponse(
        value.request_id,
        'unsupported_operation',
        'The IPC operation is not supported.',
        false
      );
  }
}

function createMainWindow(): BrowserWindow {
  const mainWindow = new BrowserWindow({
    width: 1120,
    height: 760,
    minWidth: 860,
    minHeight: 620,
    backgroundColor: '#0b1117',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  if (typeof MAIN_WINDOW_VITE_DEV_SERVER_URL !== 'undefined') {
    void mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    void mainWindow.loadFile(
      path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`)
    );
  }

  return mainWindow;
}

function registerIpcHandlers(): void {
  ipcMain.handle(IPC_CHANNEL, (_event, request: unknown) => handleIpcRequest(request));
}

app.on('web-contents-created', (_event, contents) => {
  contents.setWindowOpenHandler(() => ({ action: 'deny' }));
  contents.on('will-navigate', (event) => {
    event.preventDefault();
  });
});

void app.whenReady().then(() => {
  registerIpcHandlers();
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
