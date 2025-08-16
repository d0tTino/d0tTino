# Install via Scoop

Use [Scoop](https://scoop.sh) to install the tools from this repository on Windows.

1. Add the custom bucket:
   ```powershell
   scoop bucket add tino https://github.com/d0tTino/tino-bucket
   ```
2. Install the manifest:
   ```powershell
   scoop install tino
   ```
3. Update when needed:
   ```powershell
   scoop update tino
   ```

Alternatively, perform the installation in one step:

```powershell
scoop bucket add tino https://github.com/d0tTino/tino-bucket; scoop install tino
```

The manifest downloads the versioned release archive and runs a dry-run of the common installer to verify dependencies.
