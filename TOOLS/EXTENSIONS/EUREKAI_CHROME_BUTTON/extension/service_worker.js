chrome.action.onClicked.addListener(async () => {
  try {
    const res = await fetch("http://127.0.0.1:5050/run_inventory", { method: "POST" });
    const data = await res.json();
    const ok = data && data.status && data.status.startsWith("ok");
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icon-128.png",
      title: "EUREKAI",
      message: ok ? "Inventaire mis à jour ✅" : ("Échec ❌\n" + (data.output || ""))
    });
  } catch (e) {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icon-128.png",
      title: "EUREKAI",
      message: "Serveur local indisponible ❌\nLance install_and_run.sh"
    });
  }
});
