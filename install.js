{
  "run": [
    {
      "method": "shell.run",
      "params": {
        "message": "pip install -r requirements.txt",
        "venv": "env",
        "venv_python": "3.11"
      }
    },
    {
      "method": "notify",
      "params": {
        "html": "TrackWasher installed successfully! Click <b>Start</b> to launch."
      }
    }
  ]
}
