const YOUTUBE_ID_PATTERN = /^[A-Za-z0-9_-]{11}$/;

export function extractYouTubeId(urlOrId?: string | null): string | null {
  if (!urlOrId) return null;
  const trimmed = urlOrId.trim();
  if (YOUTUBE_ID_PATTERN.test(trimmed)) {
    return trimmed;
  }
  try {
    const parsed = new URL(trimmed.startsWith("http") ? trimmed : `https://${trimmed}`);
    const host = parsed.hostname.replace(/^(www|m)\./, "");
    if (host === "youtu.be") {
      const part = parsed.pathname.slice(1).split("/")[0]?.split("?")[0];
      return part && YOUTUBE_ID_PATTERN.test(part) ? part : null;
    }
    if (host === "youtube.com" || host === "youtube-nocookie.com") {
      if (parsed.pathname === "/watch") {
        const v = parsed.searchParams.get("v");
        return v && YOUTUBE_ID_PATTERN.test(v) ? v : null;
      }
      const match = parsed.pathname.match(/^\/(embed|shorts|live|v)\/([^/?]+)/);
      if (match && YOUTUBE_ID_PATTERN.test(match[2])) {
        return match[2];
      }
    }
    return null;
  } catch {
    return null;
  }
}

export function getYouTubeEmbedUrl(
  urlOrId?: string | null,
  startTime?: number | null,
  endTime?: number | null
): string | null {
  const id = extractYouTubeId(urlOrId);
  if (!id) return null;

  const params = new URLSearchParams();
  params.set("rel", "0");
  if (typeof startTime === "number" && startTime >= 0) {
    params.set("start", Math.floor(startTime).toString());
  }
  if (typeof endTime === "number" && endTime > (startTime ?? 0)) {
    params.set("end", Math.floor(endTime).toString());
  }

  return `https://www.youtube.com/embed/${id}?${params.toString()}`;
}
