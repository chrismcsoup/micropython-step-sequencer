// Browser-specific MIDI setup using WebMidi v3
const statusEl = document.getElementById("status");
const selectEl = document.getElementById("midi-output");
const transposeEl = document.getElementById("transpose");
const transposeOutEl = document.getElementById("transpose-val");
const playBtn = document.getElementById("play-btn");
const enableMidiBtn = document.getElementById("enable-midi");

// Expose midiOutput to window so Python can access it
window.midiOutput = null;

// JS helpers for MicroPython bridge
window.js_midi_note_on = (note, velocity) => {
  const out = window.midiOutput;
  if (!out) return;
  try {
    const v = Number(velocity);
    const velocityNormalized = Math.max(0, Math.min(1, v > 1 ? v / 127 : v));
    // WebMidi v3: use 'attack' instead of deprecated 'velocity'
    out.playNote(Number(note), { attack: velocityNormalized });
  } catch (e) {
    console.error("playNote error", e);
  }
};
window.js_midi_note_off = (note) => {
  const out = window.midiOutput;
  if (!out) return;
  try {
    out.stopNote(Number(note));
  } catch (e) {
    console.error("stopNote error", e);
  }
};

// Schedule stopping the note after a delay
window.js_schedule_note_off = (note, delayMs) => {
  const out = window.midiOutput;
  if (!out) return;
  setTimeout(() => {
    try {
      out.stopNote(Number(note));
    } catch (e) {
      console.error("stopNote (scheduled) error", e);
    }
  }, Number(delayMs));
};

function setStatus(msg) {
  statusEl.textContent = msg;
  console.log(`STATUS: ${msg}`);
}

transposeEl.addEventListener("input", () => {
  const val = parseInt(transposeEl.value) || 0;
  transposeOutEl.textContent = `${val} st`;
  if (window.midiRouter) {
    window.midiRouter.set_transpose(val);
  }
});

selectEl.addEventListener("change", () => {
  const selectedId = selectEl.value;
  window.midiOutput = selectedId ? WebMidi.getOutputById(selectedId) : null;
  setStatus(window.midiOutput ? `Using: ${window.midiOutput.name}` : "No output selected");
});

playBtn.addEventListener("click", () => {
  if (window.midiRouter) {
    window.midiRouter.send_note();
  }
});

function onMidiEnabled() {
  selectEl.innerHTML = "";
  const outputs = WebMidi.outputs;

  if (!outputs.length) {
    setStatus("No MIDI outputs detected");
    return;
  }

  let preferred = null;
  for (const out of outputs) {
    const opt = document.createElement("option");
    opt.value = out.id;
    opt.textContent = out.name;
    selectEl.appendChild(opt);
  }

  if (!preferred) preferred = outputs[0];
  selectEl.value = preferred.id;
  window.midiOutput = preferred;
  setStatus(`MIDI ready: ${preferred.name}`);
}

enableMidiBtn.addEventListener("click", () => {
  setStatus("Requesting MIDI...");
  WebMidi.enable()
    .then(onMidiEnabled)
    .catch(err => {
      setStatus("WebMIDI not available");
      console.error(err);
    });
});
