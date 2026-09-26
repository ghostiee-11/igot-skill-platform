const YOUTUBE_ID = /^[A-Za-z0-9_-]{11}$/;

export function getYouTubeEmbedUrl(url?: string | null): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.replace(/^(www|m)\./, "");
    let id: string | null = null;
    if (host === "youtu.be") {
      id = parsed.pathname.slice(1);
    } else if (host === "youtube.com" || host === "youtube-nocookie.com") {
      if (parsed.pathname === "/watch") {
        id = parsed.searchParams.get("v");
      } else {
        const match = parsed.pathname.match(/^\/(embed|shorts|live)\/([^/?]+)/);
        if (match) id = match[2];
      }
    }
    // youtube-nocookie.com is blocked on some networks and by privacy extensions; the standard embed domain is more reliable.
    return id && YOUTUBE_ID.test(id) ? `https://www.youtube.com/embed/${id}?rel=0` : null;
  } catch {
    return null;
  }
}
