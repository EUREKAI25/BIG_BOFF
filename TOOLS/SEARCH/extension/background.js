/**
 * BIG_BOFF Search — Service Worker (background)
 * Menus contextuels : ajouter vidéo / sauvegarder image
 */

const API = "http://127.0.0.1:7777/api";

// ── Patterns de détection plateforme vidéo ───────────
const VIDEO_PATTERNS = [
  { regex: /https?:\/\/(?:www\.)?youtube\.com\/watch\?[^\s]*v=[\w-]+/i, platform: "youtube" },
  { regex: /https?:\/\/youtu\.be\/[\w-]+/i, platform: "youtube" },
  { regex: /https?:\/\/(?:www\.)?youtube\.com\/shorts\/[\w-]+/i, platform: "youtube" },
  { regex: /https?:\/\/(?:www\.)?youtube\.com\/embed\/[\w-]+/i, platform: "youtube" },
  { regex: /https?:\/\/(?:www\.)?facebook\.com\/[^\s]*\/videos\/[^\s]+/i, platform: "facebook" },
  { regex: /https?:\/\/(?:www\.)?facebook\.com\/watch[^\s]*/i, platform: "facebook" },
  { regex: /https?:\/\/(?:www\.)?facebook\.com\/share\/[rv]\/[^\s]+/i, platform: "facebook" },
  { regex: /https?:\/\/m\.facebook\.com\/story\.php[^\s]+/i, platform: "facebook" },
  { regex: /https?:\/\/fb\.watch\/[^\s]+/i, platform: "facebook" },
  { regex: /https?:\/\/(?:www\.)?vimeo\.com\/\d+/i, platform: "vimeo" },
  { regex: /https?:\/\/(?:www\.)?dailymotion\.com\/video\/[\w-]+/i, platform: "dailymotion" },
  { regex: /https?:\/\/dai\.ly\/[\w-]+/i, platform: "dailymotion" },
  { regex: /https?:\/\/(?:www\.)?instagram\.com\/reel\/[\w-]+/i, platform: "instagram" },
  { regex: /https?:\/\/(?:www\.)?tiktok\.com\/@[^\s]*\/video\/\d+/i, platform: "tiktok" },
  { regex: /https?:\/\/vm\.tiktok\.com\/[\w-]+/i, platform: "tiktok" },
];

function detectPlatform(url) {
  for (const { regex, platform } of VIDEO_PATTERNS) {
    if (regex.test(url)) return platform;
  }
  return "";
}

function isVideoUrl(url) {
  return VIDEO_PATTERNS.some(({ regex }) => regex.test(url));
}

// ── Création des menus contextuels ───────────────────
chrome.runtime.onInstalled.addListener(() => {
  // Menu sur les liens
  chrome.contextMenus.create({
    id: "add-video-link",
    title: "Ajouter cette vidéo à BIG_BOFF",
    contexts: ["link"],
    targetUrlPatterns: [
      "*://www.youtube.com/*",
      "*://youtube.com/*",
      "*://youtu.be/*",
      "*://www.facebook.com/*",
      "*://m.facebook.com/*",
      "*://fb.watch/*",
      "*://www.tiktok.com/*",
      "*://vm.tiktok.com/*",
      "*://www.instagram.com/reel/*",
      "*://www.vimeo.com/*",
      "*://vimeo.com/*",
      "*://www.dailymotion.com/*",
      "*://dai.ly/*",
    ],
  });

  // Menu sur la page courante (si c'est une page vidéo)
  chrome.contextMenus.create({
    id: "add-video-page",
    title: "Ajouter cette page vidéo à BIG_BOFF",
    contexts: ["page"],
    documentUrlPatterns: [
      "*://www.youtube.com/watch*",
      "*://youtube.com/watch*",
      "*://www.youtube.com/shorts/*",
      "*://www.tiktok.com/*",
      "*://www.instagram.com/reel/*",
      "*://www.facebook.com/*/videos/*",
      "*://www.facebook.com/watch*",
      "*://www.vimeo.com/*",
      "*://vimeo.com/*",
      "*://www.dailymotion.com/video/*",
    ],
  });

  // Menu sur les images
  chrome.contextMenus.create({
    id: "save-image",
    title: "Enregistrer et tagger cette image (BIG_BOFF)",
    contexts: ["image"],
  });
});

// ── Gestionnaire de clic ─────────────────────────────
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "add-video-link") {
    const url = info.linkUrl;
    const platform = detectPlatform(url);
    const pageTitle = tab ? tab.title || "" : "";
    openTagger("video", url, platform, pageTitle);
  }
  else if (info.menuItemId === "add-video-page") {
    const url = tab.url;
    const platform = detectPlatform(url);
    const pageTitle = tab.title || "";
    openTagger("video", url, platform, pageTitle);
  }
  else if (info.menuItemId === "save-image") {
    const imageUrl = info.srcUrl;
    const pageTitle = tab ? tab.title || "" : "";
    openTagger("image", imageUrl, "", pageTitle);
  }
});

function openTagger(type, url, platform, pageTitle) {
  const params = new URLSearchParams({
    type: type,
    url: url,
    platform: platform || "",
    pageTitle: pageTitle || "",
  });
  chrome.tabs.create({
    url: chrome.runtime.getURL("tagger.html") + "?" + params.toString(),
  });
}

// ── Message passing : fetch image cross-origin ───────
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "fetchImage") {
    fetchImageAsBase64(request.url)
      .then(data => sendResponse({ ok: true, data: data }))
      .catch(err => sendResponse({ ok: false, error: err.message }));
    return true; // keep channel open for async
  }
});

async function fetchImageAsBase64(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("HTTP " + resp.status);
  const contentType = resp.headers.get("Content-Type") || "image/jpeg";
  const buffer = await resp.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const b64 = btoa(binary);
  return "data:" + contentType + ";base64," + b64;
}
