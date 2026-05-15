export function parseSseEvents(buffer) {
  const events = [];
  let remaining = buffer;
  let boundary = remaining.indexOf('\n\n');

  while (boundary >= 0) {
    const frame = remaining.slice(0, boundary);
    remaining = remaining.slice(boundary + 2);

    const data = frame
      .split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart())
      .join('\n');

    if (data) {
      events.push(JSON.parse(data));
    }

    boundary = remaining.indexOf('\n\n');
  }

  return { events, remaining };
}
