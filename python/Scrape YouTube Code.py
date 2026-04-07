// n8n Code Node
// Expected input fields:
//   "youtube-channel" : channel URL, handle URL, or channel identifier
//   "video_limit"     : max number of videos to return
//   "language"        : optional, defaults to "en"
//
// Output format:
//   return [{ json: result }];

async function scanYouTubeChannelVideos(channelInput, videoLimit = 25, language = 'en') {
  const startedAt = new Date().toISOString();
  const runtimeMsStart = Date.now();

  if (!channelInput || typeof channelInput !== 'string') {
    throw new Error('Missing required input: "youtube-channel"');
  }

  const limit = Math.max(1, Number(videoLimit) || 25);
  const lang = (language || 'en').toLowerCase();

  function normalizeChannelVideosUrl(input) {
    let value = input.trim();

    if (value.startsWith('@')) {
      return `https://www.youtube.com/${value}/videos`;
    }

    if (value.startsWith('http://') || value.startsWith('https://')) {
      value = value.replace(/\/+$/, '');

      if (/\/videos(\?|$)/i.test(value)) {
        return value;
      }

      return `${value}/videos`;
    }

    return `https://www.youtube.com/@${value}/videos`;
  }

  const videosUrl = normalizeChannelVideosUrl(channelInput);

  const response = await this.helpers.httpRequest({
    method: 'GET',
    url: videosUrl,
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
      'Accept-Language': lang === 'en' ? 'en-US,en;q=0.9' : `${lang},en;q=0.9`,
    },
    timeout: 30000,
    returnFullResponse: false,
  });

  if (!response || typeof response !== 'string') {
    throw new Error('Failed to load YouTube channel page.');
  }

  const initialDataMatch =
    response.match(/var ytInitialData = (.*?);<\/script>/s) ||
    response.match(/window\["ytInitialData"\] = (.*?);<\/script>/s) ||
    response.match(/ytInitialData"\s*:\s*(\{.*?\})\s*,\s*"metadata"/s);

  if (!initialDataMatch) {
    throw new Error('Could not locate ytInitialData on the YouTube page. YouTube page structure may have changed.');
  }

  let ytInitialData;
  try {
    ytInitialData = JSON.parse(initialDataMatch[1]);
  } catch (err) {
    throw new Error(`Unable to parse ytInitialData JSON: ${err.message}`);
  }

  function findObjectsByKey(obj, keyName, results = []) {
    if (!obj || typeof obj !== 'object') return results;

    if (Object.prototype.hasOwnProperty.call(obj, keyName)) {
      results.push(obj[keyName]);
    }

    if (Array.isArray(obj)) {
      for (const item of obj) {
        findObjectsByKey(item, keyName, results);
      }
    } else {
      for (const key of Object.keys(obj)) {
        findObjectsByKey(obj[key], keyName, results);
      }
    }

    return results;
  }

  const videoRenderers = findObjectsByKey(ytInitialData, 'videoRenderer');

  const videos = [];
  const seen = new Set();

  for (const vr of videoRenderers) {
    if (!vr || !vr.videoId) continue;

    const id = vr.videoId;
    const url = `https://www.youtube.com/watch?v=${id}`;

    if (seen.has(id)) continue;
    seen.add(id);

    const title =
      vr.title?.runs?.map(r => r.text).join('') ||
      vr.title?.simpleText ||
      null;

    const date =
      vr.publishedTimeText?.simpleText ||
      vr.publishedTimeText?.runs?.map(r => r.text).join('') ||
      null;

    const runtime =
      vr.lengthText?.simpleText ||
      vr.lengthText?.runs?.map(r => r.text).join('') ||
      null;

    const viewCount =
      vr.viewCountText?.simpleText ||
      vr.viewCountText?.runs?.map(r => r.text).join('') ||
      null;

    videos.push({
      id,
      url,
      title,
      date,
      // extra available metadata
      runtime,
      viewCount,
      thumbnail: vr.thumbnail?.thumbnails?.slice(-1)[0]?.url || null,
      descriptionSnippet:
        vr.descriptionSnippet?.runs?.map(r => r.text).join('') || null,
    });

    if (videos.length >= limit) break;
  }

  const finishedAt = new Date().toISOString();

  return {
    runtime: {
      startedAt,
      finishedAt,
      durationMs: Date.now() - runtimeMsStart,
      requestedLimit: limit,
      returnedVideos: videos.length,
      sourceUrl: videosUrl,
      language: lang,
    },
    videos: videos.map(v => ({
      id: v.id,
      url: v.url,
      title: v.title,
      date: v.date,
    })),
    availableMetaData: {
      includedInRawExtraction: [
        'runtime',
        'viewCount',
        'thumbnail',
        'descriptionSnippet',
      ],
    },
    rawVideosExtended: videos,
  };
}

// ---- function call ----

const input = $input.first()?.json || {};

const channelInput = input['youtube-channel'];
const videoLimit = input['video_limit'];
const language = input['language'] || 'en';

const result = await scanYouTubeChannelVideos.call(this, channelInput, videoLimit, language);

return [{ json: result }];