module.exports = {
  title: "TrackWasher",
  description: "Pre-mastering & audio enhancement for AI-generated music. 12-stage processing chain with platform presets (Suno, Udio), before/after spectrogram, and broadcast-ready LUFS normalization.",
  icon: "icon.png",
  menu: [
    {
      text: "Install",
      href: "install.js",
      icon: "fa-solid fa-download",
      description: "Install dependencies"
    },
    {
      text: "Start",
      href: "start.js",
      icon: "fa-solid fa-play",
      description: "Launch TrackWasher UI"
    },
    {
      text: "Update",
      href: "update.js",
      icon: "fa-solid fa-arrows-rotate",
      description: "Pull latest version"
    },
    {
      text: "Reset",
      href: "reset.js",
      icon: "fa-solid fa-rotate-left",
      description: "Reset virtual environment"
    }
  ]
}
