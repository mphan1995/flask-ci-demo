(() => {
  const MB = window.MB;
  if (!MB) return;

  const bindPlayback = () => {
    document.querySelectorAll("[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        if (action === "play") {
          const trackId = btn.dataset.trackId;
          if (trackId) {
            MB.post("/api/play", { track_id: Number(trackId) });
            return;
          }
          fetch("/api/tracks")
            .then((res) => res.json())
            .then((tracks) => {
              if (!tracks.length) {
                window.alert("No tracks in the library yet.");
                return;
              }
              MB.post("/api/play", { track_id: tracks[0].id });
            });
          return;
        }
        MB.post(`/api/${action}`);
      });
    });

    const seek = document.getElementById("seek");
    if (seek) {
      seek.addEventListener("change", () => {
        MB.post("/api/seek", { position_seconds: Number(seek.value) });
      });
    }

    const volume = document.getElementById("volume");
    if (volume) {
      volume.addEventListener("input", () => {
        MB.post("/api/volume", { volume: Number(volume.value) });
      });
    }

    const mute = document.getElementById("mute");
    if (mute && volume) {
      mute.addEventListener("click", () => {
        const last = mute.dataset.last || volume.value;
        if (Number(volume.value) > 0) {
          mute.dataset.last = volume.value;
          volume.value = 0;
          MB.post("/api/volume", { volume: 0 });
        } else {
          volume.value = last;
          MB.post("/api/volume", { volume: Number(last) });
        }
      });
    }

    const shuffle = document.getElementById("shuffle");
    if (shuffle) {
      shuffle.addEventListener("change", () => {
        MB.post("/api/shuffle", { enabled: shuffle.checked });
      });
    }

    const repeat = document.getElementById("repeat");
    if (repeat) {
      repeat.addEventListener("change", () => {
        MB.post("/api/repeat", { mode: repeat.value });
      });
    }
  };

  MB.ready(bindPlayback);
})();
