# Install via Scoop

Use [Scoop](https://scoop.sh) to install the tools from this repository on Windows.

1. Add this repository as a custom bucket, pointing at the `scoop` subdirectory:
   ```powershell
   scoop bucket add tino https://github.com/d0tTino/d0tTino main scoop
   ```
2. Install the manifest:
   ```powershell
   scoop install tino
   ```
3. Update when needed:
   ```powershell
   scoop update tino
   ```

The manifest downloads the current `main` branch archive and verifies it using the SHA256 hash stored in `scoop/tino.json`.
