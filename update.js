{
  "run": [
    {
      "method": "shell.run",
      "params": {
        "message": "git pull"
      }
    },
    {
      "method": "shell.run",
      "params": {
        "message": "pip install -r requirements.txt",
        "venv": "env"
      }
    },
    {
      "method": "notify",
      "params": {
        "html": "TrackWasher updated successfully!"
      }
    }
  ]
}
