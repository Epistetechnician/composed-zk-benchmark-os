import type { DesktopApi } from '../ipc/contract';

declare global {
  interface Window {
    desktopApi: DesktopApi;
  }
}

export {};
