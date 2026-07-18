# Testing Notes

The current committed tests cover pure chord and sheet behavior without requiring third-party packages.

```powershell
$env:PYTHONPATH="backend"
python -m unittest discover backend/tests
```

Full verification requires backend dependencies:

```powershell
cd backend
pip install -r requirements.txt
python -m pytest
```

Audio integration tests should use short fixture clips or synthetic generated WAV files. Network YouTube tests should be mocked so CI does not depend on external availability.
