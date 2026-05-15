import { describe, expect, it } from 'vitest';
import { parseSseEvents } from './sse';

describe('parseSseEvents', () => {
  it('parses complete event blocks and preserves incomplete trailing data', () => {
    const first = 'data: {"type":"stage1_start"}\n\n';
    const partial = 'data: {"type":"stage1_complete"';

    const result = parseSseEvents(first + partial);

    expect(result.events).toEqual([{ type: 'stage1_start' }]);
    expect(result.remaining).toBe(partial);
  });

  it('parses multiple complete events from one chunk', () => {
    const chunk = [
      'data: {"type":"stage2_start"}',
      '',
      'data: {"type":"complete"}',
      '',
      '',
    ].join('\n');

    const result = parseSseEvents(chunk);

    expect(result.events).toEqual([
      { type: 'stage2_start' },
      { type: 'complete' },
    ]);
    expect(result.remaining).toBe('');
  });
});
