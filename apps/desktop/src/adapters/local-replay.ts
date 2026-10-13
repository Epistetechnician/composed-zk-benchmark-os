import type { LocalReplayStatus } from '../ipc/contract';

export interface LocalReplayAdapter {
  readonly id: LocalReplayStatus['adapterId'];
  getStatus(): LocalReplayStatus;
}

class UnavailableLocalReplayAdapter implements LocalReplayAdapter {
  readonly id = 'rust-sidecar' as const;

  getStatus(): LocalReplayStatus {
    return {
      schemaVersion: 'local-replay-status.v1',
      adapterId: this.id,
      state: 'unavailable',
      message:
        'The Rust sidecar adapter seam is present, but native process execution is disabled in Release 0.'
    };
  }
}

export function createLocalReplayAdapter(): LocalReplayAdapter {
  return new UnavailableLocalReplayAdapter();
}
